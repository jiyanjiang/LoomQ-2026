# LoomQ 竞赛任务分析与实施计划备忘（2026-08-19）

> 用途：固化 2026-08-19 会话中确认的任务理解 + 下一步工作计划。
> 截止：2026-08-25 12:00（倒排 6 天）。

## 1. 任务本质（用户已确认 + 官方材料核实）

### L1 = 编译器工程（纯编程，与 LLM 无关）
- 官方原话（QUANTUM_101.md）：「这道题让你造的是'翻译器'，不是让你学物理。」
- 接口契约：
  ```python
  def transpile(qasm_str: str, target: str) -> str: ...   # 输入是 QASM！
  def run(qasm_str: str, target: str, shots: int) -> dict: ...
  ```
- 翻译方向：**QASM(2.0) → 三家平台各自 IR**，不是"任务描述→QASM"。

| 目标 | 输出方言 |
|---|---|
| `spinq` | 原样 QASM 2.0（SpinQit 原生吃） |
| `braket` | OpenQASM 3.0 |
| `originq` | OriginIR 文本（`QINIT`/`CNOT`/`MEASURE`…） |

- 评测输入全部是 QASM（公开+隐藏+变体），变体=同门集换皮的 QASM（不同比特数/相位参数/门序），与自然语言无关。
- 全部电路只使用 12 个标准门（白名单），见题面。
- "任务描述→QASM/电路"是 **L2** 的活（`agent_chat(prompt)`）。

### L2 = LLM 工程
- 接口：`def agent_chat(prompt: str) -> str: ...`
- 核心闭环：LLM 生成 QASM → **喂给自己写的 L1 翻译器自验** → 重试。
- L2 用 L1 当自验工具，两个 Level 咬合。

### 用户愿景备注（不抢跑）
- L1 的 `transpile` = 量子版 API 统一层（类比 AI 时代 OpenRouter）。
- 方向：综合性量子计算聚合平台 = 统一 API 层 + 摸清市场玩家 + 独立测评。
- 规划：先写 `docs/ROADMAP_QUANTUM_AGGREGATOR.md`（市场玩家清单 + 各真机测评表），**竞赛提交前不实施**。
- L3 调度层与愿景的关系：L3「经典层切分/调度/反馈」正是聚合平台的关键组件之一——统一 API 层不但要会翻译电路（L1），还要会编排「量子跑 + 经典处理 + 再喂回」的完整循环（L3）。竞赛 L3 是这套能力的编译器内核，平台愿景是它的产品化外延。

## 2. 现状盘点（已实现，勿重复劳动）

- `adapter.py`：`transpile` + `run`（三模拟器）+ `agent_chat`（L2 闭环，重试 3 次）**已实现**。
- 自测：21 个测试电路 × 3 后端 = 63/63 全 PASS，fidelity ≥ 0.97（`tests/test_suite_report.json`）。
- `riscv_emulator.py`（170 行）：TinyRISCVEmulator 已写好（li/add/sub/addi/beq/bne/j + 标签 + 死循环保护）。
- Web 工作台（5011 端口）+ `loomq_lib` pip 包 + PRD/SOP/教程/游戏文档。
- **未做**：L1 真机证据、人工分 evidence 填表、提交通道（`competition/config.json` 缺失、根目录未 git init）、L3 `compile_hybrid`。

## 3. 下一步工作计划（外部依赖优先）

### 阶段 A：L1 真机证据（10 分，最紧迫，唯一时间不可控环节）✅ 2026-08-20 全部完成
| 步骤 | 内容 | 谁 | 状态 |
|---|---|---|---|
| A1 | 注册量旋 SpinQ 云（spinq.cn）✅ 2026-08-19 完成（用户名已脱敏，微信登录） | 用户 | ✅ |
| A2 | 写真机提交脚本（bell + ghz3，各 8192 shots） | AI | ✅ scripts/spinq_sdk_{bellstate_gemini,ghz_triangulum}.py |
| A3 | 提交任务，记录 job ID + 运行时间（带时区） | 用户 | ✅ G-260820-0005 / S-260820-0001 |
| A4 | 取原始结果 JSON | 用户 | ✅ |
| A5 | 整理 → evidence/files/（qasm + result.json + info.json） | AI | ✅ |
| A6 | 填 evidence/README.md 的 L1 段（7 字段） | AI | ✅ 双平台已填 |
| A7（加分） | 本源悟空（+5 分）：注册 qcloud.originqc.com.cn + API Token + 提交 | 用户 | ✅ 838F... Bell（100%）/ 21F3... GHZ（99.93%） |

真机保真度（全部 8192 shots，selfcheck 绿）：SpinQ Bell 95.04% / GHZ 74.95%；本源 Bell 100% / GHZ 99.93%。
⚠️ 提交口径唯一 = 8192 shots（组织方要求，2026-08-20 统一）；旧 5000/web 1024 数据已归档，不再参与任何对比。

### 阶段 B：人工分 evidence 填表（与 A 并行）
- B1 L2 交互体验：启动命令 + 测试入口（web 5011）+ 3 个用户任务 + 截图
- B2 工程与产品化：构建启动命令 + 架构说明 + 目标用户 + 使用流程
- B3 新手引导与视觉叙事 Bonus（4 分）：零基础指南/概念解释/可视化/错误恢复
- ~~B0 web vs SDK 差异量化~~（原 LOG 遗留，2026-08-20 关闭：统一 8192 shots 后 1024 vs 5000 旧对比作废）
- 验收：evidence 三个 `[ ]` → `[x]`，可被工作人员干净环境复现

