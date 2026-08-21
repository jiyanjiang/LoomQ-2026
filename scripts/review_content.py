#!/usr/bin/env python3
"""LoomQ 内容批量审稿（游戏文案 JSON + 词典 + 参考文献）。

两层：
  1. 静态检查（默认，不需要 LLM）：必填字段 / dict_refs 存在 / source_refs 存在。
  2. LLM 审稿（--llm，需 config.yaml 配置 llm_user_api_key）：
     逐个 game_content/*.json 调 LLM，按 prompts/content_review_v1.yaml 审稿，
     输出 data/content_review_YYYYMMDD.json（原始评分）+ .md（可读报告）。

用法：
  python scripts/review_content.py            # 静态检查
  python scripts/review_content.py --llm      # 静态检查 + LLM 审稿
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "web"))
sys.path.insert(0, str(ROOT / "public" / "scripts"))

import key_loader  # noqa: E402
import qc_dict  # noqa: E402

GAME_DIR = ROOT / "web" / "game_content"
PROMPT_FILE = ROOT / "prompts" / "content_review_v1.yaml"
REPORT_DIR = ROOT / "data"


# ---------------------------------------------------------------------------
# 静态检查（零 LLM）
# ---------------------------------------------------------------------------
def static_check() -> list[dict]:
    errors: list[dict] = []
    for path in sorted(GAME_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        gid = path.stem
        # 测试题/挑战题文件（无 sections，走专门检查）
        qs = data.get("questions") or data.get("challenges")
        if qs is not None:
            for ch in qs:
                for f in ("id", "incident", "target", "solutions"):
                    if f not in ch:
                        errors.append({"game": gid, "severity": "error", "detail": f"题[{ch.get('id','?')}] 缺字段 {f}"})
                if "questions" in data and ch.get("concept") is None:
                    errors.append({"game": gid, "severity": "error", "detail": f"题[{ch.get('id')}] 缺 concept 字段"})
                if ch.get("incident") not in (data.get("model", {}).get("incident_states", []) or list(data.get("incidents", {}).keys())):
                    errors.append({"game": gid, "severity": "error", "detail": f"题[{ch.get('id')}] 入射态未定义: {ch.get('incident')}"})
            continue
        # 必填字段
        for f in ("game", "title", "subtitle", "sections"):
            if f not in data:
                errors.append({"game": gid, "severity": "error", "detail": f"缺顶层字段 {f}"})
        if data.get("game") != gid:
            errors.append({"game": gid, "severity": "error", "detail": f"game 字段({data.get('game')})与文件名({gid})不一致"})
        # section 检查
        seen_ids = set()
        for i, sec in enumerate(data.get("sections", [])):
            sid = sec.get("id", f"#{i}")
            if sid in seen_ids:
                errors.append({"game": gid, "severity": "error", "detail": f"section id 重复: {sid}"})
            seen_ids.add(sid)
            for f in ("id", "title", "body"):
                if not sec.get(f):
                    errors.append({"game": gid, "severity": "error", "detail": f"section[{sid}] 缺字段 {f}"})
            for ref in sec.get("dict_refs", []):
                if ref not in qc_dict.DICT:
                    errors.append({"game": gid, "severity": "error",
                                   "detail": f"section[{sid}] dict_ref 不存在: {ref}（词典无此英文键）"})
        # source_refs
        for ref in data.get("source_refs", []):
            if ref not in qc_dict.REFERENCES:
                errors.append({"game": gid, "severity": "warning",
                               "detail": f"source_ref 不存在: {ref}（REFERENCES 无此 key）"})
        # 词典词条字段完整性
        for en in qc_dict.DICT:
            v = qc_dict.DICT[en]
            for f in ("zh", "def_zh", "def_en", "detail_zh", "detail_en", "prereqs", "aliases", "source"):
                if f not in v:
                    errors.append({"game": gid, "severity": "error", "detail": f"词典[{en}] 缺字段 {f}"})
    return errors


# ---------------------------------------------------------------------------
# LLM 审稿
# ---------------------------------------------------------------------------
def _load_key() -> str | None:
    key = key_loader.get_secret("llm_user_api_key")
    if not key or not key.startswith("sk-") or not all(ord(c) < 128 for c in key):
        return None
    return key


def _llm_ask(api_key: str, base_url: str, model: str, system: str, user: str) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "temperature": 0,
        "max_tokens": 2000,
    }
    if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
        payload["thinking"] = {"type": "disabled"}
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]


def llm_review(api_key: str) -> list[dict]:
    base_url = key_loader.get_secret("llm_user_base_url") or "https://api.deepseek.com"
    model = key_loader.get_secret("llm_user_model") or "deepseek-v4-flash"
    # 挑战题 JSON（无 sections）走专门提示词：prompts/challenge_review_v1.yaml
    CHALLENGE_PROMPT = ROOT / "prompts" / "challenge_review_v1.yaml"

    def _load_prompt(path: Path):
        try:
            import yaml
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    reports = []
    for path in sorted(GAME_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        gid = path.stem
        if "questions" in data or "challenges" in data:  # 测试题/挑战题：专门的提示词 + 直接审 JSON
            prompt_cfg = _load_prompt(CHALLENGE_PROMPT)
            if prompt_cfg is None:
                print(f"⚠ 挑战题提示词缺失或 pyyaml 未装，跳过 [{gid}]")
                continue
            system = prompt_cfg.get("system", "")
            user = prompt_cfg.get("user", "").replace(
                "{content_json}", json.dumps(data, ensure_ascii=False, indent=1))
            print(f"  LLM 审稿 [{gid}]（挑战题）...", flush=True)
            raw = _llm_ask(api_key, base_url, model, system, user)
            try:
                report = json.loads(_strip_fence(raw))
            except Exception:
                report = {"game_id": gid, "overall_score": None,
                          "issues": [{"severity": "warning", "challenge": "?", "detail": "LLM 输出非 JSON", "fix": raw[:500]}]}
                print(f"  ⚠ [{gid}] LLM 输出非 JSON，原样存档", flush=True)
            report["game_id"] = gid
            reports.append(report)
            continue

        prompt_cfg = _load_prompt(PROMPT_FILE)
        if prompt_cfg is None:
            print("⚠ 未安装 pyyaml 或提示词解析失败，LLM 审稿跳过")
            return []
        system_tpl = prompt_cfg.get("system", "")
        user_tpl = prompt_cfg.get("user", "")
        # 收集本页涉及词典词条 + 参考文献
        refs = set()
        for sec in data.get("sections", []):
            refs.update(sec.get("dict_refs", []))
        dict_json = json.dumps(
            {en: {k: v for k, v in qc_dict.DICT[en].items() if k in
                  ("zh", "def_zh", "detail_zh", "source")} for en in refs if en in qc_dict.DICT},
            ensure_ascii=False, indent=1,
        )
        ref_json = json.dumps(
            {k: qc_dict.REFERENCES[k] for k in data.get("source_refs", []) if k in qc_dict.REFERENCES},
            ensure_ascii=False, indent=1,
        )
        system = system_tpl
        user = user_tpl
        # 占位符替换（不用 str.format：内容 JSON 含 {} 会冲突）
        user = user.replace("{game_id}", gid)
        user = user.replace("{content_json}", json.dumps(data, ensure_ascii=False, indent=1))
        user = user.replace("{dict_json}", dict_json)
        user = user.replace("{ref_json}", ref_json)
        system = system.replace("{game_id}", gid)
        system = system.replace("{title}", data.get("title", ""))
        print(f"  LLM 审稿 [{gid}] ...", flush=True)
        raw = _llm_ask(api_key, base_url, model, system, user)
        try:
            report = json.loads(_strip_fence(raw))
        except Exception:
            report = {"game_id": gid, "overall_score": None,
                      "issues": [{"severity": "warning", "section": "?", "detail": "LLM 输出非 JSON", "fix": raw[:500]}]}
            print(f"  ⚠ [{gid}] LLM 输出非 JSON，原样存档", flush=True)
        report["game_id"] = gid
        reports.append(report)
    return reports


def _strip_fence(raw: str) -> str:
    """剥掉 LLM 输出可能带的 ```json 围栏。"""
    s = raw.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json"):
            s = s[4:]
        s = s.strip()
    return s


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="LoomQ 内容批量审稿")
    ap.add_argument("--llm", action="store_true", help="额外跑 LLM 审稿")
    args = ap.parse_args()

    print("=== [1/2] 静态检查（词典 + 游戏内容 JSON）===")
    errors = static_check()
    if errors:
        print(f"✗ 发现 {len(errors)} 个问题：")
        for e in errors[:20]:
            print(f"  [{e['severity']}] {e['game']}: {e['detail']}")
        if len(errors) > 20:
            print(f"  ... 共 {len(errors)} 个")
    else:
        print(f"✓ 静态检查通过（{len(list(GAME_DIR.glob('*.json')))} 个游戏 JSON + 词典 {len(qc_dict.DICT)} 词条）")

    if not args.llm:
        print("\n提示：加 --llm 可跑 LLM 审稿（需在 config.yaml 填 llm_user_api_key）")
        return

    print("=== [2/2] LLM 审稿 ===")
    api_key = _load_key()
    if not api_key:
        print("✗ 未找到有效 API key（config.yaml 的 llm_user_api_key 需形如 'sk-...'），LLM 审稿跳过")
        print("  说明：LLM 审稿需在 Web 设置面板填入 DeepSeek key 后再跑；静态检查已通过")
        return
    reports = llm_review(api_key)
    today = date.today().strftime("%Y%m%d")
    json_path = REPORT_DIR / f"content_review_{today}.json"
    md_path = REPORT_DIR / f"content_review_{today}.md"
    json_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    # 可读报告
    lines = [f"# LoomQ 内容审稿报告 {today}", ""]
    for r in reports:
        lines.append(f"## {r.get('game_id')} — 综合评分 {r.get('overall_score', '?')}/10（verdict: {r.get('verdict', '?')}）")
        for issue in r.get("issues", []):
            lines.append(f"- **[{issue.get('severity')}]** ({issue.get('section')}) {issue.get('detail')}")
            if issue.get("fix"):
                lines.append(f"  → 建议：{issue['fix']}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ LLM 审稿完成：{json_path} + {md_path}")
    for r in reports:
        n = len(r.get("issues", []))
        print(f"  [{r.get('game_id')}] score={r.get('overall_score')} verdict={r.get('verdict')} issues={n}")


if __name__ == "__main__":
    main()
