#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive_spinq_analysis.py
=========================
把 2026-08-19 "web vs SDK 一致性分析" 的真实数据固化落盘。

⚠️ 2026-08-19 重要更正（撤回此前误判）：
    starter_kit/evidence/ 是官方参赛模板自带的**范例申报文件**（创建时间 22:28，
    早于我们 22:49/22:54 的真实实验抓包），README 预填的 G-260819-0003 / S-260819-0001、
    shots=16384 均为模板示例内容，与我们的实验无关，更不是 AI 伪造。
    此前"16384 系虚构数字 / evidence 伪造实锤 / 概率×shots 整数扫描证实真实采样=5000"
    的分析系误判，已整体撤回。

真实情况（用户 2026-08-19 确认）：
    - web 版 shots = 1024，为后端缺省值，**无法设置**；
    - SDK 版 shots 可设置，我们的实验统一跑 **5000**。

  §0 官方文档关键事实（doc.spinq.cn: 未配置 shots 默认 1024）
  §1 浏览器原始 msgpack（无 shots 字段、仅概率分布）
  §2 origin_results/ 抓包 task-detail JSON（web 版真实任务，缺省 1024）
  §3 starter_kit/evidence/ 官方模板范例（预填示例值，与实验无关）
  §4 results/spinq_sdk_20260819/ 的 SDK 实验产物（shots=5000 可设置）
  §5 保真度对比表 + 双样本比例 z 检验（web 1024 vs SDK 5000，GHZ SDK 两次复测）
  §6 时间线（UTC + 北京时间）
  §7 结论（2026-08-19 撤回版 + GHZ#2 复核）

⚠️ 2026-08-20 注：本脚本分析基于旧 shots 口径（web 1024 / SDK 5000）。
统一 8192 shots 为唯一提交口径后，此分析仅供历史追溯，不再作为当前结论。

用法: python scripts/archive_spinq_analysis.py
输出: results/spinq_analysis_evidence_20260819.md （人类可读归档）
      results/spinq_analysis_evidence_20260819.json （结构化全量 dump）
