"""
新项目统一配置加载器（模板版，从 loomsci_lexicon 提炼）。

规则：
- 程序只写相对路径；绝对路径只出现在本机 config.yaml。
- 相对路径一律基于「仓库根」（本文件上两级：<project>/public/scripts/ 的上级上级 = <project>）。
- config.yaml 读取失败/缺失时回退到默认值（跑 demo 不需任何配置）。
- 零第三方依赖（极简键值解析），便于在任意分享环境中运行。
"""
import os
from pathlib import Path

# 仓库根 = <project>（本文件位于 <project>/public/scripts/）
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_cfg() -> dict:
    """读取仓库根 config.yaml（极简键值解析）。缺失/失败返回空 dict。"""
    p = REPO_ROOT / "config.yaml"
    if not p.exists():
        return {}
    cfg: dict = {}
    try:
        with open(p, encoding="utf-8") as f:
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


_CFG = _load_cfg()


def get(key: str, default: str = "") -> str:
    """读取任意配置字段（含 API key；无值返回 default）。"""
    v = _CFG.get(key)
    return v if v not in (None, "") else default


def path(key: str, default: str) -> Path:
    """路径字段：config.yaml 优先；相对路径基于仓库根解析；绝对路径原样保留。"""
    v = _CFG.get(key)
    if not v:
        return REPO_ROOT / default
    p = Path(v)
    return p if p.is_absolute() else REPO_ROOT / v


# ============================================================
# 标准路径（程序一律引用这些常量，禁止手写路径字符串）
# ============================================================
PUBLIC_DATA_DIR = path("public_data_dir", "public/data")
PRIVATE_DATA_DIR = path("private_data_dir", "private/data")
EXPERIMENTS_DIR = path("experiments_dir", "public/docs/experiments")
STYLE_DIR = path("style_dir", "public/style")
DEFAULT_STYLE = get("default_style", "QJ_5.md")


def venv_info() -> dict:
    """返回 venv 环境信息（SOP §0 要求记录在配置中）。"""
    return {
        "venv_path": get("venv_path", ""),
        "python_version": get("python_version", "3.12"),
    }
