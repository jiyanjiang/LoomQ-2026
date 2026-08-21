#!/usr/bin/env python3
"""originq transpile 校验器 —— 用"尺子"反验 OriginIR 输出。

思路：originq 的 transpile 输出 OriginIR 文本（契约门名 SDAG/TDAG/CU1 等），
本地 pyqpanda 解析器不认这些门名（已实测）。因此不用 pyqpanda，而是扩展
qasm_semantics.py 让它直接解析 OriginIR 方言，算出精确参考分布，与
同一电路源 QASM 的参考分布比对（Hellinger ≥ 0.97 即翻译正确）。

OriginIR 方言（target_ir_contract.md）：
  QINIT n / CREG n
  门: H X S SDAG T TDAG RY RZ CNOT CU1/CR SWAP TOFFOLI/CCX
  参数门: RY q[k],(θ) 或 RY(θ) q[k] 两种格式
  测量: MEASURE q[i], c[i]

用法：source ~/.venvs/loomq310/bin/activate && python tests/originir_verifier.py
"""

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter_kit"))
sys.path.insert(0, str(ROOT / "tests"))

import adapter  # noqa: E402
from qasm_semantics import _MATS, _apply_cx, _apply_single, _parse_number, evolve, Circuit  # noqa: E402

# OriginIR 门名 -> 标准门（用于矩阵查找）
_ORIGINIR_TO_STD = {
    "H": "h", "X": "x", "S": "s", "T": "t",
    "SDAG": "sdg", "TDAG": "tdg",
    "RY": "ry", "RZ": "rz",
    "CNOT": "cx", "SWAP": "swap",
    "TOFFOLI": "ccx", "CCX": "ccx",
    "CR": "cu1", "CU1": "cu1",
}


class OriginIRCircuit:
    """解析 OriginIR 为 (n, ops)，复用 qasm_semantics 的门矩阵。"""

    def __init__(self, originir: str):
        self.n = 0
        self.ops = []
        self._parse(originir)

    def _parse(self, text: str):
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            m = re_match(r"^QINIT\s+(\d+)$", line)
            if m:
                self.n = int(m.group(1))
                continue
            m = re_match(r"^CREG\s+(\d+)$", line)
            if m:
                continue
            m = re_match(r"^MEASURE\s+(\w+)\[(\d+)\],\s*(\w+)\[(\d+)\]$", line)
            if m:
                continue  # 测量不改变态，跳过
            # 参数门: CU1 q[0], q[1],(0.5)（多比特）或 RZ q[0],(0.5)（单比特）或 RY(0.5) q[0]
            m = re_match(r"^(\w+)\s+((?:q\[\d+\],\s*)+)\(([^)]+)\)$", line)
            if m:
                name, qs_part, params = m.group(1), m.group(2), m.group(3)
                qs = [int(x) for x in re_findall(r"\[(\d+)\]", qs_part)]
                self.ops.append((name, qs, [_parse_number(params)]))
                continue
            m = re_match(r"^(\w+)\s*\(([^)]+)\)\s+q\[(\d+)\]$", line)
            if m:
                name, params, q = m.group(1), m.group(2), int(m.group(3))
                self.ops.append((name, [q], [_parse_number(params)]))
                continue
            # 多比特门: CNOT q[0], q[1] / SWAP q[0], q[1] / TOFFOLI q[0], q[1], q[2]
            m = re_match(r"^(\w+)\s+(.+)$", line)
            if m:
                name, rest = m.group(1), m.group(2)
                qs = [int(x) for x in re_findall(r"\[(\d+)\]", rest)]
                self.ops.append((name, qs, []))
                continue
            raise ValueError(f"无法解析 OriginIR 行: {line!r}")


def re_match(p, s):
    import re
    return re.match(p, s)


def re_findall(p, s):
    import re
    return re.findall(p, s)