### 阶段 C：提交通道（硬性要求，两个坑）
- C1 创建缺失的 `competition/config.json`（`prepare_submission.py` 依赖它）
- C2 根目录 `git init` + fork + `origin` + push（目前连 git 仓库都不是）
- C3 跑 `prepare_submission.py --team-id <GitHub用户名>` 全绿
- C4 提 GitHub Issue（final-submission 模板）
- ⚠️ 绝不提交 api-key.txt / token / 个人隐私；归档包 < 100 MiB

### 阶段 D（待决策，可选）：L3 量子 RISC-V Bonus（8 分）
- 见下节详细解释。`compile_hybrid()` 现为 `NotImplementedError`，`submission.yaml` 标 `l3: false`。
- 建议：先跑完 A/B/C 再决策。

### 阶段 E：聚合平台愿景（记录，不抢跑）
- 写成 `docs/ROADMAP_QUANTUM_AGGREGATOR.md`。

## 4. L3 量子 RISC-V Bonus 是什么（详细）

### 4.1 用户理解（2026-08-19 确认）：L3 = 量子-经典调度层

```
任务 --> 经典计算机 --> 量子部分的任务 --> QASM --> 量子计算机 --> 测量结果 --> 经典计算机
```

这个理解正确。`compile_hybrid` 就是「经典计算机把任务切分、把量子部分打包成 QASM、并把测量结果的经典处理逻辑（RISC-V 汇编）编出来」这一环。

精确补充一点：**「切分」不是自动发生的，正是你的编译器干的**——输入是混合程序，输出是「量子 ops（喂芯片）+ 经典汇编（处理结果）」。且该循环可迭代多轮：测量结果回经典层 → 经典汇编执行判断 → 可能修改参数/再发起新的量子任务 → 再喂回量子层（变分算法 VQE/QAOA 的标准形态）。L3 竞赛只测其中一环的分支语义正确性。

### 4.2 官方定位

- 可选 Bonus：三项齐全且测试通过 = 8 分（evidence/README.md「自定义量子 RISC-V Bonus」）。
- 本质：**量子-经典混合编程编译器**——把「量子部分 + 经典控制流」的混合程序拆成：
  - `quantum_ops`：量子操作列表
  - `assembly`：经典控制流的 RISC-V 汇编字符串
- 接口：`compile_hybrid(hybrid_qasm_str) -> tuple[list, str]`

### 4.3 为什么设计 L3（现实意义）

量子芯片**永远不能独立干活**。真实流程永远是：经典电脑喂电路 → 芯片执行测量 → 结果回经典电脑 → 经典代码做判断（if/循环/反馈）→ 决定是否再跑一轮。这就是量子-经典混合编程，也是 VQE/QAOA 等实用算法（NISQ 时代）的标准形态。L3 = 实现中间那层经典控制的编译器。

为什么用 RISC-V：经典控制系统的嵌入式 CPU 用精简指令集，RISC-V 是开源标准——用它代表"通用经典指令"，而不是让选手发明一套。

### 4.4 公开测试契约（evaluator.py 原文，权威）

```python
source = """OPENQASM 2.0; qreg q[1]; creg c[1];
measure q[0] -> c[0];
classical { if (c[0] == 1) { r1 = 7; } else { r1 = 3; } }"""
quantum_ops, assembly = adapter.compile_hybrid(source)
# 验证：
for measured, expected in ((0, 3), (1, 7)):   # 测得0→期望3；测得1→期望7
    emulator = TinyRISCVEmulator()
    emulator.load_program(assembly)
    emulator.set_register("x10", measured)     # x10 = 测量结果（输入）
    if emulator.execute().get("x1", 0) != expected:   # x1 = 分支结果（输出）
        return FAIL
```

人话：`classical { if (c[0]==1) { r1=7 } else { r1=3 } }` → 若测得 1 则 x1=7，测得 0 则 x1=3。

从测试反推出的隐藏 ABI 约定（关键设计决策）：
- `x10` = 输入测量结果
- `x1` = 输出分支结果
- 量子部分照常解析成 ops 列表

### 4.5 已有资产（勿重复劳动）

- `riscv_emulator.py`（170 行）已写好且自带测试：32 寄存器 x0-x31（x0 恒 0）、指令集 `li/add/sub/addi/beq/bne/j`、标签跳转、死循环保护（1000 步）、自带自测（x3==16）。
- **缺的唯一一块**：`adapter.py` 的 `compile_hybrid()`（现为 `raise NotImplementedError`）。

### 4.6 交付三件套（evidence 必填，缺一不可 8 分）

1. **指令编码规格**（文档）：classical 块 → RISC-V 汇编的编码规范——寄存器分配、条件语句映射 beq/bne、变量 r1 对应哪个寄存器。
2. **模拟器扩展实现**（代码）：TinyRISCVEmulator 打底 + `compile_hybrid` 实现。
3. **端到端测试命令**：`python3 evaluator.py --level l3` 跑绿。

### 4.7 工作量与风险

- 核心 = 解析 QASM 的 `classical {...}` 块 → 发射 RISC-V 汇编（`li` + `beq` + 标签）。
- 公开测试只验证一个分支语义，但**隐藏变体**可能换寄存器名/常量/比较符（==/!=）→ 需写覆盖「寄存器赋值 + if/else」的通用迷你翻译器，不能只答一题。
- 纯本地、**零外部依赖**（不注册任何云）、预计 1-2 天（含规格文档）。
- 排序：在 A/B/C 之后；有余力就做，放弃不影响任何必得分。
