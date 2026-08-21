#!/usr/bin/env python3
"""LoomQ 三后端执行封装：run(qasm, target) 与 transpile(qasm, target)。

从 starter_kit/adapter.py 移植核心逻辑（含位序归一化、braket s/t→rz 展开、
transpile/run 双模式分离），独立成 pip 包模块。
"""

import os
import re
import tempfile
import time
import uuid
from typing import Any, Dict, List, Tuple

SUPPORTED_TARGETS = ("spinq", "originq", "braket")

# ---------------------------------------------------------------------------
# transpile：QASM 2.0 -> 目标后端原生表示（契约模式）
# ---------------------------------------------------------------------------

_ORIGINIR_GATE_MAP = {
    "h": "H", "x": "X", "s": "S", "t": "T",
    "sdg": "SDAG", "tdg": "TDAG",
    "cx": "CNOT", "swap": "SWAP",
    "ccx": "TOFFOLI", "toffoli": "TOFFOLI",
}

_BRAKET_GATES_INC = None


def _braket_gates_inc_path() -> str:
    global _BRAKET_GATES_INC
    if _BRAKET_GATES_INC is None:
        import braket.default_simulator as _bds
        _BRAKET_GATES_INC = os.path.join(
            os.path.dirname(os.path.abspath(_bds.__file__)),
            "openqasm", "braket_gates.inc",
        )
    return _BRAKET_GATES_INC


def _extract_qlist(qubits: str) -> List[str]:
    parts = re.findall(r"\w+\[\d+\]", qubits)
    if parts:
        return [re.sub(r"^\w+\[", "q[", p) for p in parts]
    return [qubits.strip()]


def _originir_gate(name: str, params: str | None, qlist: list[str]) -> str:
    gname = _ORIGINIR_GATE_MAP.get(name, name.upper())
    if params is not None:
        if len(qlist) > 1:
            return f"{gname} {', '.join(qlist)},({params})"
        return f"{gname} {qlist[0]},({params})"
    return f"{gname} {', '.join(qlist)}"


def _qasm2_to_originir(qasm2: str) -> str:
    n_qubits = 0
    n_bits = 0
    gates = []
    code = re.sub(r"//.*$", "", qasm2, flags=re.MULTILINE)
    for line in code.replace(";", ";\n").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("OPENQASM") or line.startswith("include"):
            continue
        m = re.match(r"qreg\s+(\w+)\s*\[\s*(\d+)\s*\]", line)
        if m:
            n_qubits = int(m.group(2))
            continue
        m = re.match(r"creg\s+(\w+)\s*\[\s*(\d+)\s*\]", line)
        if m:
            n_bits = int(m.group(2))
            continue
        m = re.match(r"measure\s+(\w+)\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]", line)
        if m:
            gates.append(f"MEASURE q[{m.group(2)}], c[{m.group(4)}]")
            continue
        m = re.match(r"measure\s+(\w+)\s*->\s*(\w+)", line)
        if m:
            for i in range(n_bits):
                gates.append(f"MEASURE q[{i}], c[{i}]")
            continue
        if line.startswith("barrier"):
            continue
        m = re.match(r"(\w+)\s*\(([^)]*)\)\s*(.*)", line)
        if m:
            name, params, qubits = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            qlist = _extract_qlist(qubits)
            gates.append(_originir_gate(name, params, qlist))
            continue
        m = re.match(r"(\w+)\s*(.*)", line)
        if m:
            name, qubits = m.group(1).strip(), m.group(2).strip()
            qlist = _extract_qlist(qubits)
            gates.append(_originir_gate(name, None, qlist))
    out = [f"QINIT {n_qubits}", f"CREG {n_bits}"]
    out.extend(gates)
    return "\n".join(out) + "\n"


def _qasm2_to_qasm3(qasm2: str, local: bool = False) -> str:
    qasm2 = qasm2.strip()
    stmts = []
    n_qubits = 0
    n_bits = 0
    qreg_name = "q"
    creg_name = "c"
    code = re.sub(r"//.*$", "", qasm2, flags=re.MULTILINE)
    for chunk in code.replace(";", ";\n").splitlines():
        line = chunk.strip()
        if not line:
            continue
        if line.startswith("OPENQASM"):
            continue
        if line.startswith("include"):
            continue
        if re.match(r"qreg\s+", line):
            m = re.match(r"qreg\s+(\w+)\s*\[\s*(\d+)\s*\]", line)
            if m:
                qreg_name = m.group(1)
                n_qubits = int(m.group(2))
            continue
        if re.match(r"creg\s+", line):
            m = re.match(r"creg\s+(\w+)\s*\[\s*(\d+)\s*\]", line)
            if m:
                creg_name = m.group(1)
                n_bits = int(m.group(2))
            continue
        if line.startswith("measure"):
            continue
        stmts.append(line)
    body = "\n".join(stmts).strip()
    if qreg_name != "q":
        body = re.sub(rf"\b{qreg_name}\s*\[", "q[", body)
    if creg_name != "c":
        body = re.sub(rf"\b{creg_name}\s*\[", "c[", body)
    if local:
        gate_map = {"cx": "cnot", "cu1": "cphaseshift", "ccx": "ccnot", "toffoli": "ccnot"}
        for src, dst in gate_map.items():
            body = re.sub(rf"\b{src}\b", dst, body)
        phase_expand = [("sdg", "rz(-pi/2)"), ("tdg", "rz(-pi/4)"),
                        ("s", "rz(pi/2)"), ("t", "rz(pi/4)")]
        for src, dst in phase_expand:
            body = re.sub(rf"\b{src}\b(?=\s*[\[q])", dst, body)
        inc_line = f'include "{_braket_gates_inc_path()}";'
    else:
        body = re.sub(r"\bcx\b", "cnot", body)
        inc_line = 'include "stdgates.inc";'
    if body:
        body += "\n"
    qasm3 = f"""OPENQASM 3.0;
{inc_line}
qubit[{n_qubits}] q;
bit[{n_bits}] c;
{body}c = measure q;
"""
    return qasm3


