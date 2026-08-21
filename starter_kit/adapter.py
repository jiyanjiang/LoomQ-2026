#!/usr/bin/env python3
"""LoomQ submission adapter contract v1.0.

This file intentionally contains no scoring implementation. Teams may implement
the functions directly or delegate to another language/runtime with subprocess.
"""

import json
import re
import tempfile
import time
import os
import uuid
from typing import Any, Dict, List, Tuple

SUPPORTED_TARGETS = ("spinq", "originq", "braket")


# ---------------------------------------------------------------------------
# QASM 2.0 -> target native IR (transpile)
# ---------------------------------------------------------------------------

# 目标 IR 契约允许的门白名单（仅作校验/纠错提示，不强制拒绝）
_WHITELIST_GATES = {"h", "x", "y", "z", "s", "sdg", "t", "tdg", "rx", "ry", "rz",
                    "cx", "cz", "swap", "ccx", "toffoli", "u1", "u2", "u3", "cu1", "cr", "measure", "barrier"}


def _parse_qasm2(qasm_str: str) -> Dict[str, Any]:
    """提取 QASM 2.0 的寄存器规模与测量位数（容错，供各后端生成原生 IR）。"""
    n_qubits = 0
    n_bits = 0
    for line in qasm_str.splitlines():
        line = line.strip()
        m = re.match(r"qreg\s+(\w+)\s*\[\s*(\d+)\s*\]", line)
        if m:
            n_qubits = max(n_qubits, int(m.group(2)))
        m = re.match(r"creg\s+(\w+)\s*\[\s*(\d+)\s*\]", line)
        if m:
            n_bits = max(n_bits, int(m.group(2)))
    return {"n_qubits": n_qubits, "n_bits": n_bits}


_BRAKET_GATES_INC = None


def _braket_gates_inc_path() -> str:
    """braket 本地模拟器自带的门定义文件（绝对路径，供 include 用）。"""
    global _BRAKET_GATES_INC
    if _BRAKET_GATES_INC is None:
        import braket.default_simulator as _bds
        _BRAKET_GATES_INC = os.path.join(
            os.path.dirname(os.path.abspath(_bds.__file__)),
            "openqasm",
            "braket_gates.inc",
        )
    return _BRAKET_GATES_INC


def _qasm2_to_qasm3(qasm2: str, local: bool = False) -> str:
    """QASM 2.0 -> 完整可执行 QASM 3.0（保持门序，重写寄存器与测量为 v3 语法）。

    两种模式：
      - local=False（transpile 契约输出）：include "stdgates.inc"（标准库名），
        门名保持标准 s/t/cx 等 —— 供评测器按契约语义模拟，绝不含本机路径。
      - local=True（run 本地执行）：include braket_gates.inc（绝对路径），
        门名映射到 braket 本地模拟器（cx→cnot 等），且 s/t→rz 展开
        （braket 1.27.0 本地模拟器 pow 幂次门缺失，退化为恒等门，QPT 实测）。
    """
    qasm2 = qasm2.strip()
    stmts = []
    n_qubits = 0
    n_bits = 0
    qreg_name = "q"
    creg_name = "c"
    # 先剥掉 // 注释（含注释行与行尾注释），避免注释里的 ; 干扰拆句
    code = re.sub(r"//.*$", "", qasm2, flags=re.MULTILINE)
    # 再按 ; 拆句（QASM 可能一行多语句），再逐句分类
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
            # QASM2 测量行（整寄存器或逐位）统一丢弃，在 v3 里用一条 c = measure q; 代替
            continue
        stmts.append(line)
    body = "\n".join(stmts).strip()
    # 寄存器名统一为 q / c（源可能用 bits 等任意名字）
    if qreg_name != "q":
        body = re.sub(rf"\b{qreg_name}\s*\[", "q[", body)
    if creg_name != "c":
        body = re.sub(rf"\b{creg_name}\s*\[", "c[", body)
    if local:
        # ---- 本地执行模式：门名映射到 braket 本地模拟器 ----
        gate_map = {
            "cx": "cnot",
            "cu1": "cphaseshift",
            "ccx": "ccnot",
            "toffoli": "ccnot",
        }
        for src, dst in gate_map.items():
            body = re.sub(rf"\b{src}\b", dst, body)
        # s/t→rz 展开（braket 1.27.0 本地模拟器 pow 幂次门缺失）
        phase_expand = [
            ("sdg", "rz(-pi/2)"),
            ("tdg", "rz(-pi/4)"),
            ("s", "rz(pi/2)"),
            ("t", "rz(pi/4)"),
        ]
        for src, dst in phase_expand:
            body = re.sub(rf"\b{src}\b(?=\s*[\[q])", dst, body)
        inc_line = f'include "{_braket_gates_inc_path()}";'
    else:
        # ---- 契约输出模式：标准 OpenQASM 3 ----
        # 契约示例用 cnot；评测器接受 cx 或 cnot。为贴近契约示例，cx→cnot。
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


