#!/usr/bin/env python3
"""施温格积木挑战题解空间枚举（验证题目严谨性用）。

模型（测量代数 / 偏振光类比）：
  - 入射态：纯态 |↑⟩|↓⟩|+⟩|−⟩，或自然光（非偏振混合）
  - 每块积木 = 投影算符（I = 单位算符不改变）
  - 纯态出射率 = Π |⟨后一态|前一态⟩|²（首块从前一态即入射态算）
  - 自然光：第一块后恒为 1/2，之后各块乘 |⟨后|前⟩|²
  - I 对任何光强度不变（可插任意位置，等效于跳过）

用法：python web/enumerate_schwinger.py [入射态] [目标]
"""
import itertools
import sys

KETS = {
    "up": (1, 0),
    "down": (0, 1),
    "plus": (1 / 2 ** 0.5, 1 / 2 ** 0.5),
    "minus": (1 / 2 ** 0.5, -1 / 2 ** 0.5),
}
BLOCKS = ["up", "down", "plus", "minus", "I"]


def ip(a, b):
    return a[0] * b[0] + a[1] * b[1]


def rate_pure(incident, seq):
    r = 1.0
    prev = KETS[incident]
    for b in seq:
        if b == "I":
            continue
        f = abs(ip(KETS[b], prev)) ** 2
        if abs(f) < 1e-9:
            return 0.0
        r *= f
        prev = KETS[b]
    return r


def rate_natural(seq):
    r = 1.0
    prev = None
    for b in seq:
        if b == "I":
            continue
        if prev is None:
            r *= 0.5  # 第一块投影：自然光恒 1/2
        else:
            f = abs(ip(KETS[b], prev)) ** 2
            if abs(f) < 1e-9:
                return 0.0
            r *= f
        prev = KETS[b]
    return r


def rate(inc, seq):
    return rate_natural(seq) if inc == "natural" else rate_pure(inc, seq)


def solve(inc, target, maxlen=3, allow_I=True):
    blocks = BLOCKS if allow_I else ["up", "down", "plus", "minus"]
    sols = []
    for L in range(1, maxlen + 1):
        for combo in itertools.permutations(blocks, L):
            if abs(rate(inc, combo) - target) < 1e-9:
                sols.append(combo)
    return sols


def main():
    if len(sys.argv) >= 3:
        inc = sys.argv[1]
        tgt = float(sys.argv[2])
        for s in solve(inc, tgt):
            print(f"{s} = {rate(inc, s):.4f}")
        print(f"共 {len(solve(inc, tgt))} 解")
        return
    # 默认：全矩阵
    for inc in ["up", "natural"]:
        for tgt in [1.0, 0.5, 0.25, 0.125]:
            s = solve(inc, tgt)
            print(f"入射 {inc:8s} 目标 {tgt:5.3f}: {len(s)} 解")
            for x in s[:12]:
                print(f"    {x} = {rate(inc, x):.4f}")
            print()


if __name__ == "__main__":
    main()
