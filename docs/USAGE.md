# LoomQ 使用帮助

> 版本：v1.0 · 更新：2026-08-18
> 面向：参赛者本人（验证/调试）、未来 Web 界面用户（教育/科普）

---

## 一、这是什么

LoomQ 是一个**量子电路工作台**，核心能力：

1. **三后端执行**：同一段 OpenQASM 2.0 电路，可分别在 spinq（量旋）、originq（本源）、braket（AWS）三个本地模拟器上运行
2. **对齐尺子**：内置 qelib1.inc 标准语义模拟器，任何电路都能算出"正确参考分布"
3. **验证闭环**：生成的电路自动与参考分布比对（Hellinger ≥ 0.97），错了自动报原因
4. **电路库**：内置 21 个标准电路（Bell/GHZ/QFT/Grover/W/Toffoli…），一键调用

---

## 二、快速开始

### 环境要求
- Python 3.10（`~/.venvs/loomq310` 专用 venv）
- 依赖：`loomq_lib` 包（已 pip install -e 安装）

### 激活环境
```bash
source ~/.venvs/loomq310/bin/activate
```

---

## 三、日常用法

### 1. 跑一个标准电路（三后端）
```python
from loomq_lib import get_qasm, run_circuit, verify_all_targets

# 取 GHZ-3 电路
qasm = get_qasm("a01_ghz3")

# 单后端跑（带 fidelity 验证）
r = run_circuit(qasm, "spinq", shots=8192)
print(r["counts"])        # 实测 counts
print(r["reference"])     # 参考分布
print(r["fidelity"])      # 保真度
print(r["passed"])        # 是否达标

# 三后端批量跑
v = verify_all_targets(qasm)
print(v["all_pass"])
```

### 2. 跑自定义电路
```python
from loomq_lib import run_circuit, validate_qasm

qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;"""

ok, err = validate_qasm(qasm)   # 先校验
if ok:
    r = run_circuit(qasm, "originq")
    print(r)
```

### 3. 列出电路库
```python
from loomq_lib import list_circuits
for c in list_circuits():
    print(c["id"], c["kind"], c["description"])
```

### 4. L2 自然语言生成电路（需 API key）
```bash
export LOOMQ_LLM_BASE_URL=https://api.deepseek.com
export LOOMQ_LLM_API_KEY=<你的 key>
export LOOMQ_LLM_MODEL=deepseek-v4-flash
```
```python
from starter_kit.adapter import agent_chat
qasm = agent_chat("生成 5 比特 GHZ 态并全测量")
print(qasm)
```

### 5. 命令行自检
```bash
cd /Users/jiyanjiang/Downloads/LoomQ/starter_kit
python evaluator.py --level l1 --target spinq,originq,braket   # L1 6/6
python evaluator.py --level l2                                 # L2 1/1

# 全量 21 电路 × 3 后端
python /Users/jiyanjiang/Downloads/LoomQ/tests/run_test_suite.py
```

---

## 四、电路库（21 个）

> 别怕，这里不用懂量子力学。下面的讲解用大白话，把每个门/算法当成"玩具"来看。
> 想亲手玩？在 Web 界面点一下电路，三后端跑出来给你看结果。

### 4.1 十二个门（12 个，g01-g12）

**先懂两件事就够了：**
- 一个量子比特就像一枚**旋转中的硬币**——它可以是"正面朝上"（记作 |0⟩）、"反面朝上"（|1⟩），也可以是**悬在半空没落地**的叠加态。
- 测量 = **让硬币落地**。落地后只有两个结果：正面或反面，概率由叠加态决定。

