#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""draw_onboarding_illustrations.py — 新手引导 10 页插图程序化绘制（JPG）

风格对齐 web/static/js/onboarding.js 现有 SVG 画风：
  扁平矢量、粗线条、圆角矩形、半透明层次；色板：紫 #7C6CF0 / 红 #E5484D / 橙 #FFB020 /
  绿 #16A34A / 黄 #FFD84D / 深灰 #1F2937 / 浅灰 #94A3B8；画布 13:7（对齐 viewBox 260:140）。

用法:
  python scripts/draw_onboarding_illustrations.py --pages 2,6   # 只画指定页
  python scripts/draw_onboarding_illustrations.py               # 画全部 10 页
产物: data/onboarding_imgs/pXX.jpg
"""
import argparse, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.path import Path as MPath
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, PathPatch
from PIL import Image

# ---- 风格常量（对齐 onboarding.js） ----
PURPLE, RED, ORANGE, GREEN, YELLOW = "#7C6CF0", "#E5484D", "#FFB020", "#16A34A", "#FFD84D"
DARK, GRAY = "#1F2937", "#94A3B8"
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
try:
    font_manager.fontManager.addfont(FONT_PATH)
except Exception:
    pass
# 中文主字体 + STIXGeneral 兜底数学符号（⟩ 等），matplotlib >=3.7 支持 fallback
plt.rcParams["font.family"] = ["Hiragino Sans GB", "STIXGeneral"]
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "data/onboarding_imgs"

def new_fig(W, H):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax

def arrow(ax, x, y, dx, dy, color, lw=10, alpha=1.0, style="-|>", mutation=60, z=5):
    ax.add_patch(FancyArrowPatch((x, y), (x + dx, y + dy), arrowstyle=style, mutation_scale=mutation,
                                 color=color, lw=lw, alpha=alpha, shrinkA=0, shrinkB=0, zorder=z))

def rbox(ax, x, y, w, h, fc, ec=None, lw=2, alpha=1.0, rounding=14, z=5):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                 boxstyle=f"round,pad=0,rounding_size={rounding}", fc=fc,
                 ec=ec if ec else "none", lw=lw, alpha=alpha, zorder=z))

def text(ax, x, y, s, size=26, color=DARK, ha="left", va="center", z=20):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, zorder=z)

def dot(ax, x, y, r, color, alpha=1.0, z=4):
    ax.add_patch(Circle((x, y), r, fill=True, color=color, alpha=alpha, zorder=z))

def glow(ax, cx, cy, r, color=PURPLE, alpha=0.08, z=1):
    ax.add_patch(Circle((cx, cy), r, fill=True, color=color, alpha=alpha, zorder=z))

def particles(ax, cx, cy, r_min, r_max, n=50, seed=7, colors=(PURPLE, ORANGE), z=2):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        ang = rng.uniform(0, 2 * np.pi); rr = rng.uniform(r_min, r_max)
        dot(ax, cx + rr * np.cos(ang), cy + rr * np.sin(ang), rng.uniform(2, 5),
            colors[int(rng.random() * len(colors))], alpha=rng.uniform(0.25, 0.6), z=z)

def sock(ax, cx, cy, scale=1.0, color=RED, flip=False):
    """一只袜子（复刻游戏 web/static/js/socks.js 的拟真造型）：
    袜口朝上、袜筒竖直、脚掌水平伸出（flip=朝左）。cx,cy=袜口中心。

    造型照抄游戏 SVG path `M6 2h12v7.5c0 2.6-1.1 4.7-2.9 6.2L12 18.6l-3.1-2.9
    C7.1 14.2 6 12.1 6 9.5V2z`（袜筒+弯脚+圆头脚趾）。局部坐标 y 向下翻转为
    y-up：顶边 y=0、袜筒宽 12、脚趾尖 y=-16.6；K 统一缩放使袜高≈110（对齐旧矩形袜）。
    """
    K = 6.63 * scale
    verts = [(-6, 0), (6, 0), (6, -7.5),
             (6, -10.1), (4.9, -12.2), (3.1, -13.7),
             (0, -16.6), (-3.1, -13.7),
             (-4.9, -12.2), (-6, -10.1), (-6, -7.5), (-6, 0), (0, 0)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.LINETO,
             MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
             MPath.LINETO, MPath.LINETO,
             MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
             MPath.LINETO, MPath.CLOSEPOLY]
    if flip:
        verts = [(-x, y) for x, y in verts]
    ax.add_patch(PathPatch(MPath([(cx + x * K, cy + y * K) for x, y in verts], codes),
                           fill=True, facecolor=color, edgecolor="none", lw=0, zorder=5))
    # 袜口条纹（cuff）：顶边下 2.8 高矩形（复刻 SVG `M6 2h12v2.8H6z`）
    rbox(ax, cx, cy - 1.4 * K, 12 * K, 2.8 * K, "white", alpha=0.55, rounding=4 * scale, z=6)
    # 袜筒水平条纹（复刻 SVG `M6 7h12` stroke）
    ax.plot([cx - 6 * K, cx + 6 * K], [cy - 5 * K, cy - 5 * K],
            color="white", alpha=0.55, lw=max(1.2, 2.2 * scale), zorder=6)

def socks_pair(ax, cx, cy, scale=1.0, color=RED, gap=150 * 1.0):
    """一双袜子（两只并排，脚掌相对朝里），cx,cy=中心"""
    g = gap * scale
    sock(ax, cx - g / 2, cy, scale, color, flip=False)   # 左脚：脚掌朝右（朝里）
    sock(ax, cx + g / 2, cy, scale, color, flip=True)    # 右脚：脚掌朝左（朝里）

# ---------------------------------------------------------------------------
# 各页
# ---------------------------------------------------------------------------
def draw_p2(ax, W, H):
    """箭头：向上 |0⟩ + 向下 |1⟩ 的叠加（两箭头错开、中间光晕融合）"""
    cx, cy = W * 0.5, H * 0.53
    for r, a in [(300, .06), (230, .08), (165, .11)]:
        glow(ax, cx, cy, r, PURPLE, a)
    particles(ax, cx, cy, 140, 330, n=55, seed=7)
    # 向上箭头（紫，偏左）
    arrow(ax, cx - 55, cy - 90, 0, 165, PURPLE, lw=30, style="-|>", mutation=95)
    # 向下箭头（橙，偏右，半透明）
    arrow(ax, cx + 55, cy + 90, 0, -165, ORANGE, lw=30, alpha=0.55, style="-|>", mutation=95)
    text(ax, cx - 55, cy + 185, "|0⟩ 向上", size=30, color=PURPLE, ha="center")
    text(ax, cx + 55, cy - 185, "|1⟩ 向下", size=30, color=ORANGE, ha="center")
    text(ax, W * 0.5, H * 0.90, "叠加：既向上，又向下", size=38, color=DARK, ha="center")

def draw_p6(ax, W, H):
    """两双袜子：红 / 绿，中间发光量子连线"""
    left_cx, right_cx = W * 0.30, W * 0.70
    cy = H * 0.48
    glow(ax, left_cx, cy - 10, 135, RED, 0.10)
    glow(ax, right_cx, cy - 10, 135, GREEN, 0.10)
    socks_pair(ax, left_cx, cy, scale=1.0, color=RED)
    socks_pair(ax, right_cx, cy, scale=1.0, color=GREEN)
    # 发光量子连线（两道弧 + 粒子）
    mid = W * 0.5
    for off, al in [(-18, .85), (18, .45)]:
        ax.plot([left_cx + 80, mid, right_cx - 80], [cy - 20 + off, cy + 90, cy - 20 + off],
                linestyle=(0, (8, 6)), color=PURPLE, lw=4, alpha=al, zorder=6)
    for i in range(9):
        t = i / 8.0
        x = left_cx + 80 + (right_cx - left_cx - 160) * t
        y = cy - 20 + 110 * np.sin(np.pi * t) + 8 * np.cos(2 * np.pi * t)
        dot(ax, x, y, 4.5, PURPLE, alpha=0.85)
    text(ax, W * 0.5, H * 0.13, "两双袜子，一双红，一双绿", size=32, color=DARK, ha="center")
    text(ax, W * 0.5, H * 0.90, "看到一只红，另一只必红", size=38, color=DARK, ha="center")

DRAWERS = {2: draw_p2, 6: draw_p6}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="", help="逗号分隔页号，缺省=全部已实现页")
    ap.add_argument("--size", default="1300x700", help="画布 WxH（13:7）")
    ap.add_argument("--quality", type=int, default=88)
    args = ap.parse_args()
    W, H = (int(v) for v in args.size.split("x"))
    os.makedirs(OUT_DIR, exist_ok=True)
    pages = [int(p) for p in args.pages.split(",") if p] if args.pages else sorted(DRAWERS)
    for pg in pages:
        if pg not in DRAWERS:
            print(f"[skip] p{pg}: 未实现"); continue
        fig, ax = new_fig(W, H)
        DRAWERS[pg](ax, W, H)
        png = os.path.join(OUT_DIR, f"p{pg:02d}.png")
        fig.savefig(png, dpi=100, format="png")
        plt.close(fig)
        out = os.path.join(OUT_DIR, f"p{pg:02d}.jpg")
        Image.open(png).convert("RGB").save(out, "JPEG", quality=args.quality)
        os.remove(png)
        kb = os.path.getsize(out) / 1024
        print(f"[ok] p{pg:02d}.jpg  {W}x{H}  {kb:.0f} KB")

if __name__ == "__main__":
    main()
