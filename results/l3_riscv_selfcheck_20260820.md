# L3 RISC-V 自测结果（2026-08-20）

## 背景
L3 = 量子-经典混合编程 Bonus（8 分）。契约：给定含 `classical {}` 块的混合 QASM，
`adapter.compile_hybrid(source)` 返回 `(quantum_ops, assembly)`；评测方把测量结果
写入 `x10`、执行汇编后断言分支结果落在 `x1`（对应源码 `r1`）。
自测目标：迷你翻译器对规格文档（`docs/l3_riscv_encoding_spec.md` §5）的隐藏变体矩阵
全部正确，不只答公开那一题。

## 环境
- 模拟器：`starter_kit/riscv_emulator.py`（TinyRISCVEmulator，7 条指令）
- 翻译器：`adapter.py::compile_hybrid`（2026-08-20 实现）
- 入口：`set_register("x10", measured)` → `execute()` → 断言目标寄存器

## 结果

### 公开契约（evaluator.py --level l3）
| 项 | 结果 |
|---|---|
| public-branch（`if(c[0]==1){r1=7}else{r1=3}`） | **[PASS]** passed:1 failed:0 |

### 隐藏变体矩阵（7/7）
| 变体 | 翻译点 | 用例 | 判定 |
|---|---|---|---|
| 公开契约 r1==1 | beq 分支 + li | 测0→3 / 测1→7 | PASS |
| 换变量 r2 / ==0 / 负常量 | rN→xN 直映 + li 通吃 | 测0→42 / 测1→-1 | PASS |
| != 分支 | bne | 测0→5 / 测1→9 | PASS |
| 多 if 串联 | THEN_n/END_n 编号递增 | 测0→3 / 测1→7 | PASS |
| else 缺省 | 省 else 段，反向跳转跳过 | 测0→0 / 测1→11 | PASS |
| 多测量位 c[1] | 语法通用（只喂 x10） | 测0→20 / 测1→21 | PASS |
| 寄存器赋值 r1=r2 | add x1, x2, x0 | 测0→3 / 测1→0 | PASS |

汇总：**公开 1/1 PASS + 隐藏 7/7 PASS，lint 零错误**

## 复现
```bash
# 公开契约
python3 starter_kit/evaluator.py --level l3
# 隐藏变体矩阵（内联自测）
python3 -c "..."   # 见 docs/l3_riscv_encoding_spec.md §5 / 会话记录
```

## 结论
`compile_hybrid` 对 L3 契约与全部已知变体正确，分支语义（beq/bne/j + 常量装载 +
寄存器直映）在 TinyRISCVEmulator 上验证通过；quantum_ops 剥离 classical 块后逐条
门操作输出非空。L3 Bonus 风险已消除。
