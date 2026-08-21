#!/usr/bin/env python3
"""新项目分享打包器（模板版，含内容级防泄漏扫描）。

只读 public/ + 根级白名单；扫描所有进包文本文件的内容，
命中隐私正则（绝对路径 / API key 字面量）即 fail-fast 拒绝出包。

用法：
  python tools/make_share_package.py            # 输出 share_<project>_YYYYMMDD.tar.gz
  python tools/make_share_package.py --dry      # 只扫描校验，不出包
"""
import argparse
import datetime
import os
import re
import shutil
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT.name

# 根级白名单：随包分享的根文件
ROOT_FILES = [
    "README.md", "LICENSE", "requirements.txt",
    "config.example.yaml", "SOP.md", "SHARE_MANIFEST.md",
]

# 进包文本文件扩展名（需要内容扫描）
TEXT_EXTS = {".py", ".yaml", ".yml", ".json", ".csv", ".md", ".html", ".txt", ".toml", ".cfg"}

# 防泄漏正则（命中即拒绝）
LEAK_PATTERNS = [
    (r"/Users/[A-Za-z0-9_\-]+/", "本地绝对路径(/Users/…)"),
    (r"/home/[A-Za-z0-9_\-]+/", "本地绝对路径(/home/…)"),
    (r"[A-Za-z]:\\", "Windows 绝对路径"),
    (r"sk-[A-Za-z0-9]{20,}", "疑似 DeepSeek/OpenAI key"),
    (r"AKLT[A-Za-z0-9]{8,}", "疑似火山/ARK key"),
    (r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9]{16,}['\"]", "配置中内联 key"),
]
_LEAK_RE = [(re.compile(p), label) for p, label in LEAK_PATTERNS]


def scan_text(path: Path) -> list[str]:
    """扫描文本文件内容，返回命中描述列表（空=干净）。"""
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        for rx, label in _LEAK_RE:
            if rx.search(line):
                hits.append(f"  {path} :{lineno}  [{label}]  {line.strip()[:100]}")
    return hits


def scan_all(stage: Path) -> list[str]:
    """扫描 stage 下所有文本文件，返回全部命中。"""
    all_hits: list[str] = []
    for p in stage.rglob("*"):
        if p.is_file() and p.suffix.lower() in TEXT_EXTS:
            all_hits.extend(scan_text(p))
    return all_hits


def build_stage(stage: Path) -> None:
    """复制分享内容到 staging：public/ 全量 + 根级白名单。"""
    os.makedirs(stage, exist_ok=True)

    # public/ 全量
    src = ROOT / "public"
    if src.exists():
        shutil.copytree(src, stage / "public", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc"))

    # 根级白名单
    for f in ROOT_FILES:
        s = ROOT / f
        if s.exists():
            shutil.copy2(s, stage / f)


def main() -> int:
    ap = argparse.ArgumentParser(description="新项目分享打包（public 全量 + 防泄漏扫描）")
    ap.add_argument("--dry", action="store_true", help="只扫描校验，不出包")
    ap.add_argument("--out", default=str(ROOT), help="输出目录（默认项目根）")
    args = ap.parse_args()

    stamp = datetime.date.today().strftime("%Y%m%d")
    stage = ROOT / f".stage_{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    build_stage(stage)

    print("[1/3] 内容级防泄漏扫描 ...")
    hits = scan_all(stage)
    if hits:
        print("  ✗ 检测到敏感内容，拒绝出包：")
        for h in hits:
            print(h)
        shutil.rmtree(stage, ignore_errors=True)
        return 1
    print("  ✓ 干净（0 命中）")

    print("[2/3] 白名单校验 ...")
    checks = [
        ("config.yaml 已排除", not (stage / "config.yaml").exists()),
        ("private/ 已排除", not (stage / "private").exists()),
        ("tools/ 已排除", not (stage / "tools").exists()),
        ("config.example.yaml 已包含", (stage / "config.example.yaml").exists()),
        ("public/ 已包含", (stage / "public").exists()),
    ]
    for label, ok in checks:
        print(f"  {'✓' if ok else '✗'} {label}")
    if not all(ok for _, ok in checks):
        shutil.rmtree(stage, ignore_errors=True)
        return 1

    if args.dry:
        print("[3/3] --dry：跳过打包")
        shutil.rmtree(stage, ignore_errors=True)
        return 0

    print("[3/3] 打包 ...")
    tarball = Path(args.out) / f"share_{PROJECT}_{stamp}.tar.gz"
    with tarfile.open(tarball, "w:gz") as tar:
        tar.add(stage, arcname=f"{PROJECT}")
    size_mb = os.path.getsize(tarball) / 1e6
    shutil.rmtree(stage, ignore_errors=True)
    print(f"  → {tarball} ({size_mb:.1f} MB)")
    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
