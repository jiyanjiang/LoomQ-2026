#!/usr/bin/env python3
"""LoomQ 电路库：21 个标准电路（代码生成，pip 包自包含）。

每个电路提供：
  - id: 用例 ID
  - name: 人类可读名
  - qasm(): 返回 OpenQASM 2.0 文本
  - kind: gate / algo
  - covers: 覆盖的 12 门白名单
  - description: 中文说明
"""

import math

HEADER = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n'


def _circuit(n: int, body: str) -> str:
    body = body.rstrip("\n") + "\n"
    return HEADER + f"qreg q[{n}];\ncreg c[{n}];\n" + body + "measure q -> c;\n"


# ---------------------------------------------------------------------------
# 逐门确定性电路（可手算）
# ---------------------------------------------------------------------------
GATE_CIRCUITS = {
    "g01_x": {"n": 1, "body": "x q[0];", "desc": "X 门：|0>→|1> 确定性翻转"},
    "g02_h": {"n": 1, "body": "h q[0];", "desc": "H 门：50/50 叠加"},
    "g03_s": {"n": 1, "body": "s q[0];", "desc": "S 相位门（|0> 上分布不变）"},
    "g04_sdg": {"n": 1, "body": "sdg q[0];", "desc": "S† 相位门"},
    "g05_t": {"n": 1, "body": "t q[0];", "desc": "T 相位门"},
    "g06_tdg": {"n": 1, "body": "tdg q[0];", "desc": "T† 相位门"},
    "g07_rz": {"n": 1, "body": "rz(0.5) q[0];", "desc": "RZ 旋转门"},
    "g08_ry": {"n": 1, "body": "ry(pi/2) q[0];", "desc": "RY(π/2)：50/50"},
    "g09_cx": {"n": 2, "body": "h q[0];\ncx q[0], q[1];", "desc": "CNOT：Bell 态"},
    "g10_cu1": {"n": 2, "body": "x q[0];\ncu1(0.5) q[0], q[1];", "desc": "受控相位"},
    "g11_swap": {"n": 2, "body": "x q[0];\nswap q[0], q[1];", "desc": "SWAP 交换"},
    "g12_ccx": {"n": 3, "body": "x q[0];\nx q[1];\nccx q[0], q[1], q[2];", "desc": "Toffoli"},
}

# ---------------------------------------------------------------------------
# 算法电路
# ---------------------------------------------------------------------------
ALGO_CIRCUITS = {
    "a01_ghz3": {"desc": "3 比特 GHZ 态 (|000>+|111>)/√2"},
    "a02_cat4": {"desc": "4 比特猫态 GHZ（QASMBench）"},
    "a03_qft4": {"desc": "4 比特量子傅里叶变换（QASMBench）"},
    "a04_grover2": {"desc": "2 比特 Grover 搜索（QASMBench）"},
    "a05_teleport3": {"desc": "3 比特量子隐形传态（QASMBench）"},
    "a06_qft5": {"desc": "5 比特 QFT（均匀 32 态）"},
    "a07_grover3": {"desc": "3 比特 Grover 目标|100> 约 78%"},
    "a08_toffoli3": {"desc": "3 比特 Toffoli 确定性"},
    "a09_wstate3": {"desc": "3 比特 W 态 (001+010+100)/√3"},
    "a10_ghz5": {"desc": "5 比特 GHZ 态 (00000+11111)/√2（评测核心）"},
}