"""
import json
import math
import os
from datetime import datetime, timezone, timedelta

import msgpack

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
ORIGIN = os.path.join(ROOT, "origin_results")
EVID = os.path.join(ROOT, "starter_kit", "evidence", "files")
SDK = os.path.join(RES, "spinq_sdk_20260819")

OUT_MD = os.path.join(RES, "spinq_analysis_evidence_20260819.md")
OUT_JSON = os.path.join(RES, "spinq_analysis_evidence_20260819.json")

CST = timezone(timedelta(hours=8))

# 真实概率数据（来自文件，非推断）
WEB_BELL = {"00": 0.4825999, "01": 0.0298, "10": 0.0142, "11": 0.4734}  # E7599A00
WEB_GHZ = {"000": 0.473, "001": 0.0136, "010": 0.0036, "011": 0.0352,
           "100": 0.0262, "101": 0.0079999, "110": 0.0152, "111": 0.4252}  # 06C3076E
SDK_BELL = {"00": 2263, "11": 2063, "01": 408, "10": 266}  # G-260819-0004, 5000
SDK_GHZ = {"000": 1743, "011": 104, "110": 137, "001": 317,
           "100": 287, "111": 1551, "101": 462, "010": 400}  # S-260819-0002, 5000 (run1)
SDK_GHZ_2 = {"000": 1625, "011": 59, "110": 569, "001": 398,
             "100": 69, "111": 1351, "101": 442, "010": 488}  # S-260819-0003, 5000 (run2)


def bj(utc_str):
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        return dt.astimezone(CST).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_str


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def unpack_msgpack(path):
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return {"bytes": len(raw), "data": msgpack.unpackb(raw, raw=False)}
    except Exception as e:
        return {"bytes": len(raw), "parse_error": str(e)}


def ztest(p1, n1, p2, n2):
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    return {"p1": p1, "n1": n1, "p2": p2, "n2": n2, "z": (p1 - p2) / se if se > 0 else float("nan")}


def dump_json_files(md, name, dirpath, suffix=".json", indent=1):
    """把所有 *.json/*.qasm 文件以紧凑方式写入 md"""
    rows = []
    for fname in sorted(os.listdir(dirpath)):
        path = os.path.join(dirpath, fname)
        if fname.endswith(suffix):
            with open(path, "r", encoding="utf-8") as f:
                rows.append((fname, f.read()))
    md.append(f"### {name}")
    md.append("")
    for fname, content in rows:
        md.append(f"`{fname}`")
        md.append("")
        md.append("```json")
        md.append(content)
        md.append("```")
        md.append("")


def main():
    dump = {"saved_at_utc": datetime.now(timezone.utc).isoformat()}
    md = []
    md.append("# SpinQ web vs SDK 一致性分析 —— 真实数据归档（撤回版）")
    md.append("")
    md.append(f"归档时间(UTC): {dump['saved_at_utc']}")
    md.append("")
    md.append("> 背景: 用户质疑 SDK 跑的实验与 web 跑的实验是否一致、3 比特误差是否正常。")
    md.append(">")
    md.append("> ⚠️ **重要更正（2026-08-19 撤回此前误判）**: `starter_kit/evidence/` 是官方模板")
    md.append("> 自带的**范例申报文件**（创建时间 22:28，早于实验 22:49/22:54），README 预填的")
    md.append("> job ID 与 `shots=16384` 均为模板示例，与我们的实验无关，**非伪造**。")
    md.append(">")
    md.append("> **真实情况（用户确认）**: web 版 `shots=1024` 为后端缺省值、无法设置；")
    md.append("> SDK 版 `shots` 可设置，我们的实验统一跑 **5000**。")
    md.append("")

    # §0
    md.append("## 0. 官方文档关键事实（doc.spinq.cn）")
    md.append("")
    md.append("**SpinQit Cloud 后端: 如果未配置 shots，默认值是 1024。**")
    md.append("")
    md.append("> 原文: \"If shots are not configured, the default is 1024.\"")
    md.append("> 来源: doc.spinq.cn（用户 2026-08-19 查证）")
    md.append("")
    md.append("推论: web 版任务未配置 shots → 实际采样数 = 1024（缺省，无法设置）。")
    md.append("SDK 版显式配置 shots=5000 → 实际采样数 = 5000（可设置）。")
    md.append("")

    # §1 msgpack
    md.append("## 1. 浏览器原始 msgpack（web 端原始响应）")
    md.append("")
    md.append("> msgpack 为浏览器响应体，内容仅为概率分布、**无 shots 字段**。")
    md.append("")
    msgpack_dump = {}
    for fname in ["task_result_G-260819-0003.msgpack", "task_result_S-260819-0001.msgpack"]:
        path = os.path.join(RES, fname)
        r = unpack_msgpack(path)
        msgpack_dump[fname] = r
        md.append(f"### {fname}  ({r.get('bytes', 0)} bytes)")
        md.append("")
        if "parse_error" in r:
            md.append(f"解析失败: {r['parse_error']}")
        else:
            md.append("```json")
            md.append(json.dumps(r["data"], ensure_ascii=False, indent=2, default=str))
            md.append("```")
        md.append("")
    dump["msgpack"] = msgpack_dump

    # §2 抓包
    md.append("## 2. origin_results/ 浏览器抓包 task-detail（web 版真实任务）")
    md.append("")
    md.append("> 这两个任务（UUID）是用户在 web 端真实提交的，web 版 shots=1024（缺省，无法设置）。")
    md.append("")
    origin_dump = {}
    for fname in sorted(os.listdir(ORIGIN)):
        if fname.endswith(".json"):
            data = read_json(os.path.join(ORIGIN, fname))
            origin_dump[fname] = data
            md.append(f"### {fname}")
            md.append("")
            md.append("```json")
            md.append(json.dumps(data, ensure_ascii=False, indent=2))
            md.append("```")
            md.append("")
    dump["origin_results"] = origin_dump

    # §3 evidence
    md.append("## 3. starter_kit/evidence/ 官方模板范例（与我们的实验无关）")
    md.append("")
    md.append("> 这是官方参赛模板自带的**范例申报材料**（`starter_kit/evidence/README.md` 为模板入口，")
    md.append("> `files/` 创建时间 22:28，早于我们 22:49/22:54 的实验抓包）。")
    md.append("> README 预填的 `G-260819-0003 / S-260819-0001`、`shots=16384` 均为**模板示例内容**。")
    md.append("> 结论: 该目录与我们的实验无关，**不是伪造、也不是真实实验记录**，申报时按需替换/删除。")
    md.append("")
    evid_dump = {}
    for fname in sorted(os.listdir(EVID)):
        if fname.endswith(".json"):
            data = read_json(os.path.join(EVID, fname))
            evid_dump[fname] = data
            md.append(f"### {fname}")
            md.append("")
            md.append("```json")
            md.append(json.dumps(data, ensure_ascii=False, indent=2))
            md.append("```")
            md.append("")
    dump["evidence"] = evid_dump

    # §4 SDK
    md.append("## 4. results/spinq_sdk_20260819/ SDK 实验产物（shots=5000 可设置）")
    md.append("")
    md.append("> SDK 实验 shots=5000 提交/5000 返回、counts 整数可验，为可控实验。")
    md.append("")
    sdk_dump = {}
    for exp_dir in sorted(os.listdir(SDK)):
        full = os.path.join(SDK, exp_dir)
        if not os.path.isdir(full):
            continue
        if exp_dir.startswith("_archive_"):
            # 2026-08-20 统一 8192 shots 口径后，归档目录（旧 5000 产物）不再纳入分析
            continue
        sdk_dump[exp_dir] = {}
        md.append(f"### {exp_dir}")
        md.append("")
        for fname in sorted(os.listdir(full)):
            path = os.path.join(full, fname)
            if fname.endswith(".json"):
                data = read_json(path)
                sdk_dump[exp_dir][fname] = data
                md.append(f"#### {fname}")
                md.append("")
                md.append("```json")
                md.append(json.dumps(data, ensure_ascii=False, indent=2))
                md.append("```")
                md.append("")
            elif fname.endswith(".qasm"):
                with open(path, "r", encoding="utf-8") as f:
                    qasm = f.read()
                sdk_dump[exp_dir][fname] = qasm
                md.append(f"#### {fname}")
                md.append("")
                md.append("```")
                md.append(qasm)
                md.append("```")
                md.append("")
    dump["sdk"] = sdk_dump

    # §5 保真度对比
    bell_web_f = WEB_BELL["00"] + WEB_BELL["11"]
    ghz_web_f = WEB_GHZ["000"] + WEB_GHZ["111"]
    bell_sdk_f = (SDK_BELL["00"] + SDK_BELL["11"]) / sum(SDK_BELL.values())
    ghz_sdk_f = (SDK_GHZ["000"] + SDK_GHZ["111"]) / sum(SDK_GHZ.values())
    ghz_sdk2_f = (SDK_GHZ_2["000"] + SDK_GHZ_2["111"]) / sum(SDK_GHZ_2.values())
    ghz_sdk_pool_f = ((SDK_GHZ["000"] + SDK_GHZ["111"] + SDK_GHZ_2["000"] + SDK_GHZ_2["111"])
                      / (sum(SDK_GHZ.values()) + sum(SDK_GHZ_2.values())))
    dump["fidelity"] = {
        "bell_web_1024": round(bell_web_f, 6),
        "bell_sdk_5000": round(bell_sdk_f, 6),
        "ghz_web_1024": round(ghz_web_f, 6),
        "ghz_sdk_5000_run1": round(ghz_sdk_f, 6),
        "ghz_sdk_5000_run2": round(ghz_sdk2_f, 6),
        "ghz_sdk_5000_pooled": round(ghz_sdk_pool_f, 6),
    }
    md.append("## 5. 保真度对比表 + 双样本比例 z 检验（web 1024 vs SDK 5000，GHZ SDK 两次复测）")
    md.append("")
    md.append("| 实验 | 提交方式 | 任务号 | 机器 | shots | 保真度(00/000+11/111) |")
    md.append("|---|---|---|---|---|---|")
    md.append(f"| Bell 2比特 | web(抓包) | UUID E7599A00 | Gemini-pro-1 | 1024(缺省) | {bell_web_f*100:.2f}% |")
    md.append(f"| Bell 2比特 | SDK | G-260819-0004 | Gemini-pro-1 | 5000(设置) | {bell_sdk_f*100:.2f}% |")
    md.append(f"| GHZ 3比特 | web(抓包) | UUID 06C3076E | Triangulum-pro-1 | 1024(缺省) | {ghz_web_f*100:.2f}% |")
    md.append(f"| GHZ 3比特 | SDK #1 | S-260819-0002 | Triangulum-pro-1 | 5000(设置) | {ghz_sdk_f*100:.2f}% |")
    md.append(f"| GHZ 3比特 | SDK #2 | S-260819-0003 | Triangulum-pro-1 | 5000(设置) | {ghz_sdk2_f*100:.2f}% |")
    md.append("")
    md.append(f"差异: Bell `{(bell_web_f-bell_sdk_f)*100:.2f}pp`；")
    md.append(f"GHZ web vs SDK#1 `{(ghz_web_f-ghz_sdk_f)*100:.2f}pp`、web vs SDK#2 `{(ghz_web_f-ghz_sdk2_f)*100:.2f}pp`、")
    md.append(f"SDK 两次之间 `{(ghz_sdk_f-ghz_sdk2_f)*100:.2f}pp`。")
    md.append("")

    ghz_sdk_n = sum(SDK_GHZ.values())
    ghz_sdk2_n = sum(SDK_GHZ_2.values())
    ztests = {
        "bell_web1024_vs_sdk5000": ztest(bell_web_f, 1024, bell_sdk_f, 5000),
        "ghz_web1024_vs_sdk5000": ztest(ghz_web_f, 1024, ghz_sdk_f, 5000),
        "ghz_web1024_vs_sdk_pooled2": ztest(ghz_web_f, 1024, ghz_sdk_pool_f, ghz_sdk_n + ghz_sdk2_n),
        "ghz_sdk1_vs_sdk2": ztest(ghz_sdk_f, ghz_sdk_n, ghz_sdk2_f, ghz_sdk2_n),
    }
    dump["z_tests"] = ztests
    md.append("| 对比 | p1 | n1 | p2 | n2 | z |")
    md.append("|---|---|---|---|---|---|")
    for k, v in ztests.items():
        md.append(f"| {k} | {v['p1']:.4f} | {v['n1']} | {v['p2']:.4f} | {v['n2']} | {v['z']:.2f} |")
    md.append("")
    md.append("> 注意: 保真度是分布级 Hellinger 相似度而非单比特计数，z 检验仅作参考（比例假设不严格成立）。")
    md.append("> 差异远超统计误差（n=1024/5000 时 z 检验下差异显著），但这是**不同时段**的任务")
    md.append("> （web 22:49/22:54 vs SDK 23:08/23:17 北京），NMR 真机状态随时段波动，")
    md.append("> 单次对比不足以判定\"web 特有\"还是\"机器波动\"，需重复运行量化。")
    md.append("")

    # §6 时间线
    md.append("## 6. 时间线（UTC / 北京时间）")
    md.append("")
    md.append("| 任务 | 事件 | UTC | 北京时间 |")
    md.append("|---|---|---|---|")
    events = [
        ("starter_kit/evidence/ 范例文件", "模板创建(官方范例)", "2026-08-19T14:28Z", "≈22:28"),
        ("web 抓包 Bell UUID E7599A00", "createTime(本地)", "2026-08-19T14:49:07Z", "22:49:07"),
        ("web 抓包 GHZ UUID 06C3076E", "createTime(本地)", "2026-08-19T14:54:35Z", "22:54:35"),
        ("G-260819-0004 (SDK Bell)", "submitted", "2026-08-19T15:08:08.597995+00:00", ""),
        ("G-260819-0004 (SDK Bell)", "finished", "2026-08-19T15:09:47.119604+00:00", ""),
        ("S-260819-0002 (SDK GHZ #1)", "submitted", "2026-08-19T15:17:54.608148+00:00", ""),
        ("S-260819-0002 (SDK GHZ #1)", "finished", "2026-08-19T15:20:23.878583+00:00", ""),
        ("S-260819-0003 (SDK GHZ #2)", "submitted", "2026-08-19T15:48:35.235514+00:00", ""),
        ("S-260819-0003 (SDK GHZ #2)", "finished", "2026-08-19T15:51:09.554195+00:00", ""),
    ]
    for task, ev, ts, note in events:
        md.append(f"| {task} | {ev} | {ts} | {note or bj(ts)} |")
    md.append("")

    # §7 结论
    md.append("## 7. 结论（2026-08-19 撤回版 + GHZ#2 复核）")
    md.append("")
    md.append("1. **官方文档事实**: SpinQit Cloud 后端未配置 shots 时默认 1024（doc.spinq.cn）。")
    md.append("2. **web 版 shots=1024 缺省、不可设置；SDK 版 shots 可设置，我们跑 5000**（用户确认）。")
    md.append("3. **evidence 非伪造**: starter_kit/evidence/ 是官方模板自带的范例文件，")
    md.append("   README 预填的 job ID / shots=16384 是模板示例，与我们的实验无关。此前\"伪造\"误判已撤回。")
    md.append("4. **web vs SDK 电路与平台一致**（同 QASM：Bell `h+cx`、GHZ `h+cx+cx`；同机器型号），")
    md.append("   唯一已知区别是 shots（web 缺省 1024 不可设置 vs SDK 5000 可设置）。")
    md.append(f"5. **SDK GHZ 两次复测**: #1 {ghz_sdk_f*100:.2f}%（S-260819-0002）与 #2 {ghz_sdk2_f*100:.2f}%"
              f"（S-260819-0003），波动 {abs(ghz_sdk_f-ghz_sdk2_f)*100:.2f}pp"
              f"（z={ztests['ghz_sdk1_vs_sdk2']['z']:.2f}）。两次均明显低于 web {ghz_web_f*100:.2f}%"
              f"（差 {(ghz_web_f-ghz_sdk_f)*100:.2f}pp / {(ghz_web_f-ghz_sdk2_f)*100:.2f}pp）。")
    md.append(f"6. **结论: web 与 SDK 差异远超 SDK 自身波动**——SDK 两次合并保真度 {ghz_sdk_pool_f*100:.2f}% vs web "
              f"{ghz_web_f*100:.2f}%（差 {(ghz_web_f-ghz_sdk_pool_f)*100:.2f}pp，"
              f"z={ztests['ghz_web1024_vs_sdk_pooled2']['z']:.2f}），远大于 SDK 内部两次的波动。"
              "NMR 3 比特 GHZ 保真度约 60-66% 是该机近期常态；web 的 89.82% 与 SDK 存在系统性差异，"
              "可能源于 web 端采样/后处理差异或提交时段机器状态，需 web 端复测确认。")
    md.append("7. **Bell 差异（9.08pp）在 NMR 合理带内，不再复测**（用户决策）。")
    md.append("")

    md_text = "\n".join(md) + "\n"
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md_text)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2, default=str)
    print(f"已保存归档: {OUT_MD}")
    print(f"已保存全量 dump: {OUT_JSON}")


if __name__ == "__main__":
    main()
