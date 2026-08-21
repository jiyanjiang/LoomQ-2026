# LoomQ 人工评分证据

这份文件是人工评分材料的统一入口。请直接编辑它，只填写要申报的项目。截图、原始结果或图表统一放在 `starter_kit/evidence/files/`，也可以引用 `starter_kit/` 中已有的代码和文档。

证据包是可选的。没有申报某项人工分时，留空即可，不影响自动评分。

## 提交前填写

把要申报项目的方框改成 `[x]`，并填写对应内容：

- [x] L1 真机
- [x] L2 交互体验
- [x] 工程与产品化
- [x] 自定义量子 RISC-V Bonus
- [x] 新手引导与视觉叙事 Bonus

## L1 真机

每个有效真机平台计 5 分，最多两个平台。模拟器不计真机分。每个平台复制并填写一次下面的信息：

平台 1（量旋 SpinQ 云真机，已完成）：

```text
平台名称：量旋 SpinQ 云真机（含 2 台真机：2Qubit核磁 Gemini-pro-1 / 3Qubit核磁 Triangulum-pro-1）
平台 job ID：G-260820-0005（2Qubit Bell）、S-260820-0001（3Qubit GHZ，各真机一个任务）
运行时间：G-260820-0005: 2026-08-20T04:13:37Z ~ 04:15:10Z（UTC，北京时间 12:13~12:15）；S-260820-0001: 2026-08-20T04:15:25Z ~ 04:17:53Z（北京时间 12:15~12:17）
shots：8192（两台均，平台返回 shots=8192 与提交一致）
实际执行的 QASM：starter_kit/evidence/files/G-260820-0005.qasm、S-260820-0001.qasm（从平台返回 sourceCode 原样提取）
平台返回的原始结果：starter_kit/evidence/files/G-260820-0005.result.json、S-260820-0001.result.json（原始 info 见 *.info.json）
任务页截图：暂无
```

文件说明（`starter_kit/evidence/files/`）：

```text
evidence/files/G-260820-0005.qasm          平台实际执行的电路（从平台返回 sourceCode 原样提取）
evidence/files/G-260820-0005.result.json   平台返回的原始结果（含概率分布 module + shots=8192）
evidence/files/G-260820-0005.info.json     平台返回的完整任务信息（tstatus=S、simulator=false、时间戳等）
evidence/files/S-260820-0001.qasm
evidence/files/S-260820-0001.result.json
evidence/files/S-260820-0001.info.json
```

留档（早期 16384 shots 任务，非本次申报口径，保留不删）：`G-260819-0003.*`、`S-260819-0001.*`（同目录）。

平台 2（本源悟空 180 超导真机，已完成）：

```text
平台名称：本源悟空 180（OriginQ Wukong 180，180 比特超导量子计算机，chip_id=180，真机非模拟器）
平台 job ID：838F10281C75D8756F10394B1B840B09（Bell 2 比特）、21F3E7FB2E0D12E0999E3C35E5473C7C（GHZ 3 比特）
运行时间：Bell 2026-08-20T00:31:42~00:31:47（平台记录，UTC+08:00，machineTime=2.778s）；GHZ 2026-08-20T00:36:11~00:36:15（machineTime=2.78s）
shots：8192（两个任务均，平台概率分布×8192 闭合：Bell 00=4104/11=4088，GHZ 000=4141/111=4045，与 counts 一致）
实际执行的电路：starter_kit/evidence/files/W180-838F10281C75D8756F10394B1B840B09.qasm、W180-21F3E7FB2E0D12E0999E3C35E5473C7C.qasm
平台返回的原始结果：starter_kit/evidence/files/W180-838F10281C75D8756F10394B1B840B09.result.json、W180-21F3E7FB2E0D12E0999E3C35E5473C7C.result.json（平台任务详情原生返回，key/value 概率分布，status=Completed）
任务页截图：starter_kit/evidence/files/W180-838F10281C75D8756F10394B1B840B09.screenshot.png、W180-21F3E7FB2E0D12E0999E3C35E5473C7C.screenshot.png
```

文件说明（`starter_kit/evidence/files/`，本源悟空前缀 `W180-` = 悟空 180）：

