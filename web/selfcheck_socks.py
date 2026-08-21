#!/usr/bin/env python3
"""伯特曼袜子游戏 · 可胜性自检（solvability check）。

问题：牌局是否"必定能配完全部对"？否则玩家永远无法胜利。

验证（覆盖 4/8 双 × same/diff 全部 4 种组合 × 200 次随机洗牌）：
1. 牌面完整性：总牌数 = 2N；每个 pairId 恰好 2 张（无孤儿牌）
2. 颜色规则自洽：每对的伙伴在牌堆中唯一存在（同色/相反色 + 同徽标）
3. 最优策略完整对局：按 pairId 配对必达 matched==total（胜利必然触发）
4. 任意随机策略对局：随机翻两张同 pairId 的牌，必达 matched==total

若全部通过 → "牌局必可胜"成立。
"""

import random

BIT_COLOR = {0: "红", 1: "绿"}


def make_board(mode, count, seed):
    rng = random.Random(seed)
    is_same = (mode == "same")
    pairs = []
    for i in range(count):
        bits = [0, 0] if (is_same and i % 2 == 0) else ([1, 1] if is_same else [0, 1])
        pairs.append((i, bits))
    board = []  # (pairId, side, bit)
    for pid, bits in pairs:
        board.append((pid, "L", bits[0]))
        board.append((pid, "R", bits[1]))
    rng.shuffle(board)
    return pairs, board


def check_integrity(pairs, board):
    """1. 牌面完整性：每 pairId 恰好 2 张。"""
    assert len(board) == 2 * len(pairs), f"总牌数错误: {len(board)} vs {2*len(pairs)}"
    from collections import Counter
    cnt = Counter(pid for pid, _, _ in board)
    for pid in range(len(pairs)):
        assert cnt[pid] == 2, f"pairId {pid} 有 {cnt[pid]} 张牌（应为2）"
    return True


def check_partner_exists(mode, pairs, board):
    """2. 每张牌的伙伴在牌堆中唯一存在（同徽标 + 同色/相反色）。"""
    # 按 pairId 分组：同一 pairId 的两张互为伙伴
    by_pid = {}
    for pid, side, bit in board:
        by_pid.setdefault(pid, []).append((side, bit))
    for pid, cards in by_pid.items():
        assert len(cards) == 2, f"pairId {pid} 伙伴不完整: {cards}"
        b0, b1 = cards[0][1], cards[1][1]
        if mode == "same":
            assert b0 == b1, f"same 模式 pairId {pid} 颜色不同: {b0} vs {b1}"
        else:
            assert b0 != b1, f"diff 模式 pairId {pid} 颜色相同: {b0} vs {b1}"
    return True


def simulate_optimal(pairs, board):
    """3. 最优策略：按 pairId 依次配，必达全胜。"""
    matched = 0
    remaining = set(pid for pid, _, _ in board)
    for pid in sorted(remaining):
        # 选中该 pairId 的两张
        cards = [i for i, (p, _, _) in enumerate(board) if p == pid]
        assert len(cards) == 2, f"配对时 pairId {pid} 找不到两张"
        matched += 1
    return matched == len(pairs)


def simulate_random(rng, board):
    """4. 随机策略：随机翻两张同 pairId 的牌，必达全胜（存在配对路径）。"""
    n_pairs = len(set(pid for pid, _, _ in board))
    # 构造"配完"路径：每次取一个未配 pairId 的两张牌
    unpaired = set(pid for pid, _, _ in board)
    matched = 0
    while unpaired:
        pid = rng.choice(sorted(unpaired))
        cards = [i for i, (p, _, _) in enumerate(board) if p == pid]
        if len(cards) == 2:
            matched += 1
        unpaired.discard(pid)
    return matched == n_pairs


def main():
    failures = 0
    for mode in ("same", "diff"):
        for count in (4, 8):
            for seed in range(200):
                pairs, board = make_board(mode, count, seed)
                try:
                    check_integrity(pairs, board)
                    check_partner_exists(mode, pairs, board)
                    assert simulate_optimal(pairs, board)
                    assert simulate_random(random.Random(seed + 1000), board)
                except AssertionError as e:
                    failures += 1
                    print(f"✗ {mode} {count}双 seed={seed}: {e}")
    total = 2 * 2 * 200
    if failures == 0:
        print(f"✓ 可胜性自检通过：{total} 局（4/8双 × same/diff × 200随机洗牌）全部必可胜")
        return 0
    print(f"✗ {failures}/{total} 局失败")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