def _qft_qasm(n: int) -> str:
    lines = [HEADER, f"qreg q[{n}];", f"creg c[{n}];"]
    for i in range(0, n, 2):
        lines.append(f"x q[{i}];")
    for i in range(n):
        lines.append(f"h q[{i}];")
        for j in range(i + 1, n):
            lines.append(f"cu1(pi/{2 ** (j - i + 1)}) q[{j}], q[{i}];")
    for i in range(n // 2):
        lines.append(f"swap q[{i}], q[{n - 1 - i}];")
    lines.append("measure q -> c;")
    return "\n".join(lines) + "\n"


def _grover3_qasm() -> str:
    return (HEADER + "qreg q[3];\ncreg c[3];\n"
            "h q[0];\nh q[1];\nh q[2];\n"
            "x q[0];\nx q[1];\nh q[2];\n"
            "ccx q[0], q[1], q[2];\n"
            "h q[2];\nx q[0];\nx q[1];\n"
            "h q[0];\nh q[1];\nh q[2];\n"
            "x q[0];\nx q[1];\nx q[2];\n"
            "h q[2];\nccx q[0], q[1], q[2];\nh q[2];\n"
            "x q[0];\nx q[1];\nx q[2];\n"
            "h q[0];\nh q[1];\nh q[2];\n"
            "measure q -> c;\n")


def _cat4_qasm() -> str:
    return (HEADER + "qreg bits[4];\ncreg c[4];\n"
            "h bits[0];\ncx bits[0],bits[1];\ncx bits[1],bits[2];\ncx bits[2],bits[3];\n"
            "measure bits[0] -> c[0];\nmeasure bits[1] -> c[1];\n"
            "measure bits[2] -> c[2];\nmeasure bits[3] -> c[3];\n")


def _grover2_qasm() -> str:
    return (HEADER + "qreg q[2];\ncreg c[2];\n"
            "h q[0];\nh q[1];\n"
            "h q[1];\ncx q[0],q[1];\nh q[1];\n"
            "h q[0];\nh q[1];\nx q[0];\nx q[1];\nh q[1];\ncx q[0],q[1];\nh q[1];\nx q[0];\nx q[1];\n"
            "h q[0];\nh q[1];\n"
            "measure q[0] -> c[0];\nmeasure q[1] -> c[1];\n")


def _teleport3_qasm() -> str:
    return (HEADER + "qreg q[3];\ncreg c[3];\n"
            "h q[0];\nt q[0];\nh q[0];\nh q[2];\ns q[0];\ncx q[2],q[1];\ncx q[0],q[1];\nh q[0];\n"
            "measure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];\n")


def _wstate3_qasm() -> str:
    th = 2 * math.acos(1 / math.sqrt(3))
    return (HEADER + "qreg q[3];\ncreg c[3];\n"
            f"ry({th}) q[0];\n"
            "ry(pi/4) q[1];\ncx q[0], q[1];\nry(-pi/4) q[1];\n"
            "cx q[1], q[2];\ncx q[0], q[1];\nx q[0];\n"
            "measure q -> c;\n")


def _toffoli3_qasm() -> str:
    return (HEADER + "qreg q[3];\ncreg c[3];\n"
            "x q[0];\nx q[1];\nccx q[0], q[1], q[2];\nmeasure q -> c;\n")


def _ghz5_qasm() -> str:
    """5 比特 GHZ 态 (|00000>+|11111>)/√2（QUANTUM_101 评测核心算法之一）。"""
    return (HEADER + "qreg q[5];\ncreg c[5];\n"
            "h q[0];\ncx q[0], q[1];\ncx q[1], q[2];\ncx q[2], q[3];\ncx q[3], q[4];\n"
            "measure q -> c;\n")


# id -> qasm 生成器
_ALGO_BUILDERS = {
    "a01_ghz3": lambda: _circuit(3, "h q[0];\ncx q[0], q[1];\ncx q[1], q[2];"),
    "a02_cat4": _cat4_qasm,
    "a03_qft4": lambda: _qft_qasm(4),
    "a04_grover2": _grover2_qasm,
    "a05_teleport3": _teleport3_qasm,
    "a06_qft5": lambda: _qft_qasm(5),
    "a07_grover3": _grover3_qasm,
    "a08_toffoli3": _toffoli3_qasm,
    "a09_wstate3": _wstate3_qasm,
    "a10_ghz5": _ghz5_qasm,
}

# 覆盖门（供覆盖度统计）
COVERS = {
    "g01_x": ["x"], "g02_h": ["h"], "g03_s": ["s"], "g04_sdg": ["sdg"],
    "g05_t": ["t"], "g06_tdg": ["tdg"], "g07_rz": ["rz"], "g08_ry": ["ry"],
    "g09_cx": ["cx"], "g10_cu1": ["cu1"], "g11_swap": ["swap"], "g12_ccx": ["ccx"],
    "a01_ghz3": ["h", "cx"], "a02_cat4": ["h", "cx"],
    "a03_qft4": ["h", "x", "cu1"], "a04_grover2": ["h", "x", "cx"],
    "a05_teleport3": ["h", "t", "s", "cx"],
    "a06_qft5": ["h", "x", "cu1", "swap"], "a07_grover3": ["h", "x", "ccx"],
    "a08_toffoli3": ["x", "ccx"], "a09_wstate3": ["ry", "x", "cx"],
    "a10_ghz5": ["h", "cx"],
}

ALL_IDS = tuple(GATE_CIRCUITS) + tuple(ALGO_CIRCUITS)


def get_qasm(circuit_id: str) -> str:
    """返回指定电路 ID 的 OpenQASM 2.0 文本。"""
    if circuit_id in GATE_CIRCUITS:
        meta = GATE_CIRCUITS[circuit_id]
        return _circuit(meta["n"], meta["body"])
    if circuit_id in _ALGO_BUILDERS:
        return _ALGO_BUILDERS[circuit_id]()
    raise KeyError(f"未知电路: {circuit_id}")


def get_info(circuit_id: str) -> dict:
    """返回电路元数据。"""
    if circuit_id in GATE_CIRCUITS:
        m = GATE_CIRCUITS[circuit_id]
        return {"id": circuit_id, "kind": "gate", "n": m["n"],
                "description": m["desc"], "covers": COVERS[circuit_id]}
    if circuit_id in ALGO_CIRCUITS:
        return {"id": circuit_id, "kind": "algo",
                "description": ALGO_CIRCUITS[circuit_id]["desc"], "covers": COVERS[circuit_id]}
    raise KeyError(f"未知电路: {circuit_id}")


def list_circuits() -> list:
    """列出全部电路元数据。"""
    return [get_info(cid) for cid in ALL_IDS]
