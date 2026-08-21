#!/usr/bin/env python3
"""门映射审查脚本：把 prompts/gate_mapping_review_v1.yaml 组装成消息发给 DeepSeek v4 pro。

脱敏：key 一律经 key_loader 读取（env → config.yaml），脚本内无明文 key。
用法：python scripts/gate_mapping_review.py --out data/gate_mapping_review_20260818.json
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "public" / "scripts"))
import key_loader  # noqa: E402


def load_prompt_yaml(path: Path) -> dict:
    """极简 yaml 读取（本项目提示词是扁平的 key: 块结构，无嵌套 list/dict 语法）。"""
    text = path.read_text(encoding="utf-8")
    cfg: dict = {}
    current: str | None = None
    buf: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            if current:
                cfg[current] = "\n".join(buf).strip()
            key, _, val = line.partition(":")
            current = key.strip()
            buf = [val.strip()] if val.strip() else []
        elif current:
            buf.append(line)
    if current:
        cfg[current] = "\n".join(buf).strip()
    return cfg


def build_messages(prompt: dict) -> list[dict]:
    system = prompt.get("system", "")
    task = prompt.get("task", "")
    output_fmt = prompt.get("output_format", "")
    inputs = {k: v for k, v in prompt.items() if k in ("input", "gate_identities")}
    user = []
    for k, v in inputs.items():
        user.append(f"## {k}\n{v}")
    user.append(f"## task\n{task}")
    user.append(f"## output_format\n{output_fmt}")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user)},
    ]


def call_deepseek(messages: list[dict], out_path: Path) -> None:
    conf = key_loader.get_deepseek()
    api_key = conf["api_key"]
    if not api_key:
        raise RuntimeError("deepseek_api_key 未配置（env DEEPSEEK_API_KEY 或 config.yaml）")
    base = conf["base_url"].strip()
    if not base.endswith("/chat/completions"):
        base = base.rstrip("/") + "/chat/completions"
    model = conf["model"]
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0,
        "max_tokens": 8192,
        # v4 pro 默认 thinking 会占满 max_tokens 导致 content 空；显式关闭
        "thinking": {"type": "disabled"},
    }
    req = urllib.request.Request(
        base,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DeepSeek 不可达: {exc}") from exc

    content = body["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取第一个 { ... } 块
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end < 0:
            raise RuntimeError("DeepSeek 输出不是 JSON:\n" + content[:800])
        parsed = json.loads(content[start : end + 1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"评审结果已保存: {out_path}")
    print(f"matrix 门数: {len(parsed.get('matrix', {}))}")
    print(f"answers: {list(parsed.get('answers', {}).keys())}")
    print(f"confirmed: {len(parsed.get('summary', {}).get('confirmed', []))} 条")
    print(f"corrected: {len(parsed.get('summary', {}).get('corrected', []))} 条")


def main() -> int:
    ap = argparse.ArgumentParser(description="调用 DeepSeek v4 pro 审查门映射表")
    ap.add_argument("--prompt", default=str(ROOT / "prompts" / "gate_mapping_review_v1.yaml"))
    ap.add_argument("--out", default=str(ROOT / "data" / "gate_mapping_review_20260818.json"))
    args = ap.parse_args()
    prompt = load_prompt_yaml(Path(args.prompt))
    messages = build_messages(prompt)
    call_deepseek(messages, Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
