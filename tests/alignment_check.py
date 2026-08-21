#!/usr/bin/env python3
"""用"尺子"（qasm_semantics.py）实测三后端 12 门组合的对齐度。

探针设计：单门在 |0⟩ 上测量分布不变（相位不显形），必须用相位敏感组合：
  - s/sdg/t/tdg/rz：H 夹门（h; gate; h），相位在 X 基下显形
  - ry：直接 ry(θ)（旋转改变分布）
  - cu1：受控组合（x; cu1; h 等）
  - cx/swap/ccx：确定性组合
每格输出 参考分布 vs 后端分布 的 Hellinger 保真度（≥0.97 视为对齐）。

用法：source ~/.venvs/loomq310/bin/activate && python tests/alignment_check.py
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter_kit"))
sys.path.insert(0, str(ROOT / "tests"))

import adapter  # noqa: E402
from qasm_semantics import reference_distribution  # noqa: E402

PROBES = {
    # 门: (qubits, 电路 body, 说明)
    "h": (1, "h q[0];", "h 直接测"),
    "x": (1, "x q[0];", "x 直接测"),
    "s": (1, "h q[0];\ns q[0];\nh q[0];", "H 夹 S（相位敏感）"),
    "sdg": (1, "h q[0];\nsdg q[0];\nh q[0];", "H 夹 SDG"),
    "t": (1, "h q[0];\nt q[0];\nh q[0];", "H 夹 T"),
    "tdg": (1, "h q[0];\ntdg q[0];\nh q[0];", "H 夹 TDG"),
    "rz": (1, "h q[0];\nrz(pi/2) q[0];\nh q[0];", "H 夹 RZ(π/2)"),
    "ry": (1, "ry(pi/2) q[0];", "RY(π/2) 直接测"),
    "cx": (2, "h q[0];\ncx q[0], q[1];", "Bell 态"),
    "cu1": (2, "x q[0];\nh q[1];\ncu1(pi/2) q[0], q[1];", "受控相位组合"),
    "swap": (2, "x q[0];\nswap q[0], q[1];", "确定性交换"),
    "ccx": (3, "x q[0];\nx q[1];\nccx q[0], q[1], q[2];", "Toffoli"),
}


def hellinger(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    d = math.sqrt(sum((math.sqrt(p.get(k, 0)) - math.sqrt(q.get(k, 0))) ** 2 for k in keys)) / math.sqrt(2)
    return max(0.0, min(1.0, 1.0 - d))


def qasm_for(n: int, body: str) -> str:
    return (f"OPENQASM 2.0;\ninclude \"qelib1.inc\";\n"
            f"qreg q[{n}];\ncreg c[{n}];\n{body}\nmeasure q -> c;\n")


def main() -> int:
    report = {}
    print(f"{'门':6s} {'参考分布':30s} | {'spinq':20s} {'originq':20s} {'braket':20s}")
    for gate, (n, body, note) in PROBES.items():
        qasm = qasm_for(n, body)
        ref = reference_distribution(qasm)
        row = {"reference": ref, "note": note}
        line = f"{gate:6s} {str(sorted(ref.items()))[:28]:30s} |"
        for t in ("spinq", "originq", "braket"):
            try:
                r = adapter.run(qasm, t, 8192)
                total = sum(r["counts"].values())
                obs = {k: v / total for k, v in r["counts"].items()}
                fid = hellinger(ref, obs)
                row[t] = {"fidelity": round(fid, 4), "counts": obs}
                mark = "OK " if fid >= 0.97 else "BAD"
                line += f" {t}:{mark}{fid:.3f}"
            except Exception as e:
                row[t] = {"error": str(e)[:60]}
                line += f" {t}:ERR"
        report[gate] = row
        print(line)
    out = ROOT / "tests" / "alignment_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已保存: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
