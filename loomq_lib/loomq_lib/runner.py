#!/usr/bin/env python3
"""LoomQ 统一执行入口：run_circuit() 带 fidelity 验证 + verify_circuit() 自验闭环。

这是 Web 界面的"心脏"——把电路 + 后端 + 参考分布 + 保真度判断封装成一个调用。
"""

import math
from typing import Dict, Optional

from .backends import SUPPORTED_TARGETS, run, transpile
from .semantics import reference_distribution, Circuit


def hellinger(p: Dict[str, float], q: Dict[str, float]) -> float:
    """Hellinger 保真度（与 evaluator.py 一致），≥0.97 视为对齐。"""
    keys = set(p) | set(q)
    d = math.sqrt(
        sum((math.sqrt(p.get(k, 0.0)) - math.sqrt(q.get(k, 0.0))) ** 2 for k in keys)
    ) / math.sqrt(2.0)
    return max(0.0, min(1.0, 1.0 - d))


def run_circuit(qasm: str, target: str = "spinq", shots: int = 8192) -> dict:
    """执行电路，返回 counts + 参考分布 + fidelity。

    Returns:
        {
          "qasm": ..., "target": ..., "shots": ...,
          "counts": {...},           # 后端实测（位序已归一化）
          "reference": {...},        # 尺子精确分布
          "fidelity": float,         # Hellinger
          "passed": bool,            # fidelity >= 0.97
          "transpiled": {...},       # 各后端契约 IR（可选）
        }
    """
    result = run(qasm, target, shots)
    total = sum(result["counts"].values())
    observed = {k: v / total for k, v in result["counts"].items()}
    try:
        reference = reference_distribution(qasm)
    except Exception as exc:
        reference = {}
        fidelity = 0.0
        passed = False
    else:
        fidelity = hellinger(reference, observed)
        passed = fidelity >= 0.97
    payload = {
        "qasm": qasm,
        "target": target,
        "shots": shots,
        "counts": result["counts"],
        "reference": reference,
        "fidelity": round(fidelity, 4),
        "passed": passed,
        "backend": result["backend"],
        "timestamp": result["timestamp"],
    }
    return payload


def verify_all_targets(qasm: str, shots: int = 8192) -> dict:
    """三后端全跑，返回各后端 fidelity 与整体结论。"""
    results = {}
    all_pass = True
    for t in SUPPORTED_TARGETS:
        try:
            r = run_circuit(qasm, t, shots)
            results[t] = r
            all_pass = all_pass and r["passed"]
        except Exception as exc:
            results[t] = {"target": t, "error": f"{type(exc).__name__}: {str(exc)[:100]}",
                          "passed": False}
            all_pass = False
    return {"results": results, "all_pass": all_pass}


def validate_qasm(qasm: str) -> tuple:
    """校验 QASM 2.0 是否可解析（尺子能否解析）。返回 (ok, error_msg)。"""
    if not qasm or "OPENQASM 2.0" not in qasm:
        return False, "不是有效的 OpenQASM 2.0 程序"
    try:
        circuit = Circuit(qasm)
        if circuit.n == 0:
            return False, "未声明 qreg"
        return True, ""
    except Exception as exc:
        return False, f"解析失败: {str(exc)[:100]}"
