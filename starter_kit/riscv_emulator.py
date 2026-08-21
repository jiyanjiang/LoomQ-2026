#!/usr/bin/env python3
"""
LoomQ 量子接入平权计划 - 轻量级 RISC-V 寄存器与控制流模拟器

本模拟器用于在本地评估和调试 L3 (量子-经典混合编程) 的经典部分代码。
支持基础的通用寄存器操作和控制流分支跳转指令，无需选手配置重型 QEMU。
"""

import math
import random
from typing import Dict, List, Tuple, Any

# ===== 量子扩展指令集（RISC-V CUSTOM-0 编码空间，opcode=0x0B）=====
# 编码布局（I-type）：imm[11:0] | rs1[4:0] | funct3[2:0] | rd[4:0] | opcode[6:0]
#   qinit : funct3=000, 重置 4-qubit 态矢为 |0000>
#   qh    : funct3=001, rd=qubit 索引, 施加 Hadamard 门
#   qcnot : funct3=010, rs1=控制 qubit, rd=目标 qubit, 施加 CNOT 门
#   qrx   : funct3=011, rd=qubit 索引, imm=旋转角(度), 施加绕 x 轴旋转门
#   qmeas : funct3=100, rs1=qubit 索引, rd=经典寄存器, 测量并写回 0/1
OPCODE_CUSTOM0 = 0x0B
QUANTUM_FUNCT3 = {"qinit": 0b000, "qh": 0b001, "qcnot": 0b010, "qrx": 0b011, "qmeas": 0b100}
QUANTUM_OPS = set(QUANTUM_FUNCT3)
N_QUBITS = 4  # 量子寄存器 q0-q3


