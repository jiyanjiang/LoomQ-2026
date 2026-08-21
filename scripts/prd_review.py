#!/usr/bin/env python3
"""PRD 审核脚本：把 docs/PRD.md + PRD_SELFCHECK.md 发给 DeepSeek v4 pro 审核。

脱敏：key 经 key_loader 读取（env → config.yaml）。
用法：python scripts/prd_review.py --out data/prd_review_20260818.json
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "public" / "scripts"))
import key_loader  # noqa: E402

# 相关文件（输入给 DS）
INPUT_FILES = [
    "docs/PRD.md",
    "docs/PRD_SELFCHECK.md",
    "starter_kit/evidence/README.md",
]


def load_review_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    cfg: dict = {}
    current = None
    buf: list = []
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


def build_messages(prompt: dict) -> list:
    docs = []
    for rel in INPUT_FILES:
        p = ROOT / rel
        if p.exists():
            docs.append(f"### 文件: {rel}\n\n{p.read_text(encoding='utf-8')[:8000]}")
    user = "\n\n".join(docs)
    user += "\n\n## 审核目标\n" + prompt.get("review_targets", "")
    user += "\n\n## 任务\n" + prompt.get("task", "")
    user += "\n\n## 输出格式\n" + prompt.get("output_format", "")
    return [
        {"role": "system", "content": prompt.get("system", "")},
        {"role": "user", "content": user},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default=str(ROOT / "prompts" / "prd_review_v1.yaml"))
    ap.add_argument("--out", default=str(ROOT / "data" / "prd_review_20260818.json"))
    args = ap.parse_args()

    prompt = load_review_yaml(Path(args.prompt))
    messages = build_messages(prompt)
    conf = key_loader.get_deepseek()
    if not conf["api_key"]:
        print("未配置 DeepSeek key"); return 1
    base = conf["base_url"].rstrip("/")
    if not base.endswith("/chat/completions"):
        base += "/chat/completions"
    payload = {"model": conf["model"], "messages": messages, "stream": False,
               "temperature": 0, "max_tokens": 8192, "thinking": {"type": "disabled"}}
    req = urllib.request.Request(base, data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": "Bearer " + conf["api_key"], "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.read().decode()[:300]}"); return 1
    content = body["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        s, e = content.find("{"), content.rfind("}")
        if s < 0 or e < 0:
            print("非 JSON:", content[:500]); return 1
        parsed = json.loads(content[s:e + 1])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"审核结果已保存: {out}")
    print("contradictions:", len(parsed.get("contradictions", [])))
    print("missing_features:", len(parsed.get("missing_features", [])))
    print("priority:", list(parsed.get("priority_7days", {}).keys()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
