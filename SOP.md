# LoomQ SOP（Standard Operating Procedure）

> 版本：v1.3 · 更新：2026-08-21 · 适用范围：LoomQ 量子编程竞赛（QAIDAO/LoomQ-2026）
> 原则：**与官方评测容器严格对齐**；一切可复现、可复查、留痕。

---

## §0 协作铁律（最高优先级，任何场景不得违反）

1. **绝不用选择题/ABCD/多选项列表式提问**（含 ask_followup_question 等强制给答案的交互形式）。
   必须用**开放式自然语言**陈述我的判断与推荐方案，由用户以自由文本确认或否决。
2. 任何实施前先讨论方案，获得确认后才动手；每步完成即暂停回报，绝不擅自连跑。
3. 不自作主张推进方案、不擅自决定任务方向；方向性问题必须询问用户。
4. 所有检查/确认类工作，设计提示词发送 DeepSeek v4 pro 代劳，人只做少量最终确认；确认后写验收报告。

---

## §1 环境与 venv（本竞赛的技术环境约定）

| 项 | 值 |
|---|---|
| 评测容器 Python | **3.10**（官方 `starter_kit/Dockerfile` 首行 `FROM python:3.10-slim`） |
| 本机主力 Python | **3.10**（`/opt/homebrew/bin/python3.10`，brew `python@3.10`） |
| 专用 venv | `~/.venvs/loomq310/`（**绝不混用**其它项目的 3.12 venv） |
| 激活命令 | `source ~/.venvs/loomq310/bin/activate` |
| 验证 | `which python` 应指向 `~/.venvs/loomq310/bin/python`，版本 `3.10.x` |
| 依赖清单 | `starter_kit/requirements.txt`（**全部精确锁定 `==`**，评测不会替选手选版本） |

**为什么必须是 3.10**：
1. 官方评测容器就是 `python:3.10-slim`，本地与容器不一致会在评测时才暴露。
2. `spinqit` 只发布 cp38/cp39/cp310 wheel，本机 3.11/3.12 根本装不上。
3. `pyqpanda` / `amazon-braket-sdk` 在 3.10 上全部可跑。

**本机 macOS 26.2 的两个已知坑（已修复，见下方）**：
- pip ≥26 的 truststore 后端在 `mac_ver()` 解析失败时崩溃 → venv 内锁定 pip 24.3.1。
- 3.10 的 `pyexpat` 链接系统 libexpat 缺符号 → `DYLD_LIBRARY_PATH` 指向 brew expat 2.8.1。

---

## §1.1 已验证的依赖版本组合（2026-08-18 实测全通过）

| 包 | 版本 | 说明 |
|---|---|---|
| `spinqit` | `0.2.4` | L1 后端 spinq_taurus；要求 `antlr4-python3-runtime==4.9.2` |
| `pyqpanda` | `3.8.5` | L1 后端 originq_local_simulator |
| `amazon-braket-sdk` | `1.95.0` | L1 后端 braket_local_simulator |
| `amazon-braket-default-simulator` | `1.27.0` | 必须 1.27.0！≥1.28 会升级 antlr 到 4.13.2 与 spinqit 冲突 |
| `antlr4-python3-runtime` | `4.9.2` | spinqit 硬性要求，与 default-simulator 1.27.0 兼容 |

> ⚠️ **版本组合铁律**：三包必须成套装。`amazon-braket-sdk` 不能升到 1.100.0（其运行时依赖的 `VerbatimBoxDelimiter` 需 default-simulator ≥1.28，而 ≥1.28 又会把 antlr 抬到 4.13.2 与 spinqit 冲突）。本组合是三方兼容的交集。

---

## §1.5 本地 HTTP 展示服务（查看文档/表格用）

