"""
新项目统一 API key 加载器（模板版）。

规则：
- 所有服务 key 一律经本模块取用：env 变量 → config.yaml。
- 禁止在任何脚本中硬编码 key 字面量（sk-… / AKLT…）。
- 无 key 时返回 None / False，调用方自行降级，不抛异常。

用法：
  from key_loader import get_deepseek, get_ark, get_secret
  key = get_secret("deepseek_api_key")
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# 仓库根 = <project>（本文件位于 <project>/public/scripts/）
# 注意：以 REPO_ROOT 为界，只读本项目 config.yaml，绝不向上越界查找
#（防止模板/脚本嵌入其他项目时误读父级项目的真实配置）
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _find_config_yaml():
    """本项目根的 config.yaml；不存在返回 None（不越界向上找）。"""
    p = REPO_ROOT / "config.yaml"
    return p if p.exists() else None


def _load_config() -> dict:
    path = _find_config_yaml()
    if path is None:
        return {}
    cfg: dict = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    continue
                k, _, v = line.partition(":")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k:
                    cfg[k] = v
    except Exception:
        return {}
    return cfg


_CFG = _load_config()


def get_secret(key: str) -> str | None:
    """任意服务 key：env（同名变量）优先 → config.yaml。"""
    v = os.getenv(key)
    if v:
        return v.strip()
    k = _CFG.get(key)
    return (k or "").strip() or None


def get_deepseek() -> dict:
    """DeepSeek（调研报告/科普文章，deepseek-v4-pro）。"""
    return {
        "api_key": get_secret("deepseek_api_key"),
        "base_url": (_CFG.get("deepseek_base_url") or "https://api.deepseek.com/chat/completions").strip(),
        "model": (_CFG.get("deepseek_model") or "deepseek-v4-pro").strip(),
    }


def get_ark() -> dict:
    """豆包 ARK 平台（seedance 2.0 做图等）。"""
    return {
        "api_key": get_secret("ark_api_key"),
        "endpoint": (_CFG.get("ark_endpoint") or "").strip(),
    }


def set_secret(key: str, value: str) -> bool:
    """把 key=value 写回 config.yaml：已有该键则原地替换该行（保留注释与其他键），
    不存在则追加到文件末尾。供 Web 设置面板等运行时写入（如 llm_user_api_key）。

    注意：config.yaml 底部注释块（备忘）不参与解析，set_secret 只匹配非注释键行。
    """
    path = _find_config_yaml()
    if path is None:
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return False
    pat = re.compile(rf"^\s*{re.escape(key)}\s*:")
    out: list[str] = []
    hit = False
    for line in lines:
        if pat.match(line):
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f'{indent}{key}: "{value}"')
            hit = True
        else:
            out.append(line)
    if not hit:
        out.append(f'{key}: "{value}"')
    try:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    except Exception:
        return False
    _CFG[key] = value  # 内存同步（本进程内后续 get_secret 立即可见）
    return True


if __name__ == "__main__":
    d = get_deepseek()
    print(f"deepseek key set = {bool(d['api_key'])}  model = {d['model']}")
    a = get_ark()
    print(f"ark key set = {bool(a['api_key'])}")
