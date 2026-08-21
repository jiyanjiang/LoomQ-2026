# L3 RISC-V 编码规格（`compile_hybrid` 设计文档）

> 2026-08-20 定稿。范围：LoomQ L3 量子-经典混合编程（8 分 Bonus）的经典侧翻译契约。
> 权威契约来源：`starter_kit/evaluator.py::evaluate_l3()` + `starter_kit/riscv_emulator.py`。

---

## 1. 目标与边界

L3 只测「一个环节」：`classical {}` 块的分支语义正确性。
给定含经典块的混合 QASM，`adapter.compile_hybrid(source)` 返回：

```
(quantum_ops: List[str], assembly: str)
```

- `quantum_ops`：量子部分门操作列表（本实现=逐条 QASM 门行）。
- `assembly`：classical 块翻译出的 RISC-V 汇编文本（非空即有效）。

评测方式（公开契约）：测量结果先 `set_register("x10", measured)`，执行汇编后
分支结果必须落在 `x1`（对应源码 `r1`）。即 **x10=测量入口、xN=变量出口**。

### 不实现（超出 L3 契约，模拟器也不支持）
- 完整 VQE 变分循环（梯度在经典 Python 层算，不在 RISC-V 层）。
- 浮点 / 乘除 / 内存指令（lw/sw）——模拟器指令集只有 7 条，无这些能力。
- 循环结构（模拟器支持 `j`/`bne` 回跳，但公开测试不测；`max_steps=1000` 防死循环）。

---

## 2. 模拟器指令集（TinyRISCVEmulator，全部 7 条）

| 指令 | 语义 | 说明 |
|---|---|---|
| `li rd, imm` | `rd = imm` | 立即数装载（`int(imm)`） |
| `add rd, rs1, rs2` | `rd = rs1 + rs2` | 三寄存器算术 |
| `sub rd, rs1, rs2` | `rd = rs1 - rs2` | 三寄存器算术 |
| `addi rd, rs1, imm` | `rd = rs1 + imm` | 立即数加法 |
| `beq rs1, rs2, label` | `if rs1 == rs2: pc = label` | 相等分支 |
| `bne rs1, rs2, label` | `if rs1 != rs2: pc = label` | 不等分支 |
| `j label` | `pc = label` | 无条件跳转 |

执行模型（`riscv_emulator.py` 事实）：
- 32 个寄存器 `x0-x31`，**x0 恒为 0**（`set_register` 对 x0 忽略）。
- 标签：`LABEL:`（独占行）或 `LABEL: li x1, 10`（同行）。
- 注释：`#` 或 `;` 开头整行、行内 `#` 之后；空行跳过。
- 参数分隔：逗号可有可无（内部 `replace(",", " ")`）。
- 分支未命中 → `pc+1` 顺序执行；命中 → `pc = 标签行号`。
- `execute()` 返回**非零**寄存器的 `{xN: val}` 字典（x0 恒 0 不会出现）。

---

## 3. 变量映射规则

| 源码实体 | 目标寄存器 | 说明 |
|---|---|---|
| `c[i]`（测量结果） | `x10` | 评测方预置测量值 |
| `rN`（经典变量） | `xN` | `r1 → x1`（公开契约断言出口） |
| 比较常量 `K` | 临时寄存器 `x11` 起 | 逐块递增，避开目标寄存器与 x10 |

临时寄存器分配：从 `x11` 开始，若与「目标寄存器集合 ∪ {10}」冲突则递增跳过，
保证 `li` 装载比较常量不会踩到变量/测量结果。

---

## 4. 分支语义翻译（核心）

```
classical { if (c[i] == K) { rA = V1; } else { rB = V2; } }
```

翻译为：

```asm
li  xT, K          # xT = 临时寄存器（x11 起）
beq x10, xT, THEN  # 测量结果 == K → 走 then
li  xB, V2         # else 分支（fall-through）
j   END
THEN:
li  xA, V1         # if 分支
END:
```

要点：
- `==` → `beq`；`!=` → `bne`。
- if 分支跳转前置，else 分支自然落序 + `j END` 跳过 then。
- 无 else 时省略 else 段（else 分支为空，`j END` 直接收尾）。
- 多 if 块：标签与临时寄存器按 `THEN_n / END_n` 编号递增，互不干扰。
- 赋值为数字 → `li`；赋值为另一变量 `rN = rM` → `add xN, xM, x0`。

### 公开测试样例（evaluator.py 原文）

```
OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1];
measure q[0] -> c[0];
classical { if (c[0] == 1) { r1 = 7; } else { r1 = 3; } }
```

预期汇编（可运行于 TinyRISCVEmulator）：

```asm
# L3: classical → RISC-V
li x11, 1
beq x10, x11, L3_THEN_0
li x1, 3
j L3_END_0
L3_THEN_0:
li x1, 7
L3_END_0:
```

验证：`x10=0` → beq 不命中 → `x1=3` ✓；`x10=1` → 跳 THEN → `x1=7` ✓。

---

## 5. 隐藏变体覆盖矩阵（自测基准）

| 变体 | 翻译点 | 覆盖手段 |
|---|---|---|
| 换变量名（r2/r3…） | `rN → xN` 直映 | 任意 rN 合法 |
| 换常量（`== 0` / `== 42`） | `li xT, K` 通吃整数 | K 任意 |
| 换比较符（`!=`） | `bne` | 反向跳转 |
| 多 if 串联 | `THEN_n/END_n` 编号递增 | 逐块独立 |
| else 缺省 | 省 else 段 | 单分支 |
| 多测量位 `c[1]` | 语法通用（i 不参与语义，评测只喂 x10） | 匹配 `c[\d+]` |
| 寄存器赋值 `r1 = r2` | `add x1, x2, x0` | 值解析分支 |

---

## 6. 实现约束

- `compile_hybrid` 必须是通用迷你翻译器，**不许只答公开那一题**。
- 量子部分不因 classical 块而改动：剥离 `classical{}` 后按原 QASM 门行输出。
- 解析失败时抛 `ValueError`（带原因），由评测方兜底 FAIL——不吞错。
- 汇编输出含 `#` 注释行不影响模拟器（其忽略 `#`）。

---

## 7. 验证命令

```bash
python3 starter_kit/evaluator.py --level l3        # 公开契约（1 项）
# 隐藏变体自测：见 scripts/ 临时测试或内联 python -c（5 号矩阵逐项）
```
