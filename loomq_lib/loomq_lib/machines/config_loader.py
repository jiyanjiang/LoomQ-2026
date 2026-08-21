"""量子云机器注册表读取器。

读取 <repo>/config/machines.yaml（真实配置，gitignore），返回机器列表。
规则：
- 只读 config/machines.yaml；文件不存在/解析失败/无 yaml 库 → 返回 []（调用方自行降级）。
- 不做认证校验（认证在 driver 层）；本模块只管"声明式注册表 → 内存对象"。
- 模板 config/machines.yaml.example 永不被读取（防止占位符被当真值）。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# 本文件位于 <repo>/loomq_lib/loomq_lib/machines/config_loader.py
# REPO_ROOT = 仓库根（以它为界找 config/machines.yaml，不向上越界）
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_MACHINES_YAML = REPO_ROOT / "config" / "machines.yaml"


def _load_yaml(path: Path) -> dict | None:
    try:
        import yaml  # PyYAML（loomq310 venv 已装 6.0.3）
    except ImportError:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def load_machines() -> list[dict]:
    """返回机器注册表列表；任何失败返回 []。"""
    if not _MACHINES_YAML.exists():
        return []
    data = _load_yaml(_MACHINES_YAML)
    if not data:
        return []
    machines = data.get("machines", [])
    return [m for m in machines if isinstance(m, dict)]


def get_machine(machine_id: str) -> dict | None:
    """按全局唯一 id 取机器；不存在返回 None。"""
    for m in load_machines():
        if m.get("id") == machine_id:
            return m
    return None


def available_machines() -> list[dict]:
    """status == available 的机器（路由/竞技场/状态自检都基于它）。"""
    return [m for m in load_machines() if m.get("status") == "available"]


if __name__ == "__main__":
    ms = load_machines()
    print(f"machines.yaml: {_MACHINES_YAML}")
    if not ms:
        print("  未配置（config/machines.yaml 不存在或为空）→ 返回 []")
    else:
        for m in ms:
            print(f"  - {m.get('id')}  {m.get('name')}  bits={m.get('bits')}  "
                  f"driver={m.get('driver')}  status={m.get('status')}")
        print(f"  available: {[m.get('id') for m in available_machines()]}")
