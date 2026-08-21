#!/usr/bin/env python3
"""生成逐门确定性测试电路（tests/circuits/g*.qasm）并验证手算期望分布。

期望分布验证方式：
  - 确定性电路（x/swap/ccx 等）用手算值
  - 相位/旋转门用 spinq 本地模拟器跑 8192 shots 确认
用法：source ~/.venvs/loomq310/bin/activate && python tests/gen_gate_circuits.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CIRC = Path(__file__).resolve().parent / "circuits"

HEADER = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n'


def circuit(name: str, n: int, body: str) -> str:
    qreg = ",".join(f"q[{i}]" for i in range(n))
    creg = ",".join(f"c[{i}]" for i in range(n))
    body = body.rstrip("\n") + "\n"
    return HEADER + f"qreg q[{n}];\ncreg c[{n}];\n" + body + f"measure q -> c;\n"


CIRCUITS = {
    # 覆盖门: 电路名 -> (qubits, 门行, 手算期望)
    "x_only": (1, "x q[0];", {"1": 1.0}),
    "h_only": (1, "h q[0];", {"0": 0.5, "1": 0.5}),
    "s_phase": (1, "s q[0];", {"0": 1.0}),
    "sdg_phase": (1, "sdg q[0];", {"0": 1.0}),
    "t_phase": (1, "t q[0];", {"0": 1.0}),
    "tdg_phase": (1, "tdg q[0];", {"0": 1.0}),
    "rz_param": (1, "rz(0.5) q[0];", {"0": 1.0}),
    "ry_param": (1, "ry(pi/2) q[0];", {"0": 0.5, "1": 0.5}),
    "cx_bell": (2, "h q[0];\ncx q[0], q[1];", {"00": 0.5, "11": 0.5}),
    "cu1_param": (2, "x q[0];\ncu1(0.5) q[0], q[1];", {"01": 1.0}),
    "swap_exchange": (2, "x q[0];\nswap q[0], q[1];", {"10": 1.0}),
    "ccx_toffoli": (3, "x q[0];\nx q[1];\nccx q[0], q[1], q[2];", {"111": 1.0}),
}


def run_spinq(qasm: str, shots: int = 8192) -> dict:
    import spinqit as sq
    from spinqit import BasicSimulatorConfig, get_basic_simulator, get_compiler
    with tempfile.NamedTemporaryFile(mode="w", suffix=".qasm", delete=False, encoding="utf-8") as f:
        f.write(qasm)
        path = f.name
    try:
        ir = get_compiler("qasm").compile(path, 0)
        engine = get_basic_simulator()
        cfg = BasicSimulatorConfig()
        cfg.configure_shots(shots)
        res = engine.execute(ir, cfg)
        return {str(k): v / shots for k, v in res.counts.items()}
    finally:
        os.unlink(path)


def main() -> int:
    os.makedirs(CIRC, exist_ok=True)
    report = {}
    for name, (n, body, hand) in CIRCUITS.items():
        qasm = circuit(name, n, body)
        (CIRC / f"{name}.qasm").write_text(qasm, encoding="utf-8")
        # 用 spinq 验证手算期望
        try:
            sim = run_spinq(qasm)
            report[name] = {"hand": hand, "spinq": sim}
            ok = all(abs(sim.get(k, 0) - v) < 0.02 for k, v in hand.items())
            print(f"{name:16s} {'OK ' if ok else 'MISMATCH'} hand={hand} spinq={sim}")
        except Exception as exc:
            report[name] = {"hand": hand, "error": str(exc)}
            print(f"{name:16s} ERROR {exc}")
    (Path(__file__).resolve().parent / "gate_circuits_verify.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
