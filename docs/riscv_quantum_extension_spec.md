# LoomQ 量子 RISC-V 扩展指令规格（Bonus +8）

> 版本：v1.0 ｜ 定稿日期：2026-08-21 ｜ 状态：已实现并端到端测试通过
>
> 对应赛题 Bonus +8：**fork `riscv_emulator.py` 增加指令支持**。本规格是"自定义量子指令编码"三件套之一，与扩展实现 `starter_kit/riscv_emulator.py`、端到端测试 `tests/test_riscv_quantum_ext.py` 配套。

## 一、背景与目标

官方 `riscv_emulator.py` 是一个轻量级 RISC-V 寄存器与控制流模拟器，支持 7 条经典指令（`li/add/sub/addi/beq/bne/j`），用于 L3（量子-经典混合编程，15 分）的经典侧执行。

Bonus +8 要求在官方模拟器基础上 **fork 增加指令支持**。本扩展选择"量子操作指令"方向：在模拟器内引入 4-qubit 态矢量模型，新增 5 条量子指令，全部走 RISC-V **CUSTOM-0 编码空间**（opcode = `0x0B`），使量子操作与经典指令在同一个 32 位指令字体系下统一编码、解码、执行。

设计目标：

1. **向后兼容**：官方 7 条经典指令语义、`TinyRISCVEmulator` 类名、`load_program/set_register/get_register/execute` 接口、`execute()` 返回值（非零寄存器字典）全部逐字不变。L3 评测契约不受任何影响。
2. **custom opcode 真实落地**：量子指令不是文本特判，而是统一编码为 32 位机器码后再执行（`encode_quantum → decode_quantum → _exec_quantum_word` 同一条路径）。
3. **端到端可验证**：单门态矢、纠缠态、测量分布、经典-量子混合程序、机器码往返均有自动化测试。

## 二、编码空间

量子指令使用 RISC-V **CUSTOM-0** 操作码空间（`opcode[6:0] = 0x0B`），I-type 布局：

```
 31           20 19   15 14   12 11    7 6     0
+---------------+-------+-------+-------+-------+
| imm[11:0]     | rs1   |funct3 | rd    | 0x0B  |
+---------------+-------+-------+-------+-------+
 12 bits         5 bits  3 bits  5 bits  7 bits
```

字段约定：

| 字段 | 含义 |
|------|------|
| `imm[11:0]` | 12 位有符号立即数（仅 `qrx` 用作旋转角，单位：度） |
| `rs1[4:0]` | 控制 qubit 索引（`qcnot`）/ 被测 qubit 索引（`qmeas`），其他指令为 0 |
| `funct3[2:0]` | 指令子类型（见下表） |
| `rd[4:0]` | 目标 qubit 索引（`qh/qrx`）/ 目标 qubit（`qcnot`）/ 经典寄存器索引（`qmeas`），`qinit` 为 0 |

## 三、指令集

| 助记符 | funct3 | 汇编语法 | rd | rs1 | imm | 语义 |
|--------|--------|----------|----|----|-----|------|
| `qinit` | `000` | `qinit` | 0 | 0 | 0 | 重置 4-qubit 态矢为 `\|0000⟩` |
| `qh` | `001` | `qh qb` | qubit | 0 | 0 | 对 qubit `qb` 施加 Hadamard 门 |
| `qcnot` | `010` | `qcnot qc, qt` | 目标 qubit | 控制 qubit | 0 | 控制非门：`qc` 为 1 时翻转 `qt` |
| `qrx` | `011` | `qrx qb, θ` | qubit | 0 | θ（度） | 绕 x 轴旋转 θ°：`Rx(θ)` |
| `qmeas` | `100` | `qmeas qb, rd` | 经典寄存器 | qubit | 0 | 测量 qubit `qb`（投影坍缩），结果 0/1 写入经典寄存器 `rd` |

约束：

- qubit 索引 `qb` 范围 `q0–q3`（4 个量子寄存器），越界报错。
- `qrx` 旋转角 `θ` 为 12 位有符号整数，范围 `[-2048, 2047]` 度。
- `qmeas` 的 `rd` 沿用经典寄存器解析规则（`x0–x31`，写入 `x0` 无效——与经典指令一致）。

## 四、执行模型