def _qasm2_to_originir(qasm2: str) -> str:
    """QASM 2.0 -> OriginIR 文本（规范子集见 target_ir_contract.md）。"""
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
            # barrier 是编译屏障，无量子语义，OriginIR 不支持，跳过
            continue
        # 门行: name q[a],q[b] 或 name(theta) q[a]
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


# OriginIR 门名映射（按 target_ir_contract.md 契约；参数门用第二格式 门 q[k],(θ)）
_ORIGINIR_GATE_MAP = {
    "h": "H", "x": "X", "s": "S", "t": "T",
    "sdg": "SDAG", "tdg": "TDAG",
    "cx": "CNOT", "swap": "SWAP",
    "ccx": "TOFFOLI", "toffoli": "TOFFOLI",
}


def _originir_gate(name: str, params: str | None, qlist: list[str]) -> str:
    """QASM2 门行 -> OriginIR 行。参数门输出第二格式：RZ q[0],(θ)。"""
    gname = _ORIGINIR_GATE_MAP.get(name, name.upper())
    if params is not None:
        # 参数门第二格式：受控门 RZ q[0],(0.5) 或 CU1 q[0], q[1],(0.5)
        if len(qlist) > 1:
            return f"{gname} {', '.join(qlist)},({params})"
        return f"{gname} {qlist[0]},({params})"
    return f"{gname} {', '.join(qlist)}"


def _extract_qlist(qubits: str) -> List[str]:
    """把 'q[0], q[1]' 之类的量子比特列表转成 ['q[0]', 'q[1]']，寄存器名统一为 q。"""
    parts = re.findall(r"\w+\[\d+\]", qubits)
    if parts:
        return [re.sub(r"^\w+\[", "q[", p) for p in parts]
    # 无下标（如整寄存器名）：转成 q 占位，调用方按需处理
    return [qubits.strip()]


def transpile(qasm_str: str, target: str) -> str:
    """Translate OpenQASM 2.0 into the target backend's native representation."""
    if target == "spinq":
        # SpinQit 原生吃 QASM 2.0（QASMCompiler 接受文件路径）
        return qasm_str.strip() + "\n"
    if target == "braket":
        return _qasm2_to_qasm3(qasm_str, local=False)
    if target == "originq":
        return _qasm2_to_originir(qasm_str)
    raise ValueError(f"unsupported target: {target}")


# ---------------------------------------------------------------------------
# Run: 在本地模拟器上执行并返回统一结果 schema
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
        "shots": shots,
        "counts": counts,
        "bit_order": "little",
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
            if isinstance(key, int):
                bits = bin(key)[2:].zfill(num_bits)
            else:
                bits = str(key)
            counts[bits] = int(val)
    finally:
        machine.finalize()
    return {
        "backend": "originq_cpu_simulator",
        "job_id": f"originq-{uuid.uuid4().hex[:12]}",
        "shots": shots,
        "counts": counts,
        "bit_order": "little",
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
        "shots": shots,
        "counts": counts,
        "bit_order": "little",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {"qubits_count": len(result.measured_qubits)},
    }


# 位序归一化：统一到 Qiskit 风格（counts key 最右字符 = c[0]）。
# 实测位序（见 tests/cases.yaml 与 gate_mapping 文档）：
#   originq: key 最右 = c[0]（已正确，无需反转）
#   spinq  : key 最左 = q[0]（需反转）
#   braket : key 最左 = q[0]（需反转）
_REVERSE_BITORDER_TARGETS = {"spinq", "braket"}


def _normalize_counts(counts: Dict[str, int], target: str) -> Dict[str, int]:
    """把 counts 归一化为统一位序（key 最右 = c[0]）。"""
    if target not in _REVERSE_BITORDER_TARGETS:
        return dict(counts)
    return {k[::-1]: v for k, v in counts.items()}


def run(qasm_str: str, target: str, shots: int) -> Dict[str, Any]:
    """Execute a circuit and return the unified result schema from the rules."""
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


_L2_MAX_RETRIES = 3


def _l2_config() -> Dict[str, Any]:
    """读取 LOOMQ_LLM_* 环境变量（L2 契约）。缺失即抛错。"""
    import os as _os
    required = ("LOOMQ_LLM_BASE_URL", "LOOMQ_LLM_API_KEY", "LOOMQ_LLM_MODEL")
    missing = [name for name in required if not _os.environ.get(name)]
    if missing:
        raise RuntimeError("缺少 L2 环境变量: " + ", ".join(missing))
    try:
        timeout = float(_os.environ.get("LOOMQ_LLM_TIMEOUT_SECONDS", "120"))
    except ValueError:
        raise RuntimeError("LOOMQ_LLM_TIMEOUT_SECONDS 非法")
    return {
        "base_url": _os.environ["LOOMQ_LLM_BASE_URL"].rstrip("/"),
        "api_key": _os.environ["LOOMQ_LLM_API_KEY"],
        "model": _os.environ["LOOMQ_LLM_MODEL"],
        "timeout": timeout,
    }