```text
evidence/files/W180-838F10281C75D8756F10394B1B840B09.qasm            Bell 电路（h q0; cx q0,q1; measure，2 比特）
evidence/files/W180-838F10281C75D8756F10394B1B840B09.result.json     平台原生返回（taskId/时间戳/status=Completed/概率分布）
evidence/files/W180-838F10281C75D8756F10394B1B840B09.info.json       任务信息（chip_id=180/shots=8192/circuit/timestamps）
evidence/files/W180-838F10281C75D8756F10394B1B840B09.screenshot.png  任务页截图
evidence/files/W180-21F3E7FB2E0D12E0999E3C35E5473C7C.qasm            GHZ 电路（h q0; cx q0,q1; cx q0,q2; measure，3 比特）
evidence/files/W180-21F3E7FB2E0D12E0999E3C35E5473C7C.result.json     平台原生返回（taskId/时间戳/status=Completed/概率分布）
evidence/files/W180-21F3E7FB2E0D12E0999E3C35E5473C7C.info.json       任务信息（chip_id=180/shots=8192/circuit/timestamps）
evidence/files/W180-21F3E7FB2E0D12E0999E3C35E5473C7C.screenshot.png  任务页截图
```

工作人员会核对 job ID、运行时间、电路、shots 和原始结果。截图只能辅助说明，不能代替 job ID 和原始结果。

## L2 交互体验

```text
启动界面或 CLI 的命令：bash web/run_web.sh（自动设置 macOS DYLD_LIBRARY_PATH 后启动 LoomQ Web 工作台，Flask 监听 5011 端口；依赖安装见 docs/USAGE.md §二.1 环境要求）
测试入口或页面地址：http://127.0.0.1:5011
用于交互体验评测的 3 个用户任务：
1. 跑通一个 H 门电路并读懂结果：打开工作台（默认"电路库"视图）→ 选"H 门"（通俗讲解：抛硬币 50/50）→ 点"运行" → 观察概率直方图（0 与 1 各约一半）与 4 台机器保真度。体现：零基础用户一键跑通真实电路、结果可视化清楚。
2. 玩一局袜子配对游戏理解纠缠：切到"量子游戏"视图 → 打开"伯特曼袜子" → 按提示翻开配对袜子（纠缠对同面/异面成对）→ 完成关卡看到胜利反馈。体现：用玩的方式理解纠缠关联，无需任何量子背景。
3. 用词典/对话理解一个术语：切到"使用帮助"视图 → 搜索框输入"纠缠" → 看词典卡片（通俗定义/类比/前置概念依赖链/反直觉点）；或在右下对话框用自然语言问"什么是量子叠加？" → 获得通俗解答并可多轮追问。体现：不懂时能获得有效帮助、回答一致。
截图或演示视频（evidence/files/）：
- hgate_run.png        任务 1：H 门运行界面（电路图 + QASM + 通俗讲解 + 结果）
- hgate_result.png     任务 1：运行结果（50/50 直方图 + 三后端 fidelity）
- socks_win.png        任务 2：袜子配对游戏胜利画面
- help_dict_search.png 任务 3：帮助页词典搜索"纠缠"
```

工作人员会在组委会统一模型环境中运行最终代码，测试新手是否看得懂、出错后能否得到有效帮助、结果是否清楚，以及多轮回答是否一致。选手自己的对话截图只用于说明产品流程，不直接证明得分。

## 工程与产品化

已有内容可以直接引用主 README 或其他项目文档，不必复制到本目录。

```text
干净环境中的构建和启动命令：
  - 环境要求与依赖安装：docs/USAGE.md §二.1（Python 3.10 + requirements + spinqit 本地包）
  - 一键启动：bash web/run_web.sh（自动设置 macOS DYLD 环境，无需手动干预；手动方式见 web/app.py 头部注释）
架构说明：
  - 文档：docs/PRD.md §四 技术架构、docs/USAGE.md §六 目录结构
  - 模块：Web 工作台（web/，Flask + JS）→ loomq_lib（21 个电路库、QASM 校验、后端封装、噪声模拟）→ 后端（本地模拟器 + 量旋 SpinQ 云真机 + 本源悟空 180 真机 API）；内容层（web/qc_dict.py 词典 + web/game_content/ 游戏文案 + 讲解/类比）
目标用户和使用场景：量子零基础的学生、爱好者与普通公众——无需任何量子/线性代数背景，通过"电路库 + 通俗讲解 + 量子游戏 + 术语词典 + LLM 对话"五合一工作台，几分钟内理解叠加、纠缠、测量等核心概念。
完整使用流程：docs/USAGE.md（§二快速开始 → §三日常用法 → §四电路库大白话讲解）；界面演示截图见 L2 段 evidence/files/*.png
```

