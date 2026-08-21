#!/usr/bin/env python3
"""LoomQ L3 噪声模拟器。

建模（用户确认的 4 参数）：
  1. T1/T2 退相干（简化：用门错误近似，教育版不做时序演化）
  2. gate_error（退极化：每门以 p 概率对作用比特加随机 X/Y/Z 泡利错误）
  3. readout_error（测量：以 p 概率翻转结果）
  4. coupling_map（拓扑：不直接耦合的双比特门需插 SWAP → 增加错误）

设计：在"尺子"（理想态矢量模拟）基础上注入噪声，返回带噪 counts。
这是教育仿真——展示"真实量子计算机目前为什么'没用'"（比特少/线路浅/噪声大）。

用法：
    from loomq_lib.noise import noisy_simulate, MACHINE_PARAMS
    counts = noisy_simulate(qasm, "grid", shots=8192)
"""

import random
from typing import Dict, List

from .semantics import Circuit, evolve, _MATS, _apply_single, _apply_cx

# 四台机器参数（与 web/qc_dict.py 保持一致）
MACHINE_PARAMS = {
    "ideal": {"gate_fidelity": 1.0, "readout_error": 0.0, "topology": "full"},
    "linear": {"gate_fidelity": 0.995, "readout_error": 0.005, "topology": "line"},
    "grid": {"gate_fidelity": 0.99, "readout_error": 0.01, "topology": "grid"},
    "noisy": {"gate_fidelity": 0.97, "readout_error": 0.03, "topology": "line"},
}

# 拓扑：哪些 (q1, q2) 对可直接做双比特门
_TOPOLOGY = {
    "full": lambda n: [(i, j) for i in range(n) for j in range(i + 1, n)],
    "line": lambda n: [(i, i + 1) for i in range(n - 1)],
    # 2D 网格（简化：按行排列，每行 width=4 列，行内相邻 + 跨行同列）
    "grid": lambda n: _grid_pairs(n, 4),
}


def _grid_pairs(n: int, width: int) -> List[tuple]:
    pairs = set()
    for q in range(n):
        r, c = q // width, q % width
        # 右邻居
        if c + 1 < width and q + 1 < n:
            pairs.add((q, q + 1))
        # 下邻居
        if q + width < n:
            pairs.add((q, q + width))
    return sorted(pairs)

# 泡利错误（对单比特态）
_PAULI = {
    "x": lambda psi, q, n: _apply_single(_MATS["x"], q, n) @ psi,
    "y": lambda psi, q, n: _apply_single(_MATS["y"], q, n) @ psi,
    "z": lambda psi, q, n: _apply_single(_MATS["z"], q, n) @ psi,
}


def _depolarize(psi, qubits, error_rate, n, rng):
    """对 qubits 上的每个比特以 error_rate 概率施加随机泡利错误。"""
    for q in qubits:
        if rng.random() < error_rate:
            err = rng.choice(["x", "y", "z"])
            psi = _PAULI[err](psi, q, n)
    return psi