def _l2_call_llm(cfg: Dict[str, Any], user_prompt: str) -> str:
    """调用 LLM 生成 QASM，返回原始文本。"""
    import urllib.request
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": _L2_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "temperature": 0,
        "max_tokens": 4096,
    }
    if cfg["model"] == "deepseek-v4-flash":
        payload["thinking"] = {"type": "disabled"}
    req = urllib.request.Request(
        cfg["base_url"] + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + cfg["api_key"], "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout"]) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"LLM HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM 不可达: {exc}") from exc
    return body["choices"][0]["message"]["content"]


_L2_SYSTEM_PROMPT = """你是量子电路专家。根据用户需求生成 OpenQASM 2.0 程序。
硬性约束：
1. 必须是完整可执行的 OpenQASM 2.0：版本行、include、qreg、creg、门、measure。
2. 只允许使用这 12 个门：h, x, s, sdg, t, tdg, rz(theta), ry(theta), cx, cu1(theta), swap, ccx。
   禁止白名单之外的门，禁止 if/自定义 gate/barrier 之外的非门指令。
3. 参数用 pi/2、pi/4 等简洁写法，或十进制小数。
4. 测量覆盖所有量子比特：整寄存器 measure q -> c; 或逐位 measure q[i] -> c[i];。
5. 量子比特数 = 经典比特数。
6. 直接输出 QASM 代码，不要 ``` 包裹，不要解释。"""


def _validate_and_run(qasm2: str) -> str:
    """自验：三后端本地模拟器跑一遍，返回空串=通过；否则返回错误原因。"""
    import tempfile as _tf
    for target in ("spinq", "originq", "braket"):
        try:
            result = run(qasm2, target, 1024)
            counts = result["counts"]
            if not counts:
                return f"{target}: 空 counts"
            total = sum(counts.values())
            if total != 1024:
                return f"{target}: counts 总和 {total} != 1024"
        except Exception as exc:
            return f"{target}: {type(exc).__name__}: {str(exc)[:80]}"
    return ""


def agent_chat(prompt: str) -> str:
    """Optional L2 entry point using the documented LOOMQ_LLM_* environment.

    闭环：LLM 生成 QASM → 三后端自验 → 失败则带错误原因重试（最多 3 次）。
    正式评测注入 deepseek-v4-flash 环境；本地可用自己的 DeepSeek key 调试。
    """
    cfg = _l2_config()
    last_error = "未生成"
    for attempt in range(1, _L2_MAX_RETRIES + 1):
        user_msg = f"请生成满足以下需求的 OpenQASM 2.0 电路：\n{prompt}\n\n直接输出 QASM 代码，不要解释。"
        if last_error != "未生成":
            user_msg += f"\n\n上次生成的电路自验失败：{last_error}。请修正后重新输出。"
        reply = _l2_call_llm(cfg, user_msg)
        # 提取 QASM 2.0 块（容忍 ``` 包裹）
        import re as _re
        match = _re.search(r"OPENQASM\s+2\.0;.*?(?=^\s*```|\Z)", reply, _re.DOTALL | _re.MULTILINE)
        qasm = match.group(0).strip() if match else ""
        if not qasm:
            last_error = "回复中无 OPENQASM 2.0 程序"
            continue
        err = _validate_and_run(qasm)
        if not err:
            return qasm
        last_error = err
    raise RuntimeError(f"L2 自验闭环失败（{_L2_MAX_RETRIES} 次重试后）: {last_error}")


# ---------------------------------------------------------------------------
# L3: 量子-经典混合编译（classical {} 块 → RISC-V 汇编）
# 规格：docs/l3_riscv_encoding_spec.md
# ---------------------------------------------------------------------------

_L3_IFELSE_RE = re.compile(
    r"if\s*\(\s*c\s*\[\s*\d+\s*\]\s*(==|!=)\s*(-?\d+)\s*\)\s*"
    r"\{(.*?)\}"
    r"(?:\s*else\s*\{(.*?)\})?",
    re.DOTALL,
)
_L3_STMT_RE = re.compile(r"(r\d+)\s*=\s*([^;}]+)")
_L3_DECL_RE = re.compile(r"^(OPENQASM\s|include\s|qreg\s|creg\s)")


