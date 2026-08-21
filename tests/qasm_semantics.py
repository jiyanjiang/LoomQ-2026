#!/usr/bin/env python3
"""LoomQ 对齐"尺子"的机器实现 —— QASM 2.0 语义模拟器。

基准定义：OpenQASM 2.0 官方标准门库（qelib1.inc，Qiskit Terra 维护），
所有门由底层 U(θ,φ,λ) 原语展开，用 numpy 做态矢量演化，输出精确参考分布。

用法：
    python tests/qasm_semantics.py --qasm <file.qasm> [--json]
    # 或作为模块：
    from tests.qasm_semantics import reference_distribution
    dist = reference_distribution("OPENQASM 2.0; ...")

这不依赖任何厂商 SDK，是判断 transpile/后端正确性的独立裁判。
"""

import argparse
import cmath
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# U 门原语：U(θ,φ,λ) = [[e^{-i(φ+λ)/2}cos(θ/2), -e^{-i(φ-λ)/2}sin(θ/2)],
#                       [ e^{ i(φ-λ)/2}sin(θ/2),  e^{ i(φ+λ)/2}cos(θ/2)]]
# ---------------------------------------------------------------------------


def U(θ: float, φ: float, λ: float) -> np.ndarray:
    a = cmath.exp(-1j * (φ + λ) / 2) * math.cos(θ / 2)
    b = -cmath.exp(-1j * (φ - λ) / 2) * math.sin(θ / 2)
    c = cmath.exp(1j * (φ - λ) / 2) * math.sin(θ / 2)
    d = cmath.exp(1j * (φ + λ) / 2) * math.cos(θ / 2)
    return np.array([[a, b], [c, d]], dtype=complex)


def I() -> np.ndarray:
    return np.eye(2, dtype=complex)


def CX() -> np.ndarray:
    return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)


# 常数
PI = math.pi
HALF = math.pi / 2
QUARTER = math.pi / 4

# 底层基元矩阵（qelib1.inc 展开后的最终形式）
_MATS = {
    "u1": lambda λ: U(0, 0, λ),
    "u2": lambda φ, λ: U(HALF, φ, λ),
    "u3": lambda θ, φ, λ: U(θ, φ, λ),
    "h": U(HALF, 0, PI),                       # u2(0,pi)
    "x": U(PI, 0, PI),                          # u3(pi,0,pi)
    "y": U(PI, HALF, HALF),                     # u3(pi,pi/2,pi/2)
    "z": U(0, 0, PI),                           # u1(pi)
    "s": U(0, 0, HALF),                         # u1(pi/2)
    "sdg": U(0, 0, -HALF),                      # u1(-pi/2)
    "t": U(0, 0, QUARTER),                      # u1(pi/4)
    "tdg": U(0, 0, -QUARTER),                   # u1(-pi/4)
    "rx": lambda θ: U(θ, -HALF, HALF),          # u3(theta,-pi/2,pi/2)
    "ry": lambda θ: U(θ, 0, 0),                 # u3(theta,0,0)
    "rz": lambda φ: U(0, 0, φ),                 # u1(phi)
}


def _tensor(parts: List[np.ndarray]) -> np.ndarray:
    """张量积多个 2x2 矩阵（按量子比特顺序，q[0] 在最左）。"""
    result = parts[0]
    for p in parts[1:]:
        result = np.kron(result, p)
    return result


def _apply_single(gate: np.ndarray, target: int, n: int) -> np.ndarray:
    """单比特门作用于 target 比特，扩展为 2^n 维矩阵。"""
    parts = [I()] * n
    parts[target] = gate
    return _tensor(parts)


def _apply_cx(control: int, target: int, n: int) -> np.ndarray:
    """CNOT 门作用于 control/target，扩展为 2^n 维矩阵。"""
    # 逐行构造（小规模 n<=12 可承受）
    dim = 2 ** n
    M = np.zeros((dim, dim), dtype=complex)
    for i in range(dim):
        # 判断 control 位是否为 1
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
    # 形如 pi/2, pi/4, 3*pi/4, 0.5*pi 等
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
    """态矢量演化：|ψ⟩ = U_last ... U_1 |0⟩。返回 2^n 维复数向量。"""
    n = circuit.n
    if n > 14:
        raise ValueError(f"n={n} 超出态矢量模拟规模上限（14）")
    psi = np.zeros(2 ** n, dtype=complex)
    psi[0] = 1.0
    for name, qargs, vals in circuit.ops:
        if name == "barrier":
            # barrier 只是编译屏障，无量子语义，跳过
            continue
        if name in ("cx", "cx"):
            control, target = qargs
            psi = _apply_cx(control, target, n) @ psi
        elif name == "swap":
            a, b = qargs
            for c, t in ((a, b), (b, a), (a, b)):
                psi = _apply_cx(c, t, n) @ psi
        elif name == "ccx":
            a, b, c = qargs
            # Toffoli 按 qelib1.inc 分解：
            #   h c; cx b,c; tdg c; cx a,c; t c; cx b,c; tdg c; cx a,c;
            #   t b; t c; h c; cx a,b; t a; tdg b; cx a,b
            seq = [
                ("h", [c]), ("cx", [b, c]), ("tdg", [c]), ("cx", [a, c]),
                ("t", [c]), ("cx", [b, c]), ("tdg", [c]), ("cx", [a, c]),
                ("t", [b]), ("t", [c]), ("h", [c]), ("cx", [a, b]),
                ("t", [a]), ("tdg", [b]), ("cx", [a, b]),
            ]
            for g_name, g_args in seq:
                if g_name == "cx":
                    psi = _apply_cx(g_args[0], g_args[1], n) @ psi
                else:
                    psi = _apply_single(_MATS[g_name], g_args[0], n) @ psi
        elif name == "cu1":
            a, b = qargs
            λ = vals[0]
            # cu1(λ) = u1(λ/2) a; cx a,b; u1(-λ/2) b; cx a,b; u1(λ/2) b
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
            # i 的二进制（n 位，最左是 q[n-1]）→ 反转成 Qiskit 位序（最右 q[0]）
            bits = format(i, f"0{n}b")[::-1]
            dist[bits] = round(float(p), 12)
    return dist


def main() -> int:
    ap = argparse.ArgumentParser(description="QASM 2.0 语义模拟器（对齐尺子）")
    ap.add_argument("--qasm", required=True, help="QASM 2.0 文件路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()
    qasm = Path(args.qasm).read_text(encoding="utf-8")
    dist = reference_distribution(qasm)
    if args.json:
        print(json.dumps(dist, ensure_ascii=False, indent=2))
    else:
        for k, v in sorted(dist.items()):
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
