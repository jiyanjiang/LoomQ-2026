#!/usr/bin/env python3
"""LoomQ 新手引导文案打磨：真实调用 DeepSeek v4 pro 生成最终文稿。

用法：
  python scripts/generate_onboarding_copy.py            # 调用 v4-pro 生成并落盘
  python scripts/generate_onboarding_copy.py --dry-run  # 只打印提示词与配置，不调用

产物（data/）：
  onboarding_copy_v1_YYYYMMDD.json   # LLM 原始 JSON（含 vision 配图提示）
  onboarding_copy_v1_YYYYMMDD.md     # 可读文稿（title + body；vision 列为注释，供做图用）
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "public" / "scripts"))
import key_loader  # noqa: E402

import urllib.request  # noqa: E402

PROMPT_FILE = ROOT / "prompts" / "onboarding_copy_v1.yaml"

# 用户原始 10 页提纲（输入数据，原样传给 LLM）
OUTLINE = [
    {
        "page": 1,
        "title": "欢迎来到 LoomQ 量子工作台",
        "body": (
            "不用数学，像搭积木一样搭量子电路，然后运行，边玩儿边学。"
            "页面左侧会显示量子电路，右边有AI助手能听懂你想搭的电路，"
            "就算完全没学过量子，也能 10 分钟跑通第一个实验。"
        ),
    },
    {
        "page": 2,
        "title": "量子比特：一个箭头",
        "body": (
            "量子比特，你可以想象它是一个箭头。它既可以向上，记为 |0>，也可以向下，记为 |1>。"
            "量子叠加使得这个箭头可以同时既是向上的也是向下的。这在经典世界中是无法想象的。"
        ),
    },
    {
        "page": 3,
        "title": "量子门与 H 门",
        "body": (
            "假设我们让量子态 |0>（一个向上的箭头），从左向右跑，然后经历一系列的操作，"
            "每个操作称之为量子门，比如这里给出的例子就是H门。H门的作用是量子抛硬币，"
            "即当 |0> 经过H门，它的效果就是变成 |0>和|1>的量子叠加。"
        ),
    },
    {
        "page": 4,
        "title": "测量：看箭头朝哪",
        "body": (
            "然后我们可以对这个量子叠加态进行测量，即我们看看这个箭头到底是向上的，还是向下的。"
            "根据量子力学，我们无法预测每次测量后箭头到底是向上，还是向下的，但我们可以知道最终的概率分布与这个箭头在|0>方向上的投影和|1>方向上的投影有关。"
            "测出向上的概率就是，量子态在|0>方向上的投影的绝对值的平方，而向下的概率是量子态在|1>方向上的投影的绝对值的平方。"
            "测量是完成量子计算必不可少的一步，因为没有测量，量子态就永远处在即是0又是1的薛定谔状态，而单次测量又是随机的，也无法抽取出有效信息，"
            "因此真正的量子计算需要重复测量很多次，这样我们就可以由概率分布提取我们想知道的运算结果了。"
        ),
    },
    {
        "page": 5,
        "title": "很多门，很多比特",
        "body": (
            "H门只是最简单的量子门之一，在我们的工具库里面有12个单量子门可以对单个量子比特施加不同的操作。"
            "两个量子比特整体也可以受两比特量子门的操作，比如C-NOT门，这样两两组合，很多量子比特就会成为一个整体，"
            "按照量子门谱写出的乐谱，进行整体同步操作。这种整体性和我们刚刚说的量子叠加就是量子计算可能比经典计算快的原因。"
        ),
    },
    {
        "page": 6,
        "title": "纠缠：两双袜子",
        "body": (
            "两个量子比特在一起可以构成纠缠态，比如经典的贝尔态之一：↑↑ + ↓↓，"
            "即我们无法知道哪一个量子比特出于向上还是向下，我们能知道的是假如第一个量子比特是向上的，那么第二个也是向上的。"
            "打个比方说，我有两双袜子，一双是红袜子，一双是绿袜子。我会随机的挑袜子穿，但我总是挑颜色相同的袜子穿。"
            "因此当我走进房间的时候，如果你看到我的一只脚穿的是红袜子，那么你就知道另一只脚肯定也是红袜子。"
        ),
    },
    {
        "page": 7,
        "title": "量子算法：远超经典",
        "body": (
            "量子纠缠可以让很多量子比特成为一个整体，借助纠缠和叠加，我们可以用量子门实现很多量子算法，"
            "比如肖尔算法等，完成很多经典计算无法完成的任务，比如快速破解当前银行系统广泛使用的RSA密码等。"
        ),
    },
    {
        "page": 8,
        "title": "电路 = 配方",
        "body": (
            "一个电路，就是一份「配方」。三步走：选电路 → 看电路图 → 跑实验。"
            "电路库里的每个电路都配了逐门讲解（大白话 + 比喻）和运行结果。"
            "选一个电路 → 看懂每一个门在干什么 → 模拟运行（或挑一台真机运行） → 看测量结果直方图。"
            "对于看不懂的概念，点一下链接，会跳出小窗解释。"
        ),
    },
    {
        "page": 9,
        "title": "说人话，AI 帮你搭",
        "body": (
            "借助聊天框，说人话，AI 帮你搭电路图。一句话生成电路。"
            "不想一个个拖量子门？直接在右下量子助手对话框里说人话：「生成一个贝尔态并进行测量」——"
            "AI 帮你搭好电路、自动跑自检，还会用通俗的语言逐门讲给你听。"
        ),
    },
    {
        "page": 10,
        "title": "准备好了吗？",
        "body": (
            "想关掉这个引导？在右下「设置 → 新手引导」取消勾选即可。"
            "准备好了就点「开始使用」，去电路库跑第一个电路吧！"
        ),
    },
]


def load_prompt() -> tuple[str, str]:
    import yaml
    cfg = yaml.safe_load(PROMPT_FILE.read_text(encoding="utf-8"))
    return cfg["system"], cfg["user"]


def build_messages() -> list[dict]:
    system, user_tpl = load_prompt()
    draft = json.dumps(OUTLINE, ensure_ascii=False, indent=1)
    user = user_tpl.replace("{onboarding_draft}", draft)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _ask(messages: list[dict]) -> str:
    d = key_loader.get_deepseek()
    if not d["api_key"]:
        raise SystemExit("✗ 未找到 deepseek_api_key（config.yaml 或 env）")
    base = d["base_url"]
    payload = {
        "model": d["model"],
        "messages": messages,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    if d["model"] in ("deepseek-v4-pro", "deepseek-v4-flash"):
        payload["thinking"] = {"type": "disabled"}
    req = urllib.request.Request(
        base,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + d["api_key"], "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        body = json.loads(resp.read())
    content = body["choices"][0]["message"]["content"]
    if not content:
        raise SystemExit("✗ v4-pro 返回 content 为空（thinking 未关闭？请检查 prompts/onboarding_copy_v1.yaml 调用参数）")
    return content


def _strip_fence(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json"):
            s = s[4:]
        s = s.strip()
    return s


def render_md(pages: list[dict]) -> str:
    lines = [
        "# LoomQ 新手引导文稿 v1（DeepSeek v4-pro 打磨稿）",
        "",
        f"- 生成日期：{date.today().isoformat()}",
        f"- 页数：{len(pages)}",
        "- 用途：每页 1 图 + 1 段文字；vision 为配图场景提示（仅供做图，不进入 UI 文案）",
        "",
    ]
    for p in pages:
        lines.append(f"## P{p.get('page')} {p.get('title', '')}")
        lines.append("")
        lines.append(p.get("body", ""))
        lines.append("")
        lines.append(f"> 配图：{p.get('vision', '')}")
        lines.append("")
    return "\n".join(lines)


def check(pages: list[dict]) -> list[str]:
    issues = []
    if not pages:
        issues.append("LLM 返回空数组")
        return issues
    if len(pages) > 10:
        issues.append(f"页数 {len(pages)} 超过上限 10")
    for p in pages:
        body = p.get("body", "")
        n = len(body)
        if n > 150:
            issues.append(f"P{p.get('page')} body 过长（{n} 字，目标 40~90）")
        if not p.get("title"):
            issues.append(f"P{p.get('page')} 缺 title")
        if not p.get("vision"):
            issues.append(f"P{p.get('page')} 缺 vision")
    # 页间重复词粗检
    all_words = " ".join(p.get("body", "") for p in pages)
    for kw in ("测量", "叠加", "纠缠", "量子门", "概率"):
        cnt = all_words.count(kw)
        if cnt > 6:
            issues.append(f"关键词「{kw}」出现 {cnt} 次，注意页间重复")
    return issues


def main() -> None:
    ap = argparse.ArgumentParser(description="新手引导文案打磨（DeepSeek v4-pro）")
    ap.add_argument("--dry-run", action="store_true", help="只打印配置与消息，不调用")
    args = ap.parse_args()

    messages = build_messages()
    d = key_loader.get_deepseek()
    print(f"== 调用配置 ==\nmodel={d['model']}  base={d['base_url']}  key={'已配置' if d['api_key'] else '缺失'}")
    if args.dry_run:
        print("== messages（system 首 300 字 / user 首 300 字）==")
        print(messages[0]["content"][:300])
        print("----")
        print(messages[1]["content"][:300])
        return

    print("== 调用 DeepSeek v4-pro ... ==")
    raw = _ask(messages)
    try:
        pages = json.loads(_strip_fence(raw))
    except Exception:
        pages = None
        print("⚠ LLM 输出非 JSON，前 800 字如下：")
        print(raw[:800])
        return
    if not isinstance(pages, list):
        pages = [pages]

    today = date.today().strftime("%Y%m%d")
    out_json = ROOT / "data" / f"onboarding_copy_v1_{today}.json"
    out_md = ROOT / "data" / f"onboarding_copy_v1_{today}.md"
    out_json.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_md(pages), encoding="utf-8")

    issues = check(pages)
    print(f"✓ 已落盘：{out_json}\n          {out_md}")
    print(f"  页数 {len(pages)}；自检 {'通过' if not issues else '发现 ' + str(len(issues)) + ' 项'}:")
    for i in issues:
        print(f"    ⚠ {i}")
    for p in pages:
        print(f"  P{p.get('page'):>2} [{p.get('title','')}] {len(p.get('body',''))}字")


if __name__ == "__main__":
    main()
