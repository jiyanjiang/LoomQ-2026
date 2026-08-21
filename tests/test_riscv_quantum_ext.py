#!/usr/bin/env python3
"""Bonus +8 量子 RISC-V 扩展 端到端测试。

覆盖：
  1. 经典回归：官方 7 条指令行为不变（x3=16）
  2. 单门态矢：qh q0 → (|0>+|1>)/√2
  3. 纠缠态：qh q0; qcnot q0,q1 → Bell 态 (|00>+|11>)/√2
  4. 含参门：qrx q0,180 → |0>→-i|1>；qrx 360° 回环
  5. qinit 重置
  6. 测量写经典寄存器 + 坍缩后二次测量一致（纠缠关联）
  7. 测量统计分布：Bell 态 8192 次仅 00/11 各约 50%
  8. 经典-量子混合程序（寄存器承接测量结果）
  9. 32 位 CUSTOM-0 机器码 encode/decode 往返（5 条指令全覆盖）
 10. machine_code()/run_machine_code() 与汇编执行等价
 11. L3 评测契约回归：evaluator --level l3 仍 1 项 PASS

用法：python3 tests/test_riscv_quantum_ext.py
"""

import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "starter_kit"))

from riscv_emulator import TinyRISCVEmulator, N_QUBITS  # noqa: E402

SQRT2_INV = 1.0 / math.sqrt(2.0)
SHOTS = 8192


class TestClassicRegression(unittest.TestCase):
    """官方 7 条经典指令回归：扩展不得改变 L3 行为。"""

    def test_official_example(self):
        code = """
        li x1, 5
        li x2, 10
        beq x1, x2, EQUAL
        add x3, x1, x2
        j END
        EQUAL:
        sub x3, x2, x1
        END:
        addi x3, x3, 1
        """
        emu = TinyRISCVEmulator()
        emu.load_program(code)
        state = emu.execute()
        self.assertEqual(state.get("x3"), 16)

    def test_branch_flow(self):
        code = "li x1, 3\nli x2, 3\nbne x1, x2, NO\nli x4, 7\nj END\nNO:\nli x4, 9\nEND:\n"
        emu = TinyRISCVEmulator()
        emu.load_program(code)
        state = emu.execute()
        self.assertEqual(state.get("x4"), 7)


class TestQuantumGates(unittest.TestCase):
    def _run(self, asm):
        emu = TinyRISCVEmulator()
        emu.load_program(asm)
        emu.execute()
        return emu

    def test_qh_statevector(self):
        emu = self._run("qh q0\n")
        sv = emu.get_statevector()
        self.assertEqual(len(sv), 1 << N_QUBITS)
        self.assertAlmostEqual(abs(sv[0]), SQRT2_INV)
        self.assertAlmostEqual(abs(sv[1]), SQRT2_INV)
        self.assertTrue(all(abs(sv[i]) < 1e-12 for i in range(2, len(sv))))

    def test_bell_state(self):
        emu = self._run("qh q0\nqcnot q0, q1\n")
        sv = emu.get_statevector()
        self.assertAlmostEqual(abs(sv[0]), SQRT2_INV)  # |00>
        self.assertAlmostEqual(abs(sv[3]), SQRT2_INV)  # |11>
        self.assertTrue(all(abs(sv[i]) < 1e-12 for i in (1, 2)))

    def test_ghz_state(self):
        emu = self._run("qh q0\nqcnot q0, q1\nqcnot q0, q2\n")
        sv = emu.get_statevector()
        self.assertAlmostEqual(abs(sv[0]), SQRT2_INV)  # |000>
        self.assertAlmostEqual(abs(sv[7]), SQRT2_INV)  # |111>
        self.assertEqual(sum(1 for a in sv if abs(a) > 1e-12), 2)

    def test_qrx_180(self):
        # Rx(180°)：|0> → -i|1>，|1> → -i|0>
        emu = self._run("qrx q0, 180\n")
        sv = emu.get_statevector()
        self.assertAlmostEqual(abs(sv[0]), 0.0)
        self.assertAlmostEqual(abs(sv[1]), 1.0)

    def test_qrx_360_returns(self):
        # Rx(360°)：整体相位 -1，振幅绝对值回环
        emu = self._run("qrx q0, 360\n")
        sv = emu.get_statevector()
        self.assertAlmostEqual(abs(sv[0]), 1.0)
        self.assertAlmostEqual(abs(sv[1]), 0.0)

    def test_qinit_reset(self):
        emu = self._run("qh q0\nqcnot q0, q1\nqinit\n")
        sv = emu.get_statevector()
        self.assertAlmostEqual(sv[0], 1.0)
        self.assertTrue(all(abs(sv[i]) < 1e-12 for i in range(1, len(sv))))