| 项 | 值 |
|---|---|
| 端口 | **5010**（LoomQ 专属；5001=loomsci、5005=STOP 词编纂，绝不占用） |
| 启动 | `cd /Users/jiyanjiang/Downloads/LoomQ && python3.12 -m http.server 5010` |
| 查看 | http://localhost:5010/docs/gate_mapping/gate_mapping.html |
| 说明 | 纯静态文件服务，仅本地查看用；文档更新后刷新浏览器即可 |

> 📌 自检结论（2026-08-19）：此处的 `/Users/...` 绝对路径是**文档展示命令的合理例外**（纯本地 HTTP 服务，不进评测容器），其余源码一律用 `Path(__file__).resolve()`，无硬编码用户路径。

---

## §2 本地自检（发布前必跑）

```bash
source ~/.venvs/loomq310/bin/activate
cd starter_kit
python evaluator.py --level l1 --target spinq,originq,braket --json-out report.json
# 期望：passed=6 failed=0，exit=0
```

- `transpile()` 输出规范子集见 `starter_kit/target_ir_contract.md`。
- braket 的 `run()` 内部把 `include "stdgates.inc"` 替换为本地 `braket_gates.inc` 绝对路径（评测器会解析 `transpile()` 返回值，不受影响）。

---

## §3 提交物

- `starter_kit/adapter.py`：实现 `transpile()` / `run()`（L1）+ `agent_chat()`（L2）+ `compile_hybrid()`（L3，L555）。
- `starter_kit/submission.yaml`：`l1: true`、`l2: true`、**`l3: true`**（L1/L2 2026-08-18 生效；L3 2026-08-21 申报，evidence 三项已填、评测全过）。
- `starter_kit/requirements.txt`：精确锁定版本。
- 截止：**2026-08-25 12:00 UTC+8**。提交流程见 `starter_kit/README.md`。

---

## §3.5 L2（agent_chat + 自验闭环，2026-08-18 已实现）

- 契约：`agent_chat(prompt) -> str` 返回含 OpenQASM 2.0 的文本；读 `LOOMQ_LLM_*` 环境变量。
- 闭环：LLM 生成 QASM → 三后端本地自验（`_validate_and_run`）→ 失败带原因重试（最多 3 次）。
- 本地调试：`export LOOMQ_LLM_BASE_URL=https://api.deepseek.com; export LOOMQ_LLM_API_KEY=<config.yaml 里 key>; export LOOMQ_LLM_MODEL=deepseek-v4-flash`（**与正式评测同模型**，已验证 QFT-4/参数门生成质量良好；v4-pro 也可用但结果可能不同）。
- 已验证：公开 GHZ 用例 PASS；QFT-4 生成正确且三后端分布均匀。
- 提示词：`prompts/l2_qasm_generator_v1.yaml`（独立可替换模块）。
- 测试集扩展：QFT-5/Grover-3/Toffoli-3 已加，20 用例 × 3 后端 60/60 PASS。

---

## §3.6 内容/呈现脱耦铁律（2026-08-19 全面自检固化）

- **分层模板化**：题库/游戏文案 = `web/game_content/*.json`；词典 = `web/qc_dict.py`（9 字段唯一权威源）；课程/UI 文案 = `web/content.py`；主题色 = `web/static/js/colors.js`；标准组件 = `web/static/js/components/*`。呈现层（HTML/CSS/JS 渲染）只负责视觉，**禁 hardcode 内容**；改内容不动代码。
- **措辞命名空间**：竞赛面向大众，统一"粒子（自旋-1/2）"图像（施温格积木/袜子/课程全用），**禁用**"光强/光透过/概率"等易误导词（光偏振需相位、Born 规则太抽象）。`web/selfcheck.sh` 含术语黑名单（从词典 aliases 动态生成）。
- **已知缺口（待排期）**：`schwinger.js` 的 LEVELS 关卡定义仍内嵌 JS，可迁移到 `data/` JS/JSON 加载；不阻塞当前提交。

---

## §3.7 L3（量子-经典混合编译，2026-08-21 申报）