| ID | 门 | 通俗理解 | 效果 |
|---|---|---|---|
| g01_x | **X** | 拨动开关 | 把 |0⟩ 变成 |1⟩，|1⟩ 变成 |0⟩。像反转硬币 |
| g02_h | **H** | 抛硬币 | 把确定的 |0⟩ 变成"悬空"态，测量 50/50。量子计算的起手式 |
| g03_s | **S** | 涂色（1/4 圈） | 不给硬币翻面，只给"反面"涂一种颜色。测量看不到变化，但干涉时起作用 |
| g04_sdg | **S†** | 涂色（反向 1/4 圈） | S 的反向涂色，用来抵消 S |
| g05_t | **T** | 涂色（1/8 圈） | 比 S 更细的涂色。S 和 T 合起来能涂出任意颜色（相位） |
| g06_tdg | **T†** | 涂色（反向 1/8 圈） | T 的反向，抵消用 |
| g07_rz | **RZ(θ)** | 任意角度旋钮 | 给"反面"涂上任意角度（θ）的颜色。S/T 只是它的特例 |
| g08_ry | **RY(θ)** | 任意角度翻硬币 | 按 θ 控制硬币悬空的角度：0° 不变、180° 全翻、90° 就 50/50 |
| g09_cx | **CX** | 联动开关 | 控制位是 1 才翻转目标位。**制造纠缠的核心**：两枚硬币从此"永远同面" |
| g10_cu1 | **CU1(θ)** | 受控涂色 | 控制位是 1 才给目标位涂色。QFT 全靠它 |
| g11_swap | **SWAP** | 换座位 | 两枚硬币交换位置。布线常用 |
| g12_ccx | **CCX** | 双开关 | 两个控制位都是 1 才翻转目标位。有了它 + H，理论上能做任何量子计算 |

**一句话记忆**：X 翻面、H 抛起、S/T/RZ 涂色、RY 定角度、CX 联动、CCX 双联动、SWAP 换座、CU1 受控涂色。

### 4.2 九个算法（9 个，a01-a09）

| ID | 电路 | 通俗理解 | 为什么有意思 |
|---|---|---|---|
| a01_ghz3 | **GHZ-3** | 三枚硬币永远同面 | 测一个就知道另外两个。三比特纠缠的"教科书案例" |
| a02_cat4 | **猫态-4** | 四枚硬币永远同面 | 薛定谔的猫从 1 只变 4 只。纠缠规模扩大 |
| a03_qft4 | **QFT-4** | 量子版傅里叶变换 | 把"频率"翻译成"位置"。很多算法的地基，考的就是相位转译精度 |
| a04_grover2 | **Grover-2** | 在 4 个抽屉里找目标 | 经典要找 4 次，量子 1 次就放大出答案。量子加速的招牌 |
| a05_teleport3 | **隐形传态** | 量子传真机 | 不传送物体，传送"状态"。用纠缠当信道 |
| a06_qft5 | **QFT-5** | QFT 升级到 5 比特 | 32 个状态均匀分布，测你对大电路的转译能力 |
| a07_grover3 | **Grover-3** | 8 个抽屉找目标 | 一次迭代后目标概率放大到 78%，"放大答案"的直观感受 |
| a08_toffoli3 | **Toffoli-3** | 双开关门 | 确定性的 111，最简单也最可靠的验证 |
| a09_wstate3 | **W 态** | 恰好一盏灯亮 | 三枚硬币恰好一枚正面，且无法拆开看。另一种纠缠，和 GHZ 不同家族 |

**算法 vs 门的关系**：门是"零件"（12 个），算法是"拼出来的机器"（9 台）。评测电路就是从这些机器里抽——你不需要懂每台机器为什么这样工作，只需保证每个零件被忠实翻译。

---

## 五、常见问题

**Q: 三后端结果为什么 fidelity 不是 1.0？**
A: 采样噪声。8192 shots 下理论分布是精确的，实测分布有 ±1% 涨落，fidelity ≥ 0.97 即视为正确。

**Q: braket 后端为什么慢？**
A: braket 本地模拟器解析 OpenQASM 3，有额外转换开销。spinq/originq 直接吃 QASM 2，更快。

**Q: 能上真机吗？**
A: 当前版本用本地模拟器。真机（spinq_cloud/originq_wukong/braket_cloud）需平台账号，API 已预留（backend_capabilities.json）。

---

## 六、目录结构

```
LoomQ/
├── loomq_lib/            # pip 可装工具包（尺子+三后端+电路库）
│   └── loomq_lib/
│       ├── semantics.py  # 尺子（qelib1.inc 语义模拟）
│       ├── backends.py   # 三后端执行
│       ├── circuits.py   # 21 电路库
│       └── runner.py     # 统一执行入口
├── starter_kit/          # 竞赛提交物（adapter/evaluator）
├── tests/                # 测试套件（自检/对齐/探针）
├── docs/                 # 文档
└── prompts/              # LLM 提示词（可替换模块）
```
