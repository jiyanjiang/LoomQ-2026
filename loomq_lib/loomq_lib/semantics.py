#!/usr/bin/env python3
"""LoomQ 对齐"尺子"—— OpenQASM 2.0 语义模拟器（独立实现）。

基准定义：OpenQASM 2.0 官方标准门库（qelib1.inc，Qiskit Terra 维护），
所有门由底层 U(θ,φ,λ) 原语展开，用 numpy 做态矢量演化，输出精确参考分布。

这是判断 transpile/后端正确性的独立裁判，不依赖任何厂商 SDK。
从 tests/qasm_semantics.py 移植核心逻辑（去 CLI，供 pip 包使用）。
"""

import cmath
import math
import re
from typing import Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# U 门原语
# ---------------------------------------------------------------------------


def U(θ: float, φ: float, λ: float) -> np.ndarray:
    a = cmath.exp(-1j * (φ + λ) / 2) * math.cos(θ / 2)
    b = -cmath.exp(-1j * (φ - λ) / 2) * math.sin(θ / 2)
    c = cmath.exp(1j * (φ - λ) / 2) * math.sin(θ / 2)
    d = cmath.exp(1j * (φ + λ) / 2) * math.cos(θ / 2)
    return np.array([[a, b], [c, d]], dtype=complex)


def I() -> np.ndarray:
    return np.eye(2, dtype=complex)


PI = math.pi
HALF = math.pi / 2
QUARTER = math.pi / 4

# 底层基元矩阵（qelib1.inc 展开后的最终形式）
_MATS = {
    "u1": lambda λ: U(0, 0, λ),
    "u2": lambda φ, λ: U(HALF, φ, λ),
    "u3": lambda θ, φ, λ: U(θ, φ, λ),
    "h": U(HALF, 0, PI),
    "x": U(PI, 0, PI),
    "y": U(PI, HALF, HALF),
    "z": U(0, 0, PI),
    "s": U(0, 0, HALF),
    "sdg": U(0, 0, -HALF),
    "t": U(0, 0, QUARTER),
    "tdg": U(0, 0, -QUARTER),
    "rx": lambda θ: U(θ, -HALF, HALF),
    "ry": lambda θ: U(θ, 0, 0),
    "rz": lambda φ: U(0, 0, φ),
}

# 12 门白名单
WHITELIST_GATES = frozenset(
    {"h", "x", "s", "sdg", "t", "tdg", "rz", "ry", "cx", "cu1", "swap", "ccx"}
)


def _tensor(parts: List[np.ndarray]) -> np.ndarray:
    result = parts[0]
    for p in parts[1:]:
        result = np.kron(result, p)
    return result


def _apply_single(gate: np.ndarray, target: int, n: int) -> np.ndarray:
    parts = [I()] * n
    parts[target] = gate
    return _tensor(parts)


def _apply_cx(control: int, target: int, n: int) -> np.ndarray:
    dim = 2 ** n
    M = np.zeros((dim, dim), dtype=complex)
    for i in range(dim):
        if (i >> (n - 1 - control)) & 1:
            j = i ^ (1 << (n - 1 - target))
        else:
            j = i
        M[j, i] = 1.0
    return M


def _parse_number(tok: str) -> float:
    tok = tok.strip()
    if tok == "pi":
        return PI
    m = re.match(r"^([-+]?[0-9.]*)\s*\*?\s*pi\s*(?:/\s*([0-9]+))?$", tok)
    if m:
        num = float(m.group(1)) if m.group(1) not in ("", "+", "-") else 1.0
        den = int(m.group(2)) if m.group(2) else 1
        if m.group(1) in ("", "+", "-"):
            num = 1.0 if m.group(1) in ("", "+") else -1.0
        return num / den * PI
    return float(tok)


class Circuit:
    """解析 QASM 2.0 为 (n_qubits, 门操作列表)。"""

    def __init__(self, qasm: str):
        self.n = 0
        self.ops: List[Tuple[str, List[int], List[float]]] = []
        self._parse(qasm)

    def _parse(self, qasm: str):
        code = re.sub(r"//.*$", "", qasm, flags=re.MULTILINE)
        for chunk in code.replace(";", ";\n").splitlines():
            line = chunk.strip()
            if not line:
                continue
            if line.startswith("OPENQASM") or line.startswith("include"):
                continue
            m = re.match(r"qreg\s+\w+\s*\[\s*(\d+)\s*\]", line)
            if m:
                self.n = int(m.group(1))
                continue
            m = re.match(r"creg\s+", line)
            if m:
                continue
            if line.startswith("measure"):
                continue
            m = re.match(r"(\w+)\s*\(([^)]*)\)\s*(.*)", line)
            if m:
                name, params, rest = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
                qargs = [int(x) for x in re.findall(r"\[(\d+)\]", rest)]
                vals = [_parse_number(t) for t in params.split(",") if t.strip()]
                self.ops.append((name, qargs, vals))
                continue
            m = re.match(r"(\w+)\s*(.*)", line)
            if m:
                name, rest = m.group(1).strip(), m.group(2).strip()
                qargs = [int(x) for x in re.findall(r"\[(\d+)\]", rest)]
                self.ops.append((name, qargs, []))
                continue


def evolve(circuit: Circuit) -> np.ndarray:
    n = circuit.n
    if n > 14:
        raise ValueError(f"n={n} 超出态矢量模拟规模上限（14）")
    psi = np.zeros(2 ** n, dtype=complex)
    psi[0] = 1.0
    for name, qargs, vals in circuit.ops:
        if name == "barrier":
            continue
        if name == "cx":
            control, target = qargs
            psi = _apply_cx(control, target, n) @ psi
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
            for g_name, g_args in seq:
                if g_name == "cx":
                    psi = _apply_cx(g_args[0], g_args[1], n) @ psi
                else:
                    psi = _apply_single(_MATS[g_name], g_args[0], n) @ psi
        elif name == "cu1":
            a, b = qargs
            λ = vals[0]
            psi = _apply_single(_MATS["u1"](λ / 2), a, n) @ psi
            psi = _apply_cx(a, b, n) @ psi
            psi = _apply_single(_MATS["u1"](-λ / 2), b, n) @ psi
            psi = _apply_cx(a, b, n) @ psi
            psi = _apply_single(_MATS["u1"](λ / 2), b, n) @ psi
        elif name in _MATS:
            target = qargs[0]
            mat = _MATS[name] if not vals else _MATS[name](*vals)
            psi = _apply_single(mat, target, n) @ psi
        else:
            raise ValueError(f"未知门: {name}")
    return psi


def reference_distribution(qasm: str) -> Dict[str, float]:
    """返回精确参考分布（Qiskit 位序：key 最右 = q[0]）。"""
    circuit = Circuit(qasm)
    psi = evolve(circuit)
    probs = np.abs(psi) ** 2
    n = circuit.n
    dist = {}
    for i, p in enumerate(probs):
        if p > 1e-12:
            bits = format(i, f"0{n}b")[::-1]
            dist[bits] = round(float(p), 12)
    return dist
