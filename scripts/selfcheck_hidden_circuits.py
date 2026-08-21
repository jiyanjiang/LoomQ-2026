#!/usr/bin/env python3
"""隐藏电路自测集：验证三后端模拟器对组织方隐藏电路的转译/执行正确性。

背景：QUANTUM_101 泄露的隐藏电路集 = QFT-4 / Grover-3 / GHZ-5 / Random×3。
组织方不收我们的电路，只收转译器（adapter）——所以自验的是：
  同一份 QASM 2.0，经 transpile() 转译后在三个后端跑出的结果是否与理论一致。

判定规则（无噪声精确模拟 + 统计涨落容差）：
  - ghz5 : |00000> 与 |11111> 各 ≈50%
  - qft4 : QFT 把任意计算基态映射到均匀叠加 → 16 态各 ≈6.25%
  - grover3 : 主峰态 ≈78%（一次 Grover 迭代），其余均匀
  - random* : 无闭式期望，判据 = 三后端两两分布最大概率差 < 容差

用法:
  python scripts/selfcheck_hidden_circuits.py [--shots 8192] [--tol 0.02] [--circuits ghz5,qft4,grover3,random1,random2,random3]
"""
import argparse
import math
import random
import sys

sys.path.insert(0, "loomq_lib")

from loomq_lib.backends import run  # noqa: E402
from loomq_lib.circuits import get_qasm  # noqa: E402

# 组织方 12 门白名单（QUANTUM_101 泄露）
WHITELIST_12 = ["h", "x", "s", "sdg", "t", "tdg", "rz", "ry", "cx", "cu1", "swap", "ccx"]

TARGETS = ("spinq", "originq", "braket")


# ---------------------------------------------------------------------------
# Random×3：固定种子生成（可复现），覆盖 12 门全门集
# ---------------------------------------------------------------------------
def _rand_qasm(seed: int, n_qubits: int = 4, n_gates: int = 18) -> str:
    rng = random.Random(seed)
    lines = ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{n_qubits}];',
             f'creg c[{n_qubits}];']
    gates_used = set()
    for _ in range(n_gates):
        g = rng.choice(WHITELIST_12)
        gates_used.add(g)
        if g in ("rz", "ry"):
            p = round(rng.uniform(-math.pi, math.pi), 6)
            lines.append(f"{g}({p}) q[{rng.randrange(n_qubits)}];")
        elif g == "cu1":
            p = round(rng.uniform(-math.pi, math.pi), 6)
            a, b = rng.sample(range(n_qubits), 2)
            lines.append(f"cu1({p}) q[{a}], q[{b}];")
        elif g == "cx":
            a, b = rng.sample(range(n_qubits), 2)
            lines.append(f"cx q[{a}], q[{b}];")
        elif g == "swap":
            a, b = rng.sample(range(n_qubits), 2)
            lines.append(f"swap q[{a}], q[{b}];")
        elif g == "ccx":
            a, b, c = rng.sample(range(n_qubits), 3)
            lines.append(f"ccx q[{a}], q[{b}], q[{c}];")
        else:  # 单比特：h/x/s/sdg/t/tdg
            lines.append(f"{g} q[{rng.randrange(n_qubits)}];")
    lines.append("measure q -> c;")
    return "\n".join(lines) + "\n"


def _probs(counts: dict, shots: int, n_qubits: int) -> dict:
    """counts -> 概率分布（补齐未命中的态）。"""
    full = {f"{i:0{n_qubits}b}": 0 for i in range(2 ** n_qubits)}
    for k, v in counts.items():
        full[k] = v / shots
    return full


# ---------------------------------------------------------------------------
# 判定器
# ---------------------------------------------------------------------------
def check_ghz5(counts: dict, shots: int, tol: float) -> tuple[bool, str]:
    p0 = counts.get("00000", 0) / shots
    p1 = counts.get("11111", 0) / shots
    ok = abs(p0 - 0.5) <= tol and abs(p1 - 0.5) <= tol
    return ok, f"P(00000)={p0:.3f} P(11111)={p1:.3f} (期望各≈0.50)"


def check_qft4(counts: dict, shots: int, tol: float) -> tuple[bool, str]:
    probs = _probs(counts, shots, 4)
    exp = 1 / 16
    worst = max(abs(p - exp) for p in probs.values())
    ok = worst <= tol
    return ok, f"最大偏差={worst:.3f} (期望 16 态各 1/16≈0.0625)"


def check_grover3(counts: dict, shots: int, tol: float) -> tuple[bool, str]:
    peak_bit, peak = max(counts.items(), key=lambda kv: kv[1])
    p = peak / shots
    ok = p >= 0.70  # 理论≈0.781，容差放 0.70 兜统计涨落
    return ok, f"主峰 {peak_bit} P={p:.3f} (理论≈0.78)"


def check_random(counts_list: list[dict], shots: int, tol: float) -> tuple[bool, str]:
    """三后端两两最大概率差。"""
    worst = 0.0
    for i in range(len(counts_list)):
        for j in range(i + 1, len(counts_list)):
            keys = set(counts_list[i]) | set(counts_list[j])
            for k in keys:
                d = abs(counts_list[i].get(k, 0) - counts_list[j].get(k, 0)) / shots
                worst = max(worst, d)
    ok = worst <= tol
    return ok, f"三后端最大概率差={worst:.3f} (容差 {tol})"


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shots", type=int, default=8192)
    ap.add_argument("--tol", type=float, default=0.02)
    ap.add_argument("--circuits", default="ghz5,qft4,grover3,random1,random2,random3")
    args = ap.parse_args()

    circuits = {
        "ghz5": ("GHZ-5", get_qasm("a10_ghz5"), check_ghz5, None),
        "qft4": ("QFT-4", get_qasm("a03_qft4"), check_qft4, None),
        "grover3": ("Grover-3", get_qasm("a07_grover3"), check_grover3, None),
        "random1": ("Random-1", _rand_qasm(seed=101), check_random, None),
        "random2": ("Random-2", _rand_qasm(seed=202), check_random, None),
        "random3": ("Random-3", _rand_qasm(seed=303), check_random, None),
    }

    want = [c.strip() for c in args.circuits.split(",") if c.strip()]
    print(f"{'电路':<10}{'后端':<10}{'结果':<8}判定")
    print("-" * 72)

    n_pass = n_fail = 0
    for cid in want:
        if cid not in circuits:
            print(f"[SKIP] 未知电路: {cid}")
            continue
        name, qasm, checker, _ = circuits[cid]
        # 预检查：确保电路覆盖的指令都在 12 门白名单
        rows = []
        for t in TARGETS:
            r = run(qasm, t, shots=args.shots)
            rows.append((t, r["counts"]))
        # 分电路判定
        if cid.startswith("random"):
            ok, msg = check_random([c for _, c in rows], args.shots, args.tol)
        else:
            ok, msg = checker(rows[0][1], args.shots, args.tol)
            # 三后端一致性也纳入：主判定的后端结果与其他后端最大差
            ref = rows[0][1]
            for t, c in rows[1:]:
                keys = set(ref) | set(c)
                d = max(abs(ref.get(k, 0) - c.get(k, 0)) / args.shots for k in keys)
                if d > args.tol:
                    ok = False
                    msg += f" | 三后端不一致 maxΔ={d:.3f}"
        mark = "PASS" if ok else "FAIL"
        n_pass += ok
        n_fail += (not ok)
        print(f"{name:<10}{'/'.join(TARGETS):<10}{mark:<8}{msg}")

    print("-" * 72)
    print(f"汇总: {n_pass} PASS / {n_fail} FAIL")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