class TestMeasurement(unittest.TestCase):
    def test_qmeas_writes_register_and_collapses(self):
        emu = TinyRISCVEmulator()
        emu.set_seed(42)
        emu.load_program("qh q0\nqmeas q0, x2\n")
        emu.execute()
        out1 = emu.get_register("x2")
        self.assertIn(out1, (0, 1))
        # 坍缩后态为 |out1>，再次测量必得相同结果
        emu.load_program("qmeas q0, x3\n")
        emu.execute()
        self.assertEqual(emu.get_register("x3"), out1)

    def test_bell_measurement_correlation(self):
        # Bell 态中测 q0 得 0/1 后，测 q1 必得一致结果（纠缠关联）
        emu = TinyRISCVEmulator()
        emu.set_seed(7)
        emu.load_program("qh q0\nqcnot q0, q1\nqmeas q0, x2\nqmeas q1, x3\n")
        emu.execute()
        self.assertEqual(emu.get_register("x2"), emu.get_register("x3"))

    def test_measurement_distribution(self):
        # Bell 态 8192 次：仅 00/11，各约 50%，01/10 严格为 0
        c = {"00": 0, "11": 0, "01": 0, "10": 0}
        for _ in range(SHOTS):
            emu = TinyRISCVEmulator()
            emu.load_program("qh q0\nqcnot q0, q1\nqmeas q0, x2\nqmeas q1, x3\n")
            emu.execute()
            key = f"{emu.get_register('x3')}{emu.get_register('x2')}"
            c[key] += 1
        self.assertEqual(c["01"], 0)
        self.assertEqual(c["10"], 0)
        self.assertGreater(c["00"] / SHOTS, 0.45)
        self.assertGreater(c["11"] / SHOTS, 0.45)
        self.assertLess(c["00"] / SHOTS, 0.55)
        self.assertLess(c["11"] / SHOTS, 0.55)


class TestHybridProgram(unittest.TestCase):
    def test_hybrid_quantum_classic(self):
        # 经典 li + 量子 Bell 制备 + 测量写回 x2 + 经典加法
        for _ in range(50):
            emu = TinyRISCVEmulator()
            emu.load_program(
                "li x1, 1\n"
                "qh q0\n"
                "qcnot q0, q1\n"
                "qmeas q1, x2\n"
                "add x3, x1, x2\n"
            )
            emu.execute()
            x2 = emu.get_register("x2")
            x3 = emu.get_register("x3")
            self.assertIn(x2, (0, 1))
            self.assertEqual(x3, 1 + x2)
        # 统计上 x2 应两种取值都出现过（P(缺失)<2^-50）
        seen = set()
        for _ in range(50):
            emu = TinyRISCVEmulator()
            emu.load_program("qh q0\nqmeas q0, x2\n")
            emu.execute()
            seen.add(emu.get_register("x2"))
        self.assertEqual(seen, {0, 1})


class TestMachineCode(unittest.TestCase):
    OPS = [
        ("qinit", []),
        ("qh", ["q0"]),
        ("qcnot", ["q0", "q1"]),
        ("qrx", ["q1", "180"]),
        ("qmeas", ["q0", "x2"]),
    ]
    KNOWN_WORDS = {
        "qinit": 0x0000000B,
        "qh q0": 0x0000100B,
        "qcnot q0, q1": 0x0000208B,
        "qrx q1, 180": 0x0B40308B,
        "qmeas q0, x2": 0x0000410B,
    }

    def test_encode_decode_roundtrip(self):
        emu = TinyRISCVEmulator()
        for op, args in self.OPS:
            word = emu.encode_quantum(op, args)
            dec_op, dec_args = emu.decode_quantum(word)
            self.assertEqual((dec_op, dec_args), (op, args))

    def test_known_machine_words(self):
        # 与规格文档 §6 实测值逐字一致
        emu = TinyRISCVEmulator()
        for op, word in self.KNOWN_WORDS.items():
            if op == "qinit":
                w = emu.encode_quantum("qinit", [])
            else:
                name, rest = op.split(" ", 1)
                a = [x for x in rest.split(", ") if x]
                w = emu.encode_quantum(name, a)
            self.assertEqual(w, word, f"{op}")

    def test_machine_code_equivalent_to_asm(self):
        asm = "qh q0\nqcnot q0, q1\n"
        emu_asm = TinyRISCVEmulator()
        emu_asm.load_program(asm)
        emu_asm.execute()

        emu_mc = TinyRISCVEmulator()
        emu_mc.load_program(asm)
        words = emu_mc.machine_code()
        self.assertEqual(len(words), 2)
        emu_mc.run_machine_code(words)
        self.assertEqual(emu_mc.get_statevector(), emu_asm.get_statevector())


class TestEvaluatorRegression(unittest.TestCase):
    def test_evaluator_l3_still_passes(self):
        r = subprocess.run(
            [sys.executable, str(ROOT / "starter_kit" / "evaluator.py"), "--level", "l3"],
            capture_output=True, text=True, timeout=180,
        )
        self.assertEqual(r.returncode, 0, f"stderr={r.stderr}\nstdout={r.stdout}")
        self.assertIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