def originir_reference(originir: str) -> dict:
    """解析 OriginIR 并计算精确参考分布（key 最右 = c[0]）。"""
    c = OriginIRCircuit(originir)
    if c.n > 14:
        raise ValueError("n 超限")
    psi = np.zeros(2 ** c.n, dtype=complex)
    psi[0] = 1.0
    for name, qargs, vals in c.ops:
        std = _ORIGINIR_TO_STD.get(name)
        if std is None:
            raise ValueError(f"未知 OriginIR 门: {name}")
        if std == "cx":
            psi = _apply_cx(qargs[0], qargs[1], c.n) @ psi
        elif std == "swap":
            a, b = qargs
            for x, y in ((a, b), (b, a), (a, b)):
                psi = _apply_cx(x, y, c.n) @ psi
        elif std == "ccx":
            # Toffoli 分解（qelib1.inc）
            a, b, cc = qargs
            seq = [("h", [cc]), ("cx", [b, cc]), ("tdg", [cc]), ("cx", [a, cc]),
                   ("t", [cc]), ("cx", [b, cc]), ("tdg", [cc]), ("cx", [a, cc]),
                   ("t", [b]), ("t", [cc]), ("h", [cc]), ("cx", [a, b]),
                   ("t", [a]), ("tdg", [b]), ("cx", [a, b])]
            for g, gq in seq:
                if g == "cx":
                    psi = _apply_cx(gq[0], gq[1], c.n) @ psi
                else:
                    psi = _apply_single(_MATS[g], gq[0], c.n) @ psi
        elif std == "cu1":
            a, b = qargs
            lam = vals[0]
            psi = _apply_single(_MATS["u1"](lam / 2), a, c.n) @ psi
            psi = _apply_cx(a, b, c.n) @ psi
            psi = _apply_single(_MATS["u1"](-lam / 2), b, c.n) @ psi
            psi = _apply_cx(a, b, c.n) @ psi
            psi = _apply_single(_MATS["u1"](lam / 2), b, c.n) @ psi
        else:
            psi = _apply_single(_MATS[std] if not vals else _MATS[std](*vals), qargs[0], c.n) @ psi
    probs = np.abs(psi) ** 2
    dist = {}
    for i, p in enumerate(probs):
        if p > 1e-12:
            bits = format(i, f"0{c.n}b")[::-1]
            dist[bits] = round(float(p), 12)
    return dist


def hellinger(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    d = math.sqrt(sum((math.sqrt(p.get(k, 0)) - math.sqrt(q.get(k, 0))) ** 2 for k in keys)) / math.sqrt(2)
    return max(0.0, min(1.0, 1.0 - d))


def main() -> int:
    circuits = ["x_only", "h_only", "s_phase", "sdg_phase", "t_phase", "tdg_phase",
                "rz_param", "ry_param", "cx_bell", "cu1_param", "swap_exchange", "ccx_toffoli",
                "bell", "ghz3", "qft_n4", "grover_n2", "cat_state_n4", "teleportation_n3"]
    base = ROOT / "tests" / "circuits"
    pass_cnt = fail_cnt = 0
    print(f"{'电路':20s} {'源QASM参考':16s} {'OriginIR参考':16s} {'Hellinger':10s} 结果")
    for name in circuits:
        path = base / f"{name}.qasm"
        if not path.exists():
            path = ROOT / "starter_kit" / "circuits" / f"{name}.qasm"
        if not path.exists():
            print(f"{name:20s} 缺文件，跳过")
            continue
        qasm = path.read_text(encoding="utf-8")
        ref_qasm = originir_verifier_source_ref(qasm)
        originir = adapter.transpile(qasm, "originq")
        try:
            ref_originir = originir_reference(originir)
            fid = hellinger(ref_qasm, ref_originir)
            ok = fid >= 0.97
            pass_cnt += ok
            fail_cnt += (not ok)
            print(f"{name:20s} {str(sorted(ref_qasm.items())[:1]):16s} {str(sorted(ref_originir.items())[:1]):16s} {fid:.4f}     {'PASS' if ok else 'FAIL'}")
        except Exception as e:
            fail_cnt += 1
            print(f"{name:20s} ERR: {str(e)[:60]}")
    print(f"\n汇总: PASS={pass_cnt} FAIL={fail_cnt}")
    return 0 if fail_cnt == 0 else 1


def originir_verifier_source_ref(qasm: str) -> dict:
    """源 QASM 参考分布（复用 qasm_semantics）。"""
    from qasm_semantics import reference_distribution
    return reference_distribution(qasm)


if __name__ == "__main__":
    sys.exit(main())
