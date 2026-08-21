"""量子真机在线状态探活（首页驾驶舱 /api/machines/status 用）。

铁律：
- 只做只读探活，绝不 submit 任何作业 —— 悟空 token 校验不消耗机时（收费机时）。
- spinq    ：官方 SDK get_spinq_cloud 登录 + get_platform(pcode).available() 查在线。
- originq  ：pyqpanda QCloud.init_qvm(token) + get_realtime_topology(chip_id) 只读查询。
- 任何异常都降级为 (False, 原因)，绝不抛给调用方；单台最多等待 PING_TIMEOUT 秒。
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

PING_TIMEOUT = 15.0  # 单台探活最久等待秒数（首页加载不被拖死）

# 机器 id → 平台 pcode（machines.yaml 也可显式写 pcode 字段覆盖）
SPINQ_PCODE = {
    "spinq_gemini_2q": "gemini_vp",
    "spinq_triangulum_3q": "triangulum_vp",
}

_REPO = Path(__file__).resolve().parent.parent.parent.parent


def _get_token(cfg: dict) -> str | None:
    """悟空 token 读取链：machines.yaml connect.token → connect.token_env 环境变量 → config.yaml originq_api_token。"""
    conn = cfg.get("connect") or {}
    tok = (conn.get("token") or "").strip()
    if not tok:
        env_name = (conn.get("token_env") or "").strip()
        if env_name:
            tok = (os.getenv(env_name) or "").strip()
    if not tok:
        tok = (os.getenv("originq_api_token") or "").strip()
    if not tok:
        try:
            p = _REPO / "config.yaml"
            if p.exists():
                import yaml
                data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                v = data.get("originq_api_token")
                if v:
                    tok = str(v).strip()
        except Exception:
            pass
    return tok or None


def ping_spinq(cfg: dict) -> tuple[bool, str]:
    """SpinQ 云：SDK 登录（内部做私钥/账号认证）+ 平台机型可用性检查。"""
    conn = cfg.get("connect") or {}
    user = (conn.get("user") or "").strip()
    key_path = os.path.expanduser((conn.get("key_path") or "").strip())
    pcode = (cfg.get("pcode") or SPINQ_PCODE.get(cfg.get("id")) or "").strip()
    if not user:
        return False, "未配置 SpinQ 云账号"
    if not key_path:
        return False, "未配置 SpinQ 私钥路径"
    if not pcode:
        return False, "未知机型 pcode"
    try:
        from spinqit.backend import get_spinq_cloud
    except Exception as e:  # noqa: BLE001
        return False, f"spinqit SDK 不可用: {type(e).__name__}"
    try:
        backend = get_spinq_cloud(user, key_path)
        platform = backend.get_platform(pcode)
        available = getattr(platform, "available", None)
        online = bool(available()) if callable(available) else (getattr(platform, "machine_count", 0) > 0)
        if online:
            return True, "在线"
        return False, "账号有效，但该机型当前不可用"
    except Exception as e:  # noqa: BLE001
        return False, f"连接失败: {type(e).__name__}"


def ping_originq(cfg: dict) -> tuple[bool, str]:
    """本源悟空：token 只读校验（init_qvm 认证 + 芯片拓扑查询，无任务提交、不耗机时）。"""
    token = _get_token(cfg)
    if not token:
        return False, "未配置本源云 Token（设置→账户 填写）"
    chip_id = int((cfg.get("connect") or {}).get("chip_id") or 180)
    try:
        from pyqpanda import QCloud
    except Exception as e:  # noqa: BLE001
        return False, f"pyqpanda SDK 不可用: {type(e).__name__}"
    try:
        qc = QCloud()
        qc.init_qvm(token)  # token 有效性校验（只读握手）
        qc.get_realtime_topology(chip_id)  # 只读查询芯片实时拓扑，不提交任务
        return True, "在线"
    except Exception as e:  # noqa: BLE001
        return False, f"Token 校验失败: {type(e).__name__}"


_PING_FN = {"spinq": ping_spinq, "originq": ping_originq}


def ping_machine(cfg: dict) -> dict:
    """探活单台机器，永不抛异常。"""
    mid = cfg.get("id")
    fn = _PING_FN.get(cfg.get("driver") or "")
    if fn is None:
        return {"id": mid, "online": False, "reason": f"未知 driver: {cfg.get('driver')}"}
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(fn, cfg)
            online, reason = fut.result(timeout=PING_TIMEOUT)
    except FutureTimeout:
        return {"id": mid, "online": False, "reason": f"检查超时（>{int(PING_TIMEOUT)}s）"}
    except Exception as e:  # noqa: BLE001
        return {"id": mid, "online": False, "reason": f"探活异常: {type(e).__name__}"}
    return {"id": mid, "online": bool(online), "reason": reason}


def ping_machines(machines: list[dict]) -> list[dict]:
    """并行探活多台（各自带独立线程，互不阻塞），按输入顺序返回。"""
    if not machines:
        return []
    with ThreadPoolExecutor(max_workers=len(machines)) as ex:
        return list(ex.map(ping_machine, machines))


if __name__ == "__main__":
    from config_loader import available_machines
    ms = available_machines()
    print(f"available machines: {[m.get('id') for m in ms]}")
    for item in ping_machines(ms):
        print(f"  - {item}")
