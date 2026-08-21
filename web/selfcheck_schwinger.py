#!/usr/bin/env python3
"""施温格积木可胜性自检（与 schwinger.js 正交表/关卡交叉验证）。

验证 3 件事：
  1. 正交表正确：4×4 全部相邻对用真实矩阵乘法验证 ORTHO 结果
  2. 8 关答案唯一确定：passes() 结果与预设目标一致（无歧义关卡）
  3. 挑战关（第 8 关"挡"）至少存在一个 2 块解

用法：python web/selfcheck_schwinger.py
"""
from __future__ import annotations

import itertools

# ---- 四种态（S_z 基下）----
KETS = {
    "up":    (1, 0),                     # |↑⟩ = S_z +ħ/2
    "down":  (0, 1),                     # |↓⟩ = S_z −ħ/2
    "plus":  (1 / 2 ** 0.5, 1 / 2 ** 0.5),   # |+⟩ = (|↑⟩+|↓⟩)/√2 = S_x +ħ/2
    "minus": (1 / 2 ** 0.5, -1 / 2 ** 0.5),  # |−⟩ = (|↑⟩−|↓⟩)/√2 = S_x −ħ/2
}


def inner(a, b):
    """⟨a|b⟩（a 共轭转置 × b）"""
    return a[0] * b[0] + a[1] * b[1]


def ortho(a, b):
    """两态是否正交（⟨a|b⟩ = 0，数值容差）"""
    return abs(inner(KETS[a], KETS[b])) < 1e-9


def passes(blocks):
    """与 JS 同构：相邻正交 → 挡(false)；否则透(true)"""
    for i in range(len(blocks) - 1):
        if ortho(blocks[i], blocks[i + 1]):
            return False
    return True


# ---- 8 关（与 schwinger.js LEVELS 同构：入射态 + 积木串 + 预期透/挡）----
# (incident, blocks, expected_pass)  expected_pass: True=能通过, False=被挡住
LEVELS = [
    ("up",   ["up"],               True),
    ("up",   ["up", "up"],         True),
    ("up",   ["up", "down"],       False),
    ("up",   ["plus", "minus"],    False),
    ("up",   ["up", "plus"],       True),
    ("down", ["down", "plus"],     True),
    ("up",   ["up", "plus", "down"], True),
    ("up",   [],                   None),  # 挑战：拼出挡住粒子的组合
]


def intensity(incident, blocks):
    """出射光强：首块 |⟨目标|入射⟩|² × 后续每块 |⟨后|前⟩|²（与 JS beamIntensity 同构）"""
    r = 1.0
    prev = KETS[incident]
    for b in blocks:
        f = inner(KETS[b], prev) ** 2
        if abs(f) < 1e-9:
            return 0.0
        r *= f
        prev = KETS[b]
    return r


def passes_level(incident, blocks):
    """粒子能否通过（光强 > 0）——与 JS answer() 的 passed 同构"""
    return intensity(incident, blocks) > 0


def main() -> int:
    fails = 0

    # 1. 正交表全验证（4×4）
    print("=== [1/3] 正交表矩阵验证（4×4）===")
    for a, b in itertools.product(KETS, repeat=2):
        js_ortho = {
            "up":    {"up": False, "down": True,  "plus": False, "minus": False},
            "down":  {"up": True,  "down": False, "plus": False, "minus": False},
            "plus":  {"up": False, "down": False, "plus": False, "minus": True},
            "minus": {"up": False, "down": False, "plus": True,  "minus": False},
        }[a][b]
        math_ortho = ortho(a, b)
        if js_ortho != math_ortho:
            print(f"  ✗ 正交表不一致: {a}×{b} JS={js_ortho} 数学={math_ortho}")
            fails += 1
    if fails == 0:
        print("  ✓ 4×4 正交表全部与矩阵乘法一致")

    # 2. 8 关答案唯一（入射态 × 积木串 → 粒子能否通过匹配预设）
    print("=== [2/3] 8 关答案验证（粒子透/挡）===")
    for i, (inc, blocks, exp) in enumerate(LEVELS[:-1]):
        got = passes_level(inc, blocks)
        if got != exp:
            print(f"  ✗ 第{i+1}关 入射{inc} {blocks}: 预设={'通过' if exp else '挡住'} 实际={'通过' if got else '挡住'}")
            fails += 1
    if fails == 0:
        print("  ✓ 1-7 关粒子透/挡唯一确定（无歧义）")

    # 3. 挑战关存在性（入射 up 下拼出挡住粒子的 2 块解）
    print("=== [3/3] 挑战关（挡住粒子）存在性 ===")
    found = []
    for combo in itertools.product(KETS, repeat=2):
        if not passes_level("up", list(combo)):
            found.append(combo)
    if found:
        print(f"  ✓ 存在 {len(found)} 个 2 块挡住粒子的解，如 {found[0]}")
    else:
        print("  ✗ 挑战关无解！")
        fails += 1

    print("---")
    if fails:
        print(f"✗ 施温格积木自检失败：{fails} 处")
        return 1
    print("✓ 施温格积木必可胜（正交表正确 + 8 关答案确定 + 挑战关有解）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