- 契约：`compile_hybrid(hybrid_qasm) -> (quantum_ops, assembly)`；`assembly` 在 `TinyRISCVEmulator` 执行，**x10=测量值入口、x1=分支结果出口**。
- 模拟器：`starter_kit/riscv_emulator.py`（7 条经典指令 li/add/sub/addi/beq/bne/j + 量子扩展 5 条 qinit/qh/qcnot/qrx/qmeas，x0 恒 0，max_steps 防死循环，4-qubit 态矢量）。
- 翻译器：`starter_kit/adapter.py::compile_hybrid`（L555）：`==`→beq、`!=`→bne、多 if 串联 `THEN_n/END_n` 编号递增、无 else 省略 else 段、`rN=rM`→`add xN,xM,x0`、比较常量装载临时寄存器 x11 起避让。
- 规格：`docs/l3_riscv_encoding_spec.md`（2026-08-20 定稿：指令集/变量映射/分支语义/隐藏变体覆盖矩阵）。
- 自验：`python evaluator.py --level l3` 公开契约 1/1 PASS；隐藏变体矩阵 11/11 全过（==0/==1/!=、换常量、多 if、无 else、寄存器赋值）。
- evidence：`starter_kit/evidence/README.md` L3 段三项已填；`submission.yaml` `l3: true`。

---

## §3.8 Bonus +8 量子 RISC-V 扩展（2026-08-21 补做）

- 目标：满足赛题 Bonus +8「fork `riscv_emulator.py` 增加指令支持」三件套（编码规格 + 扩展实现 + 端到端测试）。
- 编码：RISC-V **CUSTOM-0**（opcode=0x0B）I-type 空间，funct3 区分 5 条量子指令：`qinit`(000)/`qh`(001)/`qcnot`(010)/`qrx`(011)/`qmeas`(100)。
- 执行模型：4-qubit 态矢量（q0 最低位，little-endian，初始 |0000>）；`qh`/`qcnot`/`qrx` 矩阵演化；`qmeas` Born 采样 + 投影坍缩并写回经典寄存器，可与经典指令交错执行；`load_program` 重载重置态矢。
- 规格：`docs/riscv_quantum_extension_spec.md`（2026-08-21 定稿：编码布局/指令表/执行语义/兼容性声明/实测机器码示例）。
- 扩展实现：`starter_kit/riscv_emulator.py` 新增 `encode_quantum`/`decode_quantum`/`machine_code`/`run_machine_code`/`get_statevector`/`set_seed`，量子指令统一经 32 位机器码路径执行（非文本特判）。
- 端到端测试：`tests/test_riscv_quantum_ext.py` 16 项全过（官方回归/单门态矢/Bell+GHZ/含参门/测量坍缩一致/分布 8192 次仅 00/11/混合程序/编码往返/机器码等价/L3 契约回归）。
- 自验：`python3 starter_kit/riscv_emulator.py`（经典回归 + Bell 态自测）；`python3 tests/test_riscv_quantum_ext.py` 16/16；`python3 starter_kit/evaluator.py --level all` 6/6（L3 契约未破坏）；L1 套件 21 用例 × 3 后端 63/63。
- evidence：`starter_kit/evidence/README.md` Bonus 段已重写指向量子扩展三件套。

---

## §4 对齐基准（尺子）与门映射结论

**尺子 = OpenQASM 2.0 官方标准门库（qelib1.inc）**，机器实现 `tests/qasm_semantics.py`（numpy 态矢量模拟，不依赖厂商 SDK）。详细规格：`docs/gate_mapping/alignment_spec.md`。

**12 门 × 3 后端对齐度实测（2026-08-18，Hellinger ≥0.97 = OK）：**

| 后端 | 状态 |
|---|---|
| spinq | ✅ 12/12 完全对齐 |
| originq | ✅ 12/12 完全对齐 |
| braket | ✅ **12/12**（s/t→rz 展开后；原 8/12） |

