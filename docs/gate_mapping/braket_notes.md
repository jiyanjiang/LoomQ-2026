# braket 本地模拟器实测笔记（1.27.0）

> 更新：2026-08-18 · 环境：loomq310 venv（amazon-braket-sdk 1.95.0 + default-simulator 1.27.0）
> 主题：braket 本地模拟器的**实测行为**（不是文档），以及我们对它的适配。

---

## 一、核心发现：s/sdg/t/tdg 退化为恒等门

braket 本地模拟器的 `braket_gates.inc` 里定义：
```qasm
gate s a { pow(1/2) @ z a; }
gate t a { pow(1/2) @ s a; }
```

但**实测**这些门**完全未生效**（退化为恒等门 I）。三层证据：

### 证据 1：P2 判别探针（数学决定性）
`h s s h`：若 s²=Z（任何有效 S 门），`hZh=X` → 输出 |1⟩ 100%；实测 braket 输出 **|0⟩ 100%** → s² 表现为 I，s 只能是比例恒等门。
同理 `h sdg² h`、`h t⁴ h`（T⁴=Z）均输出 |0⟩ 100% → sdg/t/tdg 同样恒等。

### 证据 2：QPT 矩阵反推（tests/qpt_braket_s.py）
9 组实验（3 输入态 × 3 测量基，输入态/测量基全部用已验证的 h/x/rz 构造）：
候选矩阵残差：**I=0.498 最小**，Sdg=0.505，T=0.995，S=1.49，Z=1.50。
结合 P2（s²≠Z 排除 S/Sdg），s 门 = 恒等门 I（或 ±iI）。

### 证据 3：H 夹门探针
`h s h`、`h t h`、`h sdg h`、`h tdg h` 全部输出单态 100%（有效相位门必为混合分布）。

### 机理推断
braket 本地模拟器对 OpenQASM 3 的 `pow(1/2) @ gate` 幂次语法**解析/执行失败**，门未被施加。这是本地模拟器实现缺陷，不是我们的翻译错误。

---

## 二、适配：s/t → rz 展开

**正确性依据**：QASM2 标准（qelib1.inc）中 `s = u1(π/2)`、`rz(φ) = u1(φ)`，故 `s ≡ rz(π/2)`（只差全局相位，测量分布相同，gate_identities.md §2 确认）。

**展开映射**（adapter `_qasm2_to_qasm3` 中实现）：
| 门 | 展开 |
|---|---|
| `s` | `rz(pi/2)` |
| `sdg` | `rz(-pi/2)` |
| `t` | `rz(pi/4)` |
| `tdg` | `rz(-pi/4)` |

**效果**：braket 对齐度从 8/12 → **12/12**（s: 0.459→0.997, sdg: 0.459→0.994, t: 0.724→0.998, tdg: 0.724→0.999）。

**注意**：braket 没有 `u1` 门（实测 "Gate u1 is not defined"），故展开目标选 `rz` 而非 `u1`。

---

## 三、transpile 输出策略（已定：双模式分离）

**最终决策（2026-08-18）**：transpile 与 run 分离，各用各的输出。

| 函数 | 模式 | include | s/t 处理 |
|---|---|---|---|
| `transpile()` | 契约模式 `local=False` | `"stdgates.inc"`（标准库名） | **保持标准 s/t**（评测器按契约语义模拟） |
| `run()` 内部 | 本地模式 `local=True` | `braket_gates.inc`（绝对路径） | **展开为 rz**（绕开本地模拟器 pow 缺失 bug） |

**关键原因**：transpile 输出若含本机绝对路径（`/Users/jiyanjiang/.../braket_gates.inc`），评测容器中必然 FileNotFoundError——**绝对路径 include 是比 s/t 展开更严重的隐患**。双模式分离同时解决两件事：
1. transpile 输出干净契约格式（无本机路径、标准门名）→ 评测器可解析
2. run 内部用本地适配（braket_gates.inc + rz 展开）→ 本地模拟器结果正确

**实施**：`_qasm2_to_qasm3(qasm2, local: bool)` 一个函数两模式；`transpile` 传 `local=False`，`_run_braket` 传 `local=True`。
**验证**：对齐度矩阵三后端 12/12 OK；L1 公开回归 6/6 PASS。

---

## 四、可复现

- 探针：`tests/braket_s_probe.py` → `tests/braket_s_probe_report.json`
- QPT：`tests/qpt_braket_s.py`
- 对齐矩阵：`tests/alignment_check.py` → `tests/alignment_report.json`
- 依赖：amazon-braket-sdk 1.95.0 + default-simulator 1.27.0（loomq310 venv，Python 3.10）
