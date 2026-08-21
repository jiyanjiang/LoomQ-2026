# EXP001 实验报告：L1 全链路验收（transpile + run × 三后端 × 全量测试问题集）

- 日期：2026-08-18
- 项目：LoomQ（QAIDAO/LoomQ-2026 量子编程竞赛）
- 编号规则：EXP001（本报告为 L1 阶段首次完整验收）

---

## 1. 研究背景

LoomQ L1 要求实现 `transpile(qasm, target)` 与 `run(qasm, target, shots)`，
把 OpenQASM 2.0 电路翻译到三家后端（spinq / originq / braket）并本地模拟执行。
此前已完成：环境搭建（Python 3.10 venv）、三 SDK 版本锁定、门映射调研（DS v4 pro 审查）、
"尺子"（qelib1.inc 语义模拟器）、braket s/t 相位门缺陷定位与适配、位序归一化。
本实验做**最终全链路验收**：全量测试问题集 × 三后端，确认 L1 交付物可用、可复现、无泄漏。

## 2. 研究目的

验证以下假设：
- H1：transpile 对三后端的输出符合 target_ir_contract.md 契约（可被评测器语义模拟）
- H2：run 在三后端本地模拟器上的 counts 分布与"尺子"参考分布一致（Hellinger ≥ 0.97）
- H3：交付物（starter_kit/）无 API key、无本地绝对路径泄漏

## 3. 研究方法

1. **尺子**：`tests/qasm_semantics.py`（numpy 态矢量模拟，qelib1.inc 官方门定义，不依赖厂商 SDK）
2. **测试问题集**：`tests/cases.yaml`——12 个逐门确定性电路（g01-g12）+ 5 个标准算法电路（a01-a05，
   含 QASMBench 来源的 qft4/grover2/cat4/teleport3）
3. **正式自检**：`tests/run_test_suite.py`——每电路用尺子算参考分布，三后端各跑 8192 shots，
   Hellinger ≥ 0.97 = PASS；含 schema 校验（counts 总=shots、key 二进制、bit_order=little）
4. **originq transpile 校验器**：`tests/originir_verifier.py`——尺子反向解析 OriginIR，与源 QASM 分布比对
5. **脱敏扫描**：grep 检查 API key 模式与 `/Users/` 绝对路径

## 4. 研究结果

### 4.1 正式自检（tests/run_test_suite.py）

**用例级 17/17 通过；后端级 51/51 通过。**

| 用例 | 覆盖门 | spinq | originq | braket |
|---|---|---|---|---|
| g01-g12（逐门 12 个） | h/x/s/sdg/t/tdg/rz/ry/cx/cu1/swap/ccx | 全 PASS | 全 PASS | 全 PASS |
| a01 ghz3 | h,cx | 1.000 | 0.998 | 0.998 |
| a02 cat4（QASMBench） | h,cx | 1.000 | 0.994 | 1.000 |
| a03 qft4（QASMBench） | h,x,cu1 | 1.000 | **0.985** | **0.986** |
| a04 grover2（QASMBench） | h,x,cx | 1.000 | 1.000 | 1.000 |
| a05 teleport3（QASMBench） | h,t,s,cx | 1.000 | 0.990 | 0.987 |

最低 fidelity 0.985（qft4 originq），全部远超 0.97 阈值。

### 4.2 originq transpile 校验器（tests/originir_verifier.py）

**18/18 通过**（12 逐门 + bell/ghz3/qft4/grover2/cat4/teleport3）。
此校验器发现并修复了 transpile 的 3 个真实 bug：
1. `cu1` 参数门只输出单比特（丢第二个 qubit）→ 修复为 `CU1 q[0], q[1],(0.5)`
2. `barrier` 未被过滤（OriginIR 不支持）→ 修复为跳过
3. 尺子缺 `barrier` 支持 → 补充（无量子语义，跳过）

### 4.3 L1 公开回归

`evaluator.py --level l1 --target spinq,originq,braket`：**6/6 PASS**，exit=0。

### 4.4 脱敏扫描

- `starter_kit/` 内：无 `sk-`/`AIzaSy` key、无 `/Users/` 绝对路径（clean）
- 取 key 唯一通道：`public/scripts/key_loader.py`（env → config.yaml），脚本内零明文
- `config.yaml`/`api-key.txt` 在 `.gitignore`，不进交付物
- 唯一匹配是 key_loader.py 注释示例文本（非真实 key，无害）

## 5. 讨论

1. **三后端对齐度**：12 门 × 3 后端全部 Hellinger ≥ 0.97。spinq 全 1.000（原生 QASM2 支持最全）；
   originq/braket 的相位门靠"尺子"确认与标准一致（braket 经 s/t→rz 展开适配其 pow 幂次门缺失缺陷）。
2. **braket s/t 适配**：braket 1.27.0 本地模拟器 `pow(1/2) @ z` 幂次语法失效，s/t 退化恒等
   （P2 探针 + QPT 反推双证）。adapter 的 run 本地模式展开为 rz（等分布），transpile 契约模式保持标准 s/t
   ——双模式分离同时满足评测器解析与本地自检。
3. **局限**：
   - 位序归一化基于三后端实测（spinq/braket 反转、originq 原生），若评测器位序约定不同需复核
   - transpile（braket）输出 `cnot` 而非 `cx`（贴契约示例），评测器接受两者（契约明确）
   - 仅本地模拟器验证；真机（spinq_cloud/originq_wukong/braket_cloud）未测，需账号
4. **环境**：macOS 26.2 + Python 3.10（loomq310 venv）；spinqit 0.2.4 / pyqpanda 3.8.5 /
   amazon-braket-sdk 1.95.0 + default-simulator 1.27.0（版本组合经 antlr 4.9.2 冲突排查锁定）

## 6. 下一步设想

- 待办：真机后端验证（需账号）、L2（agent_chat）、评测容器 Docker 验证、transpile 位序/门名与评测器实现最终对齐
- 建议：L1 已满足提交资格线，可并行推进 L2 与容器验证；测试问题集可扩展 QFT-5/Grover-3 等更复杂电路

---

## 7. 复现信息（强制，缺一不可）

| 要素 | 内容 |
|---|---|
| 运行命令 | `source ~/.venvs/loomq310/bin/activate && cd /Users/jiyanjiang/Downloads/LoomQ && python tests/run_test_suite.py` |
| 参数设置 | SHOTS=8192, FID_THRESHOLD=0.97, TARGETS=(spinq,originq,braket) |
| 输入文件 | `tests/cases.yaml`（17 用例）、`tests/circuits/*.qasm`、`starter_kit/circuits/*.qasm` |
| 输出位置 | `tests/test_suite_report.json`、`tests/alignment_report.json`、`tests/braket_s_probe_report.json` |
| 依赖版本 | numpy 1.26.4 / spinqit 0.2.4 / pyqpanda 3.8.5 / amazon-braket-sdk 1.95.0 / default-simulator 1.27.0 / antlr4 4.9.2 / pyyaml 6.0.3（Python 3.10, loomq310 venv） |
| 耗时 | 单轮自检 ~2-3 分钟（17 电路 × 3 后端 × 8192 shots） |