**braket s/t 实测规律（braket_notes.md）**：
- braket 1.27.0 本地模拟器 `pow(1/2) @ z` 幂次语法失效，s/sdg/t/tdg **退化为恒等门**（P2 探针 + QPT 反推双证）。
- 适配：braket 路径把 s→rz(π/2)、sdg→rz(-π/2)、t→rz(π/4)、tdg→rz(-π/4)（rz 与 u1 只差全局相位，分布相同）。
- braket 无 u1 门，展开目标选 rz。

**铁律**：
1. 本地自检以 spinq/originq 为准（已全对齐 QASM2 标准）。
2. braket 的 s/t 偏差是**本地模拟器（braket_gates.inc）实现问题**，不是翻译错误。**transpile/run 双模式分离**（`_qasm2_to_qasm3(local)`）：transpile 输出契约格式（`stdgates.inc` + 标准 s/t，供评测器语义模拟），run 内部本地模式（braket_gates.inc 绝对路径 + s/t→rz 展开，供本地自检）。绝不允许 transpile 输出含本机绝对路径（评测容器会 FileNotFoundError）。
3. 位序归一化（key 最右 = c[0]）：originq 原生正确，spinq/braket 需反转，adapter 的 `run()` 统一层已处理。

**门映射结论（12 门 × 3 后端）**：完整表格见 `docs/gate_mapping/gate_mapping.md`（HTML 可视化见 §1.5 端口 5010）。

完整表格见 `docs/gate_mapping/gate_mapping.md`（HTML 可视化见 §1.5 端口 5010）。要点：

| 后端 | transpile 输出 | 门名改动 |
|---|---|---|
| spinq | QASM 2.0 | 12 门全同名，**零映射** |
| braket | QASM 3 | 5 项必改：`cx→cnot, sdg→si, tdg→ti, cu1→cphaseshift, ccx→ccnot` |
| originq | OriginIR | 契约门名：`sdg→SDAG, tdg→TDAG, cx→CNOT, cu1→CU1, ccx→TOFFOLI`；**参数门用第二格式** `RZ q[k],(θ)` |

- originq 的 `run()` 走 QASM 2.0 路径（`convert_qasm_string_to_qprog`），12 门实测全 OK，**零映射**。
- 坑：pyqpanda 3.8.5 的 OriginIR 解析器不认 `SDAG/TDAG`（契约允许但 SDK bug）、不认 `RZ(θ)` 第一格式；braket 本地无 `stdgates.inc`，须用 `braket_gates.inc` 绝对路径。
- adapter 现状：braket 仅做了 cx→cnot，originq 仅做了 cx→CNOT；**其余门名映射待补（第 1 步进行中）**。

---

## §5 提交与发布流程（2026-08-21 首次参赛提交后固化）

**仓库**：fork 自官方 `QAIDAO/LoomQ-2026`，推送到 `git@github.com:jiyanjiang/LoomQ-2026.git`（提交即参赛，官方 `.github/workflows/submission-intake.yml` 收件）。

**历史结构**（方案 A 融合后，勿再改）：
- `1071f71`（官方基线，52 文件）+ `4fe20a0`（参赛实现，227 文件，2026-08-21 已推）
- 本地备份 tag：`backup-local-start-0abc19a` / `backup-local-final-2b5a957`（仅回滚用，永不删除）

### 5.1 发布前自检（每次 push 前必跑）

```bash
source ~/.venvs/loomq310/bin/activate
# ① 官方 evaluator 契约（公开 6 项：L1 三平台 bell/ghz3 + L2 public-ghz + L3 public-branch）
cd starter_kit && python evaluator.py --level all --target spinq,originq,braket && cd ..
# ② 本地扩展测试套件（21 用例 × 3 后端 = 63 项）
python tests/run_test_suite.py   # 期望 63/63 PASS
# ③ 敏感文件复查（必须全被忽略）
git check-ignore config.yaml api-key.txt spinq.txt.pub config/machines.yaml data/onboarding_imgs/preview.html
# ④ 官方文件完整性（不得有缺失；空输出=OK）
git ls-tree -r --name-only origin/main | while read f; do [ -e "$f" ] || echo "缺失: $f"; done
```