class TinyRISCVEmulator:
    def __init__(self):
        # 32个通用寄存器 x0 - x31，x0 恒为 0
        self.registers = [0] * 32
        self.pc = 0
        self.labels: Dict[str, int] = {}
        self.instructions: List[Tuple[str, List[str]]] = []
        self.max_steps = 1000  # 防止死循环
        # 量子态：4 qubit 态矢量，little-endian（q0 为最低位），初始 |0000>
        self.statevector: List[complex] = [0.0] * (1 << N_QUBITS)
        self.statevector[0] = 1.0
        self._rng = random.Random()  # 测量用随机源，set_seed 可复现

    def set_register(self, reg: str, value: int):
        idx = self._parse_reg_idx(reg)
        if idx != 0:
            self.registers[idx] = value

    def get_register(self, reg: str) -> int:
        idx = self._parse_reg_idx(reg)
        return self.registers[idx]

    def _parse_reg_idx(self, reg: str) -> int:
        reg = reg.strip().replace(",", "")
        if not reg.startswith("x") and not reg.startswith("X"):
            raise ValueError(f"无效的寄存器名称: {reg}")
        idx = int(reg[1:])
        if idx < 0 or idx > 31:
            raise ValueError(f"寄存器索引超出范围 (x0-x31): {reg}")
        return idx

    def load_program(self, asm_code: str):
        """
        解析汇编代码并建立标签索引
        """
        self.instructions = []
        self.labels = {}
        self.pc = 0
        self.registers = [0] * 32
        # 重载程序时量子态一并重置
        self.statevector = [0.0] * (1 << N_QUBITS)
        self.statevector[0] = 1.0
        
        lines = asm_code.split("\n")
        temp_instructions = []
        
        # 第一次解析：过滤注释、空行并建立指令列表与 Label 映射
        for line in lines:
            line = line.strip()
            # 过滤注释和空行
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            
            # 分割行内注释
            if "#" in line:
                line = line.split("#")[0].strip()
            
            # 提取标签，例如 "LABEL_A:"
            if line.endswith(":"):
                label_name = line[:-1].strip()
                self.labels[label_name] = len(temp_instructions)
                continue
            elif ":" in line:
                # 处理同行的标签，例如 "LOOP: li x1, 10"
                parts = line.split(":", 1)
                label_name = parts[0].strip()
                self.labels[label_name] = len(temp_instructions)
                line = parts[1].strip()
            
            # 解析指令和参数
            tokens = line.replace(",", " ").split()
            op = tokens[0].lower()
            args = tokens[1:]
            temp_instructions.append((op, args))
            
        self.instructions = temp_instructions

    def execute(self) -> Dict[str, int]:
        """
        执行已载入的指令直到程序结束，返回所有寄存器状态字典
        """
        steps = 0
        num_instr = len(self.instructions)
        
        while 0 <= self.pc < num_instr:
            steps += 1
            if steps > self.max_steps:
                raise RuntimeError("程序执行超出最大步数限制，疑似发生死循环")
                
            op, args = self.instructions[self.pc]
            next_pc = self.pc + 1
            
            # 模拟执行各指令
            if op == "li":
                # li rd, imm
                rd, imm = args[0], int(args[1])
                self.set_register(rd, imm)
                
            elif op == "add":
                # add rd, rs1, rs2
                rd, rs1, rs2 = args[0], args[1], args[2]
                self.set_register(rd, self.get_register(rs1) + self.get_register(rs2))
                
            elif op == "sub":
                # sub rd, rs1, rs2
                rd, rs1, rs2 = args[0], args[1], args[2]
                self.set_register(rd, self.get_register(rs1) - self.get_register(rs2))
                
            elif op == "addi":
                # addi rd, rs1, imm
                rd, rs1, imm = args[0], args[1], int(args[2])
                self.set_register(rd, self.get_register(rs1) + imm)
                
            elif op == "beq":
                # beq rs1, rs2, label
                rs1, rs2, label = args[0], args[1], args[2]
                if self.get_register(rs1) == self.get_register(rs2):
                    if label not in self.labels:
                        raise ValueError(f"未定义的跳转标签: {label}")
                    next_pc = self.labels[label]
                    
            elif op == "bne":
                # bne rs1, rs2, label
                rs1, rs2, label = args[0], args[1], args[2]
                if self.get_register(rs1) != self.get_register(rs2):
                    if label not in self.labels:
                        raise ValueError(f"未定义的跳转标签: {label}")
                    next_pc = self.labels[label]
                    
            elif op == "j":
                # j label
                label = args[0]
                if label not in self.labels:
                    raise ValueError(f"未定义的跳转标签: {label}")
                next_pc = self.labels[label]

            elif op in QUANTUM_OPS:
                # 量子扩展指令：统一经 32 位 CUSTOM-0 机器码编码后执行
                self._exec_quantum_word(self.encode_quantum(op, args))

            else:
                raise ValueError(f"不支持的指令操作: {op}")
                
            self.pc = next_pc
            
        # 返回非零寄存器的状态汇总
        result = {}
        for idx, val in enumerate(self.registers):
            if val != 0:
                result[f"x{idx}"] = val
        return result

    # ===================== 量子扩展（Bonus +8）=====================
    def _parse_qubit(self, qb: str) -> int:
        qb = qb.strip().lower()
        if not qb.startswith("q"):
            raise ValueError(f"无效的量子寄存器名称: {qb}")
        idx = int(qb[1:])
        if idx < 0 or idx >= N_QUBITS:
            raise ValueError(f"量子寄存器索引超出范围 (q0-q{N_QUBITS - 1}): {qb}")
        return idx

    def set_seed(self, seed: int):
        """设置测量随机种子，保证可复现。"""
        self._rng = random.Random(seed)

    def get_statevector(self) -> List[complex]:
        """返回当前 4-qubit 态矢量（q0 为最低位）的副本。"""
        return list(self.statevector)

    # ---- 量子门 ----
    def _apply_h(self, qb: int):
        mask = 1 << qb
        inv = math.sqrt(0.5)
        amp = self.statevector
        for i in range(len(amp)):
            if i & mask:
                continue
            a, b = amp[i], amp[i | mask]
            amp[i] = inv * (a + b)
            amp[i | mask] = inv * (a - b)

    def _apply_cnot(self, ctrl: int, tgt: int):
        mask_t = 1 << tgt
        mask_c = 1 << ctrl
        amp = self.statevector
        for i in range(len(amp)):
            if (i & mask_c) and not (i & mask_t):
                j = i | mask_t
                amp[i], amp[j] = amp[j], amp[i]

    def _apply_rx(self, qb: int, theta_deg: float):
        theta = math.radians(theta_deg)
        c, s = math.cos(theta / 2), math.sin(theta / 2)
        mask = 1 << qb
        amp = self.statevector
        for i in range(len(amp)):
            if i & mask:
                continue
            a, b = amp[i], amp[i | mask]
            amp[i] = c * a - 1j * s * b
            amp[i | mask] = -1j * s * a + c * b

    def _measure(self, qb: int) -> int:
        """对 qubit qb 做投影测量并坍缩态矢，返回 0/1。"""
        mask = 1 << qb
        p1 = sum(abs(a) ** 2 for i, a in enumerate(self.statevector) if i & mask)
        p1 = min(1.0, max(0.0, p1))
        out = 1 if self._rng.random() < p1 else 0
        amp = self.statevector
        if out == 1:
            norm = math.sqrt(p1)
            for i in range(len(amp)):
                amp[i] = (amp[i] / norm) if (i & mask) else 0.0
        else:
            p0 = 1.0 - p1
            norm = math.sqrt(p0) if p0 > 0 else 1.0
            for i in range(len(amp)):
                amp[i] = (amp[i] / norm) if not (i & mask) else 0.0
        return out

    # ---- 32 位 CUSTOM-0 机器码编码 / 解码 ----
    def encode_quantum(self, op: str, args: List[str]) -> int:
        op = op.lower()
        if op not in QUANTUM_FUNCT3:
            raise ValueError(f"非量子指令: {op}")
        f3 = QUANTUM_FUNCT3[op]
        rd = rs1 = imm = 0
        if op == "qh":
            rd = self._parse_qubit(args[0])
        elif op == "qcnot":
            rs1 = self._parse_qubit(args[0])
            rd = self._parse_qubit(args[1])
        elif op == "qrx":
            rd = self._parse_qubit(args[0])
            imm = int(args[1])
            if imm < -2048 or imm > 2047:
                raise ValueError(f"qrx 旋转角超出 12 位有符号范围 [-2048, 2047]: {imm}")
            imm &= 0xFFF
        elif op == "qmeas":
            rs1 = self._parse_qubit(args[0])
            rd = self._parse_reg_idx(args[1])
        return (imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | OPCODE_CUSTOM0

    def decode_quantum(self, word: int) -> Tuple[str, List[str]]:
        if word & 0x7F != OPCODE_CUSTOM0:
            raise ValueError(f"非 CUSTOM-0 编码: 0x{word:08x}")
        f3 = (word >> 12) & 0x7
        rd = (word >> 7) & 0x1F
        rs1 = (word >> 15) & 0x1F
        imm = (word >> 20) & 0xFFF
        if imm & 0x800:
            imm -= 0x1000
        if f3 == 0b000:
            return ("qinit", [])
        if f3 == 0b001:
            return ("qh", [f"q{rd}"])
        if f3 == 0b010:
            return ("qcnot", [f"q{rs1}", f"q{rd}"])
        if f3 == 0b011:
            return ("qrx", [f"q{rd}", str(imm)])
        if f3 == 0b100:
            return ("qmeas", [f"q{rs1}", f"x{rd}"])
        raise ValueError(f"未知量子 funct3: {f3:#05b}")

    def _exec_quantum_word(self, word: int):
        op, args = self.decode_quantum(word)
        if op == "qinit":
            self.statevector = [0.0] * (1 << N_QUBITS)
            self.statevector[0] = 1.0
        elif op == "qh":
            self._apply_h(self._parse_qubit(args[0]))
        elif op == "qcnot":
            self._apply_cnot(self._parse_qubit(args[0]), self._parse_qubit(args[1]))
        elif op == "qrx":
            self._apply_rx(self._parse_qubit(args[0]), int(args[1]))
        elif op == "qmeas":
            out = self._measure(self._parse_qubit(args[0]))
            self.set_register(args[1], out)

    def machine_code(self) -> List[int]:
        """把已加载程序中的量子指令编码为 32 位机器码列表。"""
        return [self.encode_quantum(op, args) for op, args in self.instructions if op in QUANTUM_OPS]

    def run_machine_code(self, words: List[int]):
        """直接执行 32 位 CUSTOM-0 机器码（不经汇编文本）。"""
        for word in words:
            self._exec_quantum_word(word)

# 简易功能测试
if __name__ == "__main__":
    code = """
    li x1, 5
    li x2, 10
    beq x1, x2, EQUAL
    add x3, x1, x2       # x3 = 15
    j END
    EQUAL:
    sub x3, x2, x1
    END:
    addi x3, x3, 1       # x3 = 16
    """
    emu = TinyRISCVEmulator()
    emu.load_program(code)
    state = emu.execute()
    print("寄存器执行最终状态:", state)
    assert state.get("x3") == 16, "测试失败！"
    print("Tiny RISC-V 模拟器核心测试通过！")

    # ---- 量子扩展自测 ----
    qemu = TinyRISCVEmulator()
    qemu.load_program("qh q0\nqcnot q0, q1\n")
    qemu.execute()
    sv = qemu.get_statevector()
    assert len(sv) == 16, "态矢维度错误"
    bell_ok = (
        abs(abs(sv[0]) - 1 / math.sqrt(2)) < 1e-9
        and abs(abs(sv[3]) - 1 / math.sqrt(2)) < 1e-9
        and all(abs(sv[i]) < 1e-9 for i in (1, 2))
    ), f"Bell 态校验失败: {sv[:4]}"
    assert bell_ok, "Bell 态校验失败"
    # 机器码编码往返
    words = qemu.machine_code()
    assert words == [qemu.encode_quantum("qh", ["q0"]), qemu.encode_quantum("qcnot", ["q0", "q1"])]
    assert qemu.decode_quantum(words[0]) == ("qh", ["q0"])
    assert qemu.decode_quantum(words[1]) == ("qcnot", ["q0", "q1"])
    print("量子扩展自测通过：Bell 态 (|00>+|11>)/√2，机器码往返一致")
