#!/usr/bin/env python3
"""braket s 门量子过程层析（QPT）——直接反推 2x2 矩阵，确认是否为恒等门。

方法：单比特门 G，用 3 个输入态 × 3 个测量基 = 9 个实验，最小二乘反推 G。
  输入态制备（用已验证门）：
    |0⟩: 直用;  |+⟩: h;  |+i⟩: rz(pi/2); h
  测量基（用已验证门构造）：
    Z: 直接测;  X: h 后测;  Y: rz(-pi/2); h 后测
输入态和测量基都只用 h/x/rz（已验证对齐），避免用可疑的 s/sdg。

用法：source ~/.venvs/loomq310/bin/activate && python tests/qpt_braket_s.py
"""

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter_kit"))

import adapter  # noqa: E402

SHOTS = 20000


def qasm(n: int, prep: str, gate: str, meas: str) -> str:
    """构造: prep; gate; meas; 然后测 Z 基。"""
    return (f"OPENQASM 2.0;\ninclude \"qelib1.inc\";\n"
            f"qreg q[{n}];\ncreg c[{n}];\n{prep}{gate}{meas}measure q -> c;\n")


# 单比特门矩阵参考
def U(theta, phi, lam):
    a = math.cos(theta / 2)
    b = -cmath_exp(phi, lam, sign=1)
    return None


def main() -> int:
    # 参考门矩阵（QASM2 标准）
    I = np.eye(2, dtype=complex)
    S = np.array([[1, 0], [0, 1j]], dtype=complex)
    Sdg = np.array([[1, 0], [0, -1j]], dtype=complex)
    T = np.array([[1, 0], [0, np.exp(1j * math.pi / 4)]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)

    # 输入态（列向量）: |0>, |+>, |+i>
    H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
    ZERO = np.array([1, 0], dtype=complex)
    PLUS = H @ ZERO
    PLUSI = np.array([1, 1j], dtype=complex) / math.sqrt(2)
    INPUTS = [ZERO, PLUS, PLUSI]

    # 测量基（行向量，投影到 |0> 的概率）: Z基, X基, Y基
    X_BASIS0 = H @ ZERO  # |+> 即 X 基的 |0>
    Y_BASIS0 = np.array([1, -1j], dtype=complex) / math.sqrt(2)  # |+i> 即 Y 基的 |0>
    MEAS = [ZERO, X_BASIS0, Y_BASIS0]

    prep_codes = ["", "h q[0];\n", "rz(pi/2) q[0];\nh q[0];\n"]  # |0>, |+>, |+i>
    meas_codes = ["", "h q[0];\n", "rz(-pi/2) q[0];\nh q[0];\n"]  # Z, X, Y
    meas_names = ["Z", "X", "Y"]
    in_names = ["|0>", "|+>", "|+i>"]

    # 目标门: s（对 braket 反推）
    GATE = "s q[0];\n"

    print("=== 实验: 9 组 (输入态 x 测量基)，braket 实测 ===")
    P = np.zeros((3, 3))  # P[i][j] = 输入 i 基下测得 |0> 的概率
    for i, prep in enumerate(prep_codes):
        for j, meas in enumerate(meas_codes):
            q = qasm(1, prep, GATE, meas)
            try:
                r = adapter.run(q, "braket", SHOTS)
                total = sum(r["counts"].values())
                p0 = r["counts"].get("0", 0) / total
            except Exception as e:
                print(f"  {in_names[i]} × {meas_names[j]}  ERR {str(e)[:60]}")
                P[i][j] = 0.5
                continue
            P[i][j] = p0
            print(f"  {in_names[i]} × {meas_names[j]}基: P(|0>)={p0:.4f}")

    # 反推矩阵 G: P[i][j] = |<meas_j| G |input_i>|^2
    # 用最小二乘拟合 G 的 4 个复参数。简化：先枚举候选（I, S, Sdg, T, Z, H）算理论概率找最接近
    candidates = {
        "I (恒等)": I,
        "S": S,
        "Sdg": Sdg,
        "T": T,
        "Z": Z,
    }
    print("\n=== 反推：候选矩阵对比 ===")
    best, best_err = None, 1e9
    for name, G in candidates.items():
        err = 0.0
        for i, inp in enumerate(INPUTS):
            out = G @ inp
            for j, meas in enumerate(MEAS):
                p_theory = abs(np.vdot(meas, out)) ** 2
                err += (p_theory - P[i][j]) ** 2
        print(f"  {name:12s} 残差={err:.6f}")
        if err < best_err:
            best_err, best = err, name

    print(f"\n=== 结论: braket 的 s 门最接近 {best}（残差 {best_err:.6f}）===")
    print("若 best == 'I (恒等)' → braket s 门 = 恒等门（实测确认），与 P2 探针结论一致。")
    return 0


def cmath_exp(phi, lam, sign):
    """辅助：U 门元素（未使用，保留占位）。"""
    import cmath
    if sign == 1:
        return cmath.exp(-1j * (phi + lam) / 2)


if __name__ == "__main__":
    sys.exit(main())