### 5.2 提交步骤（参赛后日常迭代，直接推即可，无需再融合）

```bash
cd /Users/jiyanjiang/Downloads/LoomQ
git status -sb                       # 先看改了什么
git diff --stat                      # 变更概览
git add -A
git diff --cached --name-only | grep -iE "api.?key|machines|spinq.txt|\.epub|quantum_book|PPT_PDF|preview\.html"
# ↑ 有输出=有敏感文件误入，立刻 git reset 排查；空=安全
git commit -m "feat|fix|docs: 一句话描述"
git push                             # 已跟踪 origin/main，直接推
git log --oneline -3                 # 确认提交已落地
```

**铁律**：
1. 改代码 → 本地自检（§5.1）→ 提交 → push，每步之间不连跑，先回报再继续。
2. 提交信息遵循 Conventional Commits（`feat:`/`fix:`/`docs:`/`chore:`）。
3. 绝不 `push --force`（fork 参赛库禁止改写历史）；如需回滚，用备份 tag 重建新提交，不改写已推送历史。
4. 截止 2026-08-25 12:00 UTC+8；截止前一切 push 均自动进入收件。

### 5.3 评分对照（2026-08-21 自检口径，满分 100+12）

| 项目 | 分数 | 当前状态 | 预估 |
|---|---|---|---|
| L1 语义等价 | 35 | 三平台 12 门对齐，公开+本地 63 项全过 | 30-35 |
| L1 真机 | 10 | 量旋双平台 + 本源双任务，evidence 已填 | 10 |
| L2 客观 | 20 | agent_chat 自验闭环，公开 GHZ PASS；隐藏变体未知 | 12-18 |
| L2 交互 | 10 | Web 工作台 3 任务 4 截图已填（客观≥12 才计入） | 0-10 |
| L3 混合编译 | 15 | 公开 1/1 + 隐藏矩阵 11/11 | 15 |
| 工程与产品化 | 10 | README/USAGE/架构/一键启动齐全 | 8-10 |
| Bonus 新手引导 | 4 | 4 项全填 | 3-4 |
| Bonus 自定义 RISC-V | 8 | 量子扩展三件套齐：fork 模拟器 +5 量子指令（CUSTOM-0 编码）+ 规格 + 端到端测试 16 项 | 8 |
| **合计** | **100+12** | | **86-110** |

**风险点（2026-08-21 已解除）**：官方 Bonus +8 要求"对官方模拟器的扩展实现（fork `riscv_emulator.py` 增加指令支持）"。已于 2026-08-21 补做：新增 5 条量子指令 `qinit/qh/qcnot/qrx/qmeas`（RISC-V CUSTOM-0 opcode=0x0B 编码），经典 7 条指令与 `load_program/set_register/get_register/execute` 接口逐字不变；规格 `docs/riscv_quantum_extension_spec.md`；端到端测试 `tests/test_riscv_quantum_ext.py` 16/16 PASS；`evaluator --level all` 6/6、L1 套件 63/63 回归通过。详见 §3.8。

### 5.4 收尾清单（参赛后可选改进，非必做）

- [x] 补做自定义 RISC-V 扩展指令（+8，2026-08-21 完成，见 §3.8/§5.3）
- [ ] 官方隐藏电路（GHZ-5/QFT-4/Grover-3/Random×3）本地全覆盖验证（tests 已含等价电路，可再加 3 个 Random 变体）
- [ ] L2 隐藏 prompt 变体本地自测（模拟正式评测的 12 case 抽样）
- [ ] web 展示层完善（schwinger.js LEVELS 迁移到 data/ JSON）
- [ ] 赛后复盘：收集评测反馈，更新 gate_mapping 文档
