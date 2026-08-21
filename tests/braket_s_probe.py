#!/usr/bin/env python3
"""braket s/t 门错误级别判别探针（第 0-3 层）。

分层：
  第0层 对照：用已验证门（h/x/rz/cx）跑同样模板，确认装置可靠
  第1层 判别：P1 h s h / P2 h s s h / P3 h s s s s h —— s 是否恒等
  第2层 相位角：P4 h s h 精确分布 / P5 x h s h
  第3层 确认：P6 h rz h / P7 h u1 h / P8 h sdg sdg h / P9 h t t t t h

用法：source ~/.venvs/loomq310/bin/activate && python tests/braket_s_probe.py
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

SHOTS = 16384

# 探针定义: id -> (qubits, body, 预期分布来源注释)
PROBES = [
    # ---- 第 0 层：对照（已验证门） ----
    ("ctrl_h", 1, "h q[0];", "对照:h"),
    ("ctrl_x", 1, "x q[0];", "对照:x"),
    ("ctrl_rz", 1, "h q[0];\nrz(pi/2) q[0];\nh q[0];", "对照:h rz(pi/2) h"),
    ("ctrl_cx", 2, "h q[0];\ncx q[0], q[1];", "对照:bell"),
    # ---- 第 1 层：判别 s 是否恒等 ----
    ("P1_h_s_h", 1, "h q[0];\ns q[0];\nh q[0];", "P1:s 有效则50/50,恒等则100/0"),
    ("P2_h_s_s_h", 1, "h q[0];\ns q[0];\ns q[0];\nh q[0];", "P2:s²=Z→|1⟩100%,恒等→|0⟩100%"),
    ("P3_h_s4_h", 1, "h q[0];\ns q[0];\ns q[0];\ns q[0];\ns q[0];\nh q[0];", "P3:s⁴=I→|0⟩(若s²=Z)"),
    # ---- 第 2 层：相位角 ----
    ("P4_x_h_s_h", 1, "x q[0];\nh q[0];\ns q[0];\nh q[0];", "P4:换输入态|1⟩"),
    ("P5_h_s_h_x", 1, "h q[0];\ns q[0];\nh q[0];\nx q[0];", "P5:h s h 后再 x"),
    # ---- 第 3 层：确认 ----
    ("P6_h_rz_h", 1, "h q[0];\nrz(pi/2) q[0];\nh q[0];", "P6:rz 对照(应OK)"),
    ("P7_h_u1_h", 1, "h q[0];\nu1(pi/2) q[0];\nh q[0];", "P7:u1 是否可用"),
    ("P8_h_sdg_sdg_h", 1, "h q[0];\nsdg q[0];\nsdg q[0];\nh q[0];", "P8:sdg²=Z?"),
    ("P9_h_t4_h", 1, "h q[0];\nt q[0];\nt q[0];\nt q[0];\nt q[0];\nh q[0];", "P9:t⁴=Z→|1⟩,恒等→|0⟩"),
    # ---- 补充：sdg/t/tdg 的 P2 对应 ----
    ("P10_h_t_t_h", 1, "h q[0];\nt q[0];\nt q[0];\nh q[0];", "P10:t²=S→50/50,恒等→100/0"),
]


def qasm_for(n: int, body: str) -> str:
    return (f"OPENQASM 2.0;\ninclude \"qelib1.inc\";\n"
            f"qreg q[{n}];\ncreg c[{n}];\n{body}\nmeasure q -> c;\n")


def hellinger(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    d = math.sqrt(sum((math.sqrt(p.get(k, 0)) - math.sqrt(q.get(k, 0))) ** 2 for k in keys)) / math.sqrt(2)
    return max(0.0, min(1.0, 1.0 - d))


def main() -> int:
    report = {}
    for pid, n, body, note in PROBES:
        qasm = qasm_for(n, body)
        try:
            ref = reference_distribution(qasm)
        except Exception as e:
            ref = {"ERR": str(e)[:50]}
        row = {"note": note, "reference": ref}
        print(f"\n=== {pid}: {note} ===")
        print(f"  参考: {sorted(ref.items())}")
        for t in ("spinq", "originq", "braket"):
            try:
                r = adapter.run(qasm, t, SHOTS)
                total = sum(r["counts"].values())
                obs = {k: v / total for k, v in sorted(r["counts"].items(), key=lambda x: -x[1])}
                fid = hellinger(ref, obs)
                row[t] = {"fidelity": round(fid, 4), "counts": obs}
                print(f"  {t:8s} fid={fid:.4f} {obs}")
            except Exception as e:
                row[t] = {"error": str(e)[:80]}
                print(f"  {t:8s} ERR {str(e)[:80]}")
        report[pid] = row
    out = ROOT / "tests" / "braket_s_probe_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n探针报告已保存: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