- **态矢量**：4 qubit → 2^4 = 16 维复振幅向量，little-endian（`q0` 为最低位，态矢索引 `i` 的二进制第 k 位对应 `qk`）。
- **初始态**：`|0000⟩`（`statevector[0] = 1`）。
- **门操作**：`qh`/`qcnot`/`qrx` 按标准矩阵作用于态矢，不消耗经典寄存器、不影响 PC。
- **测量**：`qmeas qb, rd` 按 Born 规则采样——`p(1) = Σ|amp[i]|²（i 的第 qb 位为 1）`，以随机源（默认 `random.Random`，可用 `set_seed(seed)` 固定）决定结果，随后将态矢投影坍缩到对应子空间并归一化；结果写入经典寄存器 `rd`。
- **经典-量子混合**：量子指令与经典指令在同一个指令流中顺序执行，可交错（如 `li x1, 1` → `qh q0` → `qcnot q0, q1` → `qmeas q1, x2` → `add x3, x1, x2`）。经典寄存器的值可被量子测量写回，量子态不进入通用寄存器。
- **重载语义**：`load_program()` 重载程序时态矢一并重置为 `|0000⟩`。

## 五、与官方模拟器的兼容性声明

| 官方契约 | 扩展后状态 |
|----------|-----------|
| 7 条经典指令（`li/add/sub/addi/beq/bne/j`） | 语义、报错行为逐字不变 |
| `TinyRISCVEmulator` 类名与 `__init__` 签名 | 不变（仅新增量子字段） |
| `load_program` 解析（注释/标签/行内注释） | 不变（新增量子指令解析分支） |
| `set_register / get_register` | 不变 |
| `execute() -> Dict[str, int]`（非零寄存器） | 不变（新增量子执行分支） |
| `max_steps` 防死循环 | 不变 |
| `__main__` 经典自测 | 保留，`x3 == 16` 断言原样通过 |

## 六、编码示例（以下机器码为实现的实测输出，与 `encode_quantum/decode_quantum` 严格一致）

| 汇编 | 32 位机器码 | 解码回汇编 |
|------|-------------|-----------|
| `qinit` | `0x0000000B` | `qinit` |
| `qh q0` | `0x0000100B` | `qh q0` |
| `qcnot q0, q1` | `0x0000208B` | `qcnot q0, q1` |
| `qrx q1, 180` | `0x0B40308B` | `qrx q1, 180` |
| `qmeas q0, x2` | `0x0000410B` | `qmeas q0, x2` |

核算（以 `qcnot q0, q1` 与 `qrx q1, 180` 为例）：

```
qcnot q0, q1 : rs1=q0(0)<<15 | f3(010)<<12 | rd=q1(1)<<7 | 0x0B = 0x2000 | 0x80 | 0x0B = 0x0000208B
qrx   q1, 180: imm=180(0x0B4)<<20 | rs1(0)<<15 | f3(011)<<12 | rd=q1(1)<<7 | 0x0B
             = 0x0B400000 | 0x3000 | 0x80 | 0x0B = 0x0B40308B
```

## 七、端到端验证

```bash
# 1) 模拟器内置自测（经典回归 + Bell 态 + 机器码往返）
python3 starter_kit/riscv_emulator.py
#   期望输出：Tiny RISC-V 模拟器核心测试通过！ / 量子扩展自测通过：Bell 态 (|00>+|11>)/√2

# 2) Bonus 端到端测试（10 项，覆盖单门/纠缠/测量分布/混合程序/编码往返/L3 契约回归）
python3 tests/test_riscv_quantum_ext.py

# 3) L3 公开契约回归（确认扩展不破坏 15 分项）
python3 starter_kit/evaluator.py --level l3
```

预期结果示例（来自扩展实现的真实输出）：

- `qh q0` → 态矢 `[0.707, 0.707, 0, ...]`（`(|0⟩+|1⟩)/√2`）
- `qh q0; qcnot q0, q1` → Bell 态 `(|00⟩+|11⟩)/√2`，`amp[0]=amp[3]=0.707`
- Bell 态测量 8192 次 → 仅出现 `00`/`11`，各约 50%
- 混合程序 `li x1,1; qh q0; qcnot q0,q1; qmeas q1,x2; add x3,x1,x2` → `x3 ∈ {1,2}` 且与 `x2` 强关联

## 八、实现清单

| 产物 | 路径 | 说明 |
|------|------|------|
| 扩展模拟器 | `starter_kit/riscv_emulator.py` | fork 官方实现，+137 行量子扩展（编码/解码/门/测量/机器码） |
| 端到端测试 | `tests/test_riscv_quantum_ext.py` | 10 项自动化测试 |
| 本规格 | `docs/riscv_quantum_extension_spec.md` | 编码表 + 执行语义 + 兼容性声明 |