工作人员会按最终 commit 实际构建和启动，并检查文档与代码是否一致、产品是否真的降低了量子计算的使用门槛。

## 自定义量子 RISC-V Bonus

以下三项必须齐全且测试通过，才获得 8 分：

```text
指令编码规格：docs/riscv_quantum_extension_spec.md（2026-08-21 定稿：5 条量子指令 qinit/qh/qcnot/qrx/qmeas 的 RISC-V CUSTOM-0(opcode=0x0B) I-type 编码表 + 4-qubit 态矢量执行语义 + 与官方 7 条经典指令的兼容性声明；机器码示例为实现的实测输出）
模拟器扩展实现：starter_kit/riscv_emulator.py（fork 官方实现，TinyRISCVEmulator 内新增 5 条量子指令：encode_quantum/decode_quantum 32 位机器码编码、_apply_h/_apply_cnot/_apply_rx 门演化、_measure 投影坍缩并写回经典寄存器、machine_code()/run_machine_code()；官方 7 条经典指令与 load_program/set_register/get_register/execute 接口逐字不变）
端到端测试：python3 tests/test_riscv_quantum_ext.py（16 项全过：官方回归 / 单门态矢 / Bell+GHZ 纠缠 / 含参门 qrx / 测量坍缩一致性 / Bell 态测量分布 8192 次仅 00/11 / 经典-量子混合程序 / 机器码编码往返 / machine_code 与汇编执行等价 / evaluator --level l3 契约回归）；python3 starter_kit/riscv_emulator.py（经典回归 + Bell 态自测）
```

评测口径：官方 Bonus +8 要求对 `riscv_emulator.py` 的扩展实现（fork 增加指令支持）+ 规格文档 + 端到端测试。本实现通过自定义量子 opcode（RISC-V CUSTOM-0 空间）为模拟器增加量子指令支持，三件套齐全且全量测试通过；同时 L3（15 分）契约不受影响——`evaluator --level all` 6/6 PASS、L1 套件 21 用例 × 3 后端 63/63 全过。

## 新手引导与视觉叙事 Bonus

请填写已有材料的路径，不要求为评分另写一套文档：

```text
零基础首次运行指南：docs/USAGE.md（§二快速开始 + §四电路库大白话讲解）；应用内"使用帮助"视图（/api/help + 词典搜索）
量子概念解释：web/qc_dict.py 术语词典（通俗定义/类比/反直觉点/前置概念依赖链）+ docs/quantum_book/（《Q is for Quantum》中文版量子书）+ 互动课程与游戏文案（web/game_content/：H 门/袜子纠缠/施温格积木）
结果可视化：web/static/js/components/histogram.js（概率直方图：理论 vs 实测 + 保真度标注）、web/static/js/bloch.js（3D 布洛赫球）、电路 SVG 实时图；示例 evidence/files/hist_5000.png、hgate_result.png
错误恢复或无障碍引导：运行前 loomq_lib.validate_qasm 语法校验并返回中文错误；右上"执行过程要点"面板显示各后端 fidelity 与失败原因；支持主题切换与字号；出错提示均为中文大白话
```

以上四项各 1 分。普通项目 README 完整不代表自动获得 Bonus。

## 提交规则

- 所有材料都要在截止前进入最终提交的 commit，工作人员不接受截止后补交。
- 外部视频可以用稳定只读链接，源码、原始结果和复现命令应保存在仓库中。
- 整个 fork commit 的归档包不得超过 100 MiB。
- 不要提交 API Key、Token、Cookie、个人身份信息或平台账户隐私。
- 如申报 L1 真机分，在最终提交 Issue 的 `Hardware evidence` 中填写 `starter_kit/evidence/README.md`。
