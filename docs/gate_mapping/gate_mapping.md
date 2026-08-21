# LoomQ L1 门映射表（12 门 × 3 后端）

> 更新：2026-08-18 · 基于 loomq310 venv 实测（spinqit 0.2.4 / pyqpanda 3.8.5 / amazon-braket-sdk 1.95.0+default-sim 1.27.0）
>
> 结论先行：**12 门白名单里，spinq 零映射（全同名）；braket 需映射 5 个门名（cx→cnot 等）；originq 的 run() 走 QASM 2.0 零映射，transpile 输出 OriginIR 需映射门名 + 用第二参数格式。**

## 一、12 门白名单（QUANTUM_101.md 题面定义）

`h, x, s, sdg, t, tdg, rz(θ), ry(θ), cx, cu1(θ), swap, ccx`

评测电路（含隐藏/评测日变体）只使用这 12 门，不会超纲。

## 二、三后端实测支持矩阵

| # | 门 (QASM2) | spinq | braket | originq(契约) | originq(pyqpanda 实测) |
|---|---|---|---|---|---|
| 1 | `h` | ✅ `h` | ✅ `h` | ✅ `H` | ✅ `H` |
| 2 | `x` | ✅ `x` | ✅ `x` | ✅ `X` | ✅ `X` |
| 3 | `s` | ✅ `s` | ✅ `s` | ✅ `S` | ✅ `S` |
| 4 | `sdg` | ✅ `sdg` | ⚠️ **`si`** | ✅ `SDAG` | ❌ 未定义（转 `U1(-π/2)` 或走 QASM2） |
| 5 | `t` | ✅ `t` | ✅ `t` | ✅ `T` | ✅ `T` |
| 6 | `tdg` | ✅ `tdg` | ⚠️ **`ti`** | ✅ `TDAG` | ❌ 未定义（转 `U1(-π/4)` 或走 QASM2） |
| 7 | `rz(θ)` | ✅ `rz(θ)` | ✅ `rz(θ)` | ✅ `RZ q[k],(θ)` | ✅ `RZ q[0],(θ)` **必须第二格式** |
| 8 | `ry(θ)` | ✅ `ry(θ)` | ✅ `ry(θ)` | ✅ `RY q[k],(θ)` | ✅ `RY q[0],(θ)` **必须第二格式** |
| 9 | `cx` | ✅ `cx` | ⚠️ **`cnot`** | ✅ `CNOT` | ✅ `CNOT` |
| 10 | `cu1(θ)` | ✅ `cu1(θ)` | ⚠️ **`cphaseshift(θ)`** | ✅ `CU1/CR` | ⚠️ 实测 `U1 q[0],(θ)` 可解析（`CU1(` 失败） |
| 11 | `swap` | ✅ `swap` | ✅ `swap` | ✅ `SWAP` | ✅ `SWAP` |
| 12 | `ccx` | ✅ `ccx` | ⚠️ **`ccnot`** | ✅ `TOFFOLI/CCX` | ✅ `TOFFOLI` |

图例：✅ 原生同名支持（零改动） / ⚠️ 需改名映射 / ❌ 本地 SDK 不支持（需分解或走 QASM2 路径）

## 三、各后端关键差异细节

### spinq（transpile 输出 = QASM 2.0）
- **12 门全部同名原生支持，零映射**。`get_compiler("qasm")` 实测逐门编译通过。
- 参数门标准写法：`rz(0.5) q[0];`（QASM 2.0 惯例）。
- 白名单外不需要处理。

### braket（transpile 输出 = QASM 3）
- **本地模拟器只认自带 `braket_gates.inc` 里的门名**，5 个门与 QASM2 不同名：
  | QASM2 | braket | 备注 |
  |---|---|---|
  | `cx` | `cnot` | braket 无 `cx`，实测 `cx` 直接报 "Gate cx is not defined" |
  | `sdg` | `si` | braket 无 `sdg` |
  | `tdg` | `ti` | braket 无 `tdg` |
  | `cu1(θ)` | `cphaseshift(θ)` | braket 的受控相位门 |
  | `ccx` | `ccnot` | 3 比特 Toffoli |
- 参数门 `rx/ry/rz(θ)` 原生支持（实测 OK）。
- 运行时需把 `include "stdgates.inc"` 替换为 `braket_gates.inc` 绝对路径（本地无 `stdgates.inc` 文件）。
- 实测映射验证：`cnot/si/ti/cphaseshift/ccnot/swap/ry/rz/rx` 全部可执行；`sdg` 报错。

### originq（transpile 输出 = OriginIR）
- **run() 真实路径 = QASM 2.0**（`convert_qasm_string_to_qprog`），12 门实测全部 OK，**零映射**。
- **transpile 输出 OriginIR 的门名映射**（按 target_ir_contract.md 契约）：
  | QASM2 | OriginIR 契约 | 备注 |
  |---|---|---|
  | `h/x/s/t` | `H/X/S/T` | 同名大写 |
  | `sdg` | `SDAG` | 契约允许；但 pyqpanda 3.8.5 本地解析报 "undefined"（bug/不兼容），评测器按契约解析 |
  | `tdg` | `TDAG` | 同上 |
  | `cx` | `CNOT` | |
  | `cu1(θ)` | `CU1` | 契约允许；pyqpanda 本地 `CU1(` 第一格式失败，`U1 q[0],(θ)` 可解析 |
  | `swap` | `SWAP` | |
  | `ccx` | `TOFFOLI` | pyqpanda 实测 OK |
- **参数门必须用第二格式**：`RZ q[0],(0.5)` / `RY q[0],(0.3)`。第一格式 `RZ(0.5)` 在 pyqpanda 3.8.5 直接语法错误（契约文档说两种都接受，但本地 SDK 只认第二格式）。
- ⚠️ 策略：`transpile` 输出按**契约**门名（`SDAG/TDAG/CU1`），因为评测器按契约解析；本地自检用 `run()` 的 QASM 2.0 路径，不受 OriginIR 解析限制影响。

## 四、实施结论（adapter.py 改动点）

1. `transpile(qasm, "spinq")`：原样返回 QASM 2.0（零改动）。
2. `transpile(qasm, "braket")`：QASM 2 → QASM 3，且做 5 项门名映射 `cx→cnot, sdg→si, tdg→ti, cu1→cphaseshift, ccx→ccnot`（当前已做 cx→cnot，需补其余 4 项）。
3. `transpile(qasm, "originq")`：QASM 2 → OriginIR，门名映射（`sdg→SDAG, tdg→TDAG, cx→CNOT, cu1→CU1, ccx→TOFFOLI`），参数门用第二格式 `门 q[k],(θ)`（当前实现已做 cx→CNOT，需补参数门格式 + 其余门名）。
4. `run()`：三后端全部直接吃 QASM 2.0（spinq 编译 / pyqpanda 转换 / braket 转 QASM3 执行），12 门全 OK，无需改门。

## 五、回归与扩展测试（下一步）

- [ ] bell/ghz3 回归（现有 6/6 不倒退）
- [ ] 新增测试电路：toffoli、swap、ry/rz 参数门、cu1 受控相位、sdg/tdg 相位共轭
- [ ] 逐门在三后端跑通 + 与参考分布比对