def _split_hybrid(source: str) -> Tuple[str, str]:
    """把混合源拆成（量子部分, classical 块部分）。

    支持单/多 classical 块、单行/多行块体；未闭合花括号抛 ValueError。
    """
    quantum_parts: List[str] = []
    classical_parts: List[str] = []
    rest = source
    while True:
        m = re.search(r"\bclassical\s*\{", rest)
        if not m:
            quantum_parts.append(rest)
            break
        start = m.start()
        depth = 0
        i = m.end() - 1  # 指向 '{'
        while i < len(rest):
            if rest[i] == "{":
                depth += 1
            elif rest[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if depth != 0:
            raise ValueError("classical 块未闭合: 缺少 }")
        quantum_parts.append(rest[:start])
        classical_parts.append(rest[start:i + 1])
        rest = rest[i + 1:]
    return "".join(quantum_parts), "\n".join(classical_parts)


def _l3_emit_assign(stmt: re.Match) -> str:
    """把一条 `rN = 值` 赋值翻译为指令。值可为整数常量或另一变量 rM。"""
    rd = stmt.group(1)
    val = stmt.group(2).strip()
    if re.fullmatch(r"-?\d+", val):
        return f"li x{rd[1:]}, {val}"
    if re.fullmatch(r"r\d+", val):
        # rN = rM  →  add xN, xM, x0（x0 恒 0，充当加法单位元）
        return f"add x{rd[1:]}, x{val[1:]}, x0"
    raise ValueError(f"classical 赋值不支持: {rd} = {val}")


def _classical_to_riscv(classical_src: str) -> str:
    """把 classical{...} 块翻译为 TinyRISCVEmulator 可执行的汇编文本。

    变量映射：测量结果 c[i] → x10（评测方预置）；rN → xN；比较常量 → x11 起临时寄存器。
    if(条件) 前置跳转，else 分支 fall-through + j END；无 else 用反向分支跳过。
    """
    body = classical_src
    m = re.search(r"\bclassical\s*\{", body)
    if m:
        body = body[m.end():]
        body = re.sub(r"\}\s*$", "", body.rstrip(), count=1)
    asm: List[str] = ["# L3: classical -> RISC-V"]
    used: set[int] = {10}  # x10 = 测量入口，永不被临时寄存器复用
    n = 0
    for match in _L3_IFELSE_RE.finditer(body):
        op, k = match.group(1), int(match.group(2))
        then_body, else_body = match.group(3) or "", match.group(4)
        targets: set[int] = set()
        for stmt in _L3_STMT_RE.finditer(then_body + " " + (else_body or "")):
            targets.add(int(stmt.group(1)[1:]))
        temp = 11
        while temp in used or temp in targets:
            temp += 1
        used.add(temp)
        lt, le = f"L3_THEN_{n}", f"L3_END_{n}"
        n += 1
        if else_body:
            asm.append(f"li x{temp}, {k}")
            asm.append(f"{'beq' if op == '==' else 'bne'} x10, x{temp}, {lt}")
            for stmt in _L3_STMT_RE.finditer(else_body):
                asm.append(_l3_emit_assign(stmt))
            asm.append(f"j {le}")
            asm.append(f"{lt}:")
            for stmt in _L3_STMT_RE.finditer(then_body):
                asm.append(_l3_emit_assign(stmt))
            asm.append(f"{le}:")
        else:
            # 无 else：条件不成立（!=）时直接跳过 then 块
            asm.append(f"li x{temp}, {k}")
            asm.append(f"{'bne' if op == '==' else 'beq'} x10, x{temp}, {le}")
            asm.append(f"{lt}:")
            for stmt in _L3_STMT_RE.finditer(then_body):
                asm.append(_l3_emit_assign(stmt))
            asm.append(f"{le}:")
    return "\n".join(asm)


def compile_hybrid(hybrid_qasm_str: str) -> Tuple[List[str], str]:
    """L3：解析含 classical{} 块的混合 QASM，返回 (quantum_ops, riscv_assembly)。

    - quantum_ops: 量子部分逐条门操作（list[str]，含 measure/barrier，不含声明与注释）。
    - assembly: classical{} 块翻译的 RISC-V 汇编（TinyRISCVEmulator 可执行）。
    """
    quantum_part, classical_part = _split_hybrid(hybrid_qasm_str)
    quantum_ops = []
    for line in quantum_part.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        # 按 ; 分句：丢弃声明句（OPENQASM/include/qreg/creg），保留门/measure
        for stmt in line.split(";"):
            stmt = stmt.strip()
            if not stmt or _L3_DECL_RE.match(stmt):
                continue
            quantum_ops.append(stmt + ";")
    assembly = _classical_to_riscv(classical_part)
    if not assembly.strip():
        raise ValueError("classical 块为空，无法生成汇编")
    return quantum_ops, assembly