def _apply_gate(psi, op, n, params, rng):
    """应用一个门（含噪声 + 拓扑 SWAP 惩罚）。"""
    name = op[0]
    qargs = op[1]
    vals = op[2]
    err_rate = 1.0 - params["gate_fidelity"]

    # barrier 无量子语义，跳过
    if name == "barrier":
        return psi

    # 双比特门拓扑检查：非直接耦合 → 插 SWAP（每 SWAP 也带错误）
    if len(qargs) == 2 and params["topology"] != "full":
        a, b = qargs
        if (a, b) not in _TOPOLOGY[params["topology"]](n) and \
           (b, a) not in _TOPOLOGY[params["topology"]](n):
            # 简化：直接当一次额外错误（教育版不做完整 SWAP 路由）
            psi = _depolarize(psi, [a, b], err_rate, n, rng)

    # 应用门（理想逻辑）
    if name == "cx":
        psi = _apply_cx(qargs[0], qargs[1], n) @ psi
    elif name == "swap":
        a, b = qargs
        for c, t in ((a, b), (b, a), (a, b)):
            psi = _apply_cx(c, t, n) @ psi
    elif name == "ccx":
        a, b, c = qargs
        seq = [("h", [c]), ("cx", [b, c]), ("tdg", [c]), ("cx", [a, c]),
               ("t", [c]), ("cx", [b, c]), ("tdg", [c]), ("cx", [a, c]),
               ("t", [b]), ("t", [c]), ("h", [c]), ("cx", [a, b]),
               ("t", [a]), ("tdg", [b]), ("cx", [a, b])]
        for g, gq in seq:
            if g == "cx":
                psi = _apply_cx(gq[0], gq[1], n) @ psi
            else:
                psi = _apply_single(_MATS[g], gq[0], n) @ psi
    elif name == "cu1":
        a, b = qargs
        lam = vals[0]
        psi = _apply_single(_MATS["u1"](lam / 2), a, n) @ psi
        psi = _apply_cx(a, b, n) @ psi
        psi = _apply_single(_MATS["u1"](-lam / 2), b, n) @ psi
        psi = _apply_cx(a, b, n) @ psi
        psi = _apply_single(_MATS["u1"](lam / 2), b, n) @ psi
    elif name in _MATS:
        target = qargs[0]
        mat = _MATS[name] if not vals else _MATS[name](*vals)
        psi = _apply_single(mat, target, n) @ psi
    else:
        raise ValueError(f"未知门: {name}")

    # 门后退极化噪声
    psi = _depolarize(psi, qargs, err_rate, n, rng)
    return psi


def noisy_counts(qasm: str, machine: str, shots: int = 8192, seed: int = None) -> Dict[str, int]:
    """带噪声的 counts 模拟（含测量错误）。

    Args:
        qasm: OpenQASM 2.0
        machine: "ideal"/"linear"/"grid"/"noisy"
        shots: 采样次数
        seed: 随机种子（可复现）
    Returns:
        counts: {位串: 次数}
    """
    params = MACHINE_PARAMS[machine]
    rng = random.Random(seed)

    circuit = Circuit(qasm)
    n = circuit.n

    # 逐门演化（含噪声）
    import numpy as np
    psi = np.zeros(2 ** n, dtype=complex)
    psi[0] = 1.0
    for op in circuit.ops:
        psi = _apply_gate(psi, op, n, params, rng)

    # 测量（含 readout_error）
    probs = np.abs(psi) ** 2
    counts = {}
    ro = params["readout_error"]
    for _ in range(shots):
        # 按概率采样基础态
        r = rng.random()
        acc = 0.0
        outcome = 0
        for i, p in enumerate(probs):
            acc += p
            if r < acc:
                outcome = i
                break
        bits = format(outcome, f"0{n}b")[::-1]
        # 测量错误：每位以 ro 概率翻转
        if ro > 0:
            bits = "".join("1" if (b == "0" and rng.random() < ro)
                           else "0" if (b == "1" and rng.random() < ro) else b
                           for b in bits)
        counts[bits] = counts.get(bits, 0) + 1
    return counts


def machine_education(machine: str) -> dict:
    """返回某机器的教育提示（为什么量子计算机目前'没用'）。"""
    p = MACHINE_PARAMS[machine]
    if machine == "ideal":
        msg = "理想机：完美的量子计算机（现实中不存在）。用来对照——看正确分布长什么样。"
    else:
        err = (1 - p["gate_fidelity"]) * 100
        msg = (f"{machine} 机：每个门有 {err:.1f}% 概率出错。"
               f"如果线路有 100 个门，最终错误率 ≈ {100 * (1 - p['gate_fidelity'] ** 100):.1f}%！"
               f"这就是为什么现在的量子计算机只能跑很浅的线路——噪声会淹没信号。")
    return {"machine": machine, "gate_fidelity": p["gate_fidelity"],
            "readout_error": p["readout_error"], "msg": msg}
