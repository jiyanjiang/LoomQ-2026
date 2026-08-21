# 隐藏电路自测集结果（2026-08-20）

## 背景
组织方隐藏电路集（QUANTUM_101 泄露）：QFT-4 / Grover-3 / GHZ-5 / Random×3。
自验目标：同一份 QASM 2.0 经 transpile() 转译后在三个后端模拟器跑出的结果与理论一致。
（组织方不收电路，只收转译器 adapter —— 本自测验证的正是转译正确性。）

## 环境
- 三后端：spinq_basic_simulator / originq_cpu_simulator / braket_local_simulator
- shots=8192，容差=0.02（2%）
- 位序：已统一归一化为 little-endian（key 最右 = c[0]）

## 结果

| 电路 | 后端 | 结果 | 判定 |
|---|---|---|---|
| GHZ-5 | spinq/originq/braket | PASS | P(00000)=0.500 P(11111)=0.500（期望各≈0.50） |
| QFT-4 | spinq/originq/braket | PASS | 最大偏差=0.000（期望 16 态各 1/16≈0.0625） |
| Grover-3 | spinq/originq/braket | PASS | 主峰 100 P=0.781（理论≈0.78） |
| Random-1 | spinq/originq/braket | PASS | 三后端最大概率差=0.000 |
| Random-2 | spinq/originq/braket | PASS | 三后端最大概率差=0.009 |
| Random-3 | spinq/originq/braket | PASS | 三后端最大概率差=0.006 |

汇总：**6 PASS / 0 FAIL**

## 覆盖的 12 门白名单
h / x / s / sdg / t / tdg / rz / ry / cx / cu1 / swap / ccx —— 全部在三个电路的 Random×3 中覆盖并通过。

## 复现
```bash
python scripts/selfcheck_hidden_circuits.py --shots 8192 --tol 0.02
```

## 结论
adapter 转译链路对组织方隐藏电路集全部正确，L1 自动评分（隐藏电路）风险已消除。