def transpile(qasm_str: str, target: str) -> str:
    """QASM 2.0 -> 目标后端原生表示（契约模式，供评测器语义模拟）。"""
    if target == "spinq":
        return qasm_str.strip() + "\n"
    if target == "braket":
        return _qasm2_to_qasm3(qasm_str, local=False)
    if target == "originq":
        return _qasm2_to_originir(qasm_str)
    raise ValueError(f"unsupported target: {target}")


# ---------------------------------------------------------------------------
# run：三后端本地模拟执行
# ---------------------------------------------------------------------------

def _run_spinq(qasm2: str, shots: int) -> Dict[str, Any]:
    import spinqit as sq
    from spinqit import BasicSimulatorConfig, get_basic_simulator, get_compiler
    with tempfile.NamedTemporaryFile(mode="w", suffix=".qasm", delete=False, encoding="utf-8") as tmp:
        tmp.write(qasm2)
        path = tmp.name
    try:
        compiler = get_compiler("qasm")
        ir = compiler.compile(path, 0)
        engine = get_basic_simulator()
        config = BasicSimulatorConfig()
        config.configure_shots(shots)
        result = engine.execute(ir, config)
        counts = {str(k): int(v) for k, v in result.counts.items()}
    finally:
        os.unlink(path)
    return {
        "backend": "spinq_basic_simulator",
        "job_id": f"spinq-{uuid.uuid4().hex[:12]}",
        "shots": shots, "counts": counts, "bit_order": "little",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {"qubits_count": ir.qnum},
    }


def _run_originq(qasm2: str, shots: int) -> Dict[str, Any]:
    import pyqpanda as pq
    machine = pq.CPUQVM()
    machine.init_qvm()
    try:
        prog, qreg, creg = pq.convert_qasm_string_to_qprog(qasm2, machine)
        raw = machine.run_with_configuration(prog, creg, shots)
        num_bits = len(creg)
        counts = {}
        for key, val in raw.items():
            bits = bin(key)[2:].zfill(num_bits) if isinstance(key, int) else str(key)
            counts[bits] = int(val)
    finally:
        machine.finalize()
    return {
        "backend": "originq_cpu_simulator",
        "job_id": f"originq-{uuid.uuid4().hex[:12]}",
        "shots": shots, "counts": counts, "bit_order": "little",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {"qubits_count": num_bits},
    }


def _run_braket(qasm2: str, shots: int) -> Dict[str, Any]:
    from braket.devices import LocalSimulator
    from braket.ir.openqasm import Program
    qasm3 = _qasm2_to_qasm3(qasm2, local=True)
    device = LocalSimulator()
    task = device.run(Program(source=qasm3), shots=shots)
    result = task.result()
    counts = {str(k): int(v) for k, v in result.measurement_counts.items()}
    return {
        "backend": "braket_local_simulator",
        "job_id": str(result.task_metadata.id),
        "shots": shots, "counts": counts, "bit_order": "little",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {"qubits_count": len(result.measured_qubits)},
    }


_REVERSE_BITORDER_TARGETS = {"spinq", "braket"}


def _normalize_counts(counts: Dict[str, int], target: str) -> Dict[str, int]:
    if target not in _REVERSE_BITORDER_TARGETS:
        return dict(counts)
    return {k[::-1]: v for k, v in counts.items()}


def run(qasm_str: str, target: str, shots: int = 8192) -> Dict[str, Any]:
    """执行电路并返回统一结果 schema（位序已归一化，key 最右 = c[0]）。"""
    if target == "spinq":
        result = _run_spinq(qasm_str, shots)
    elif target == "originq":
        result = _run_originq(qasm_str, shots)
    elif target == "braket":
        result = _run_braket(qasm_str, shots)
    else:
        raise ValueError(f"unsupported target: {target}")
    result["counts"] = _normalize_counts(result["counts"], target)
    return result
