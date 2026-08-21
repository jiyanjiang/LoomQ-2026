#!/usr/bin/env python3
"""
本源量子云真机实验：Bell state 纠缠态（2 比特）· 本源悟空 180 · v2 修正版

实验配置（用户 2026-08-20 指定）：
  - 电路  : Bell state (H q0; CNOT q0->q1)，2 量子比特
  - shots : 8192（参数化，--shots 可改任意值）
  - 机器  : 本源悟空 180（chip_id=180，第四代 180 比特超导真机，
            经 console.originqc.com.cn/api/taskApi/getFullConfig.json?chipId=180 探测确认唯一有效 ID）

v2 修正（2026-08-20，任务 3A0E51C7E2002327618EC4B3342F2826 云上失败后修复）：
  - 失败错误 : "QProq pre-estimate error: Error: not measure node"
  - 根因     : pyqpanda convert_qasm_string_to_originir 把 `measure q -> c`
               输出为整寄存器 `MEASURE q,c`，司南系统解析器不认此语法，
               判定电路无测量节点 → pre-estimate 失败。
  - 修复     : 弃用该转换器，复用项目已验证的 starter_kit/adapter.py::_qasm2_to_originir，
               输出契约格式（target_ir_contract.md §originq）逐比特测量：
               MEASURE q[0], c[0] / MEASURE q[1], c[1]。
  - 结果目录 : results/originq_20260820/bellstate_wukong180_shots8192_v2/（与失败版隔离）

设计：提交 / 轮询 两步分离（真机排队可达小时级，避免单次命令阻塞超时）：
  python scripts/originq_bellstate_wukong180.py --mode submit   # 提交并落盘 task.json
  python scripts/originq_bellstate_wukong180.py --mode poll     # 查询任务状态，完成则落盘结果
  python scripts/originq_bellstate_wukong180.py --mode run      # submit + 自动轮询直到完成（默认）

产物（results/originq_20260820/bellstate_wukong180_shots8192_v2/）：
  - circuit.qasm     电路源码（OpenQASM 2.0，存档）
  - task.json        提交信息（task_id / 时间戳 / 机器 / shots）
  - result_raw.json  平台返回结果全量转储
  - result_norm.json 规范化结果（含统计汇总）
  - selfcheck.json   自检

依赖：pyqpanda 3.8.5（~/.venvs/loomq310），API Token 在 config.yaml 的 originq_api_token 键
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

# ---- 项目常量 ----
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHIP_ID_WUKONG180 = 180          # 本源悟空 180（getFullConfig 探测确认）
MACHINE_NAME = "本源悟空 180（180 比特超导真机）"
EXPERIMENT = "bellstate"

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT, "results", "originq_20260820",
    f"{EXPERIMENT}_wukong180_shots{0}_v2",  # shots 由下方真实值覆盖
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_token() -> str:
    """从 config.yaml 提取本源量子云 API Token（只读，不修改文件）。"""
    cfg = os.path.join(PROJECT_ROOT, "config.yaml")
    if not os.path.exists(cfg):
        sys.exit(f"!! 未找到 {cfg}")
    token = ""
    with open(cfg, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("originq_api_token:"):
                token = line.partition(":")[2].strip().strip('"').strip("'")
                break
    if not token:
        sys.exit("!! config.yaml 中未找到本源量子云 'originq_api_token'")
    return token


def build_bell_originir() -> str:
    """Bell state 的 OriginIR 字符串（本源中间表示，提交载体）。

    注1：用 QASM → OriginIR 转换而非 QProg 直传，实测 pyqpanda 3.8.5 在
    真机提交时对 QProg 序列化会段错误（exit 139）；字符串载体稳定。
    注2（v2 修复）：弃用 pyqpanda convert_qasm_string_to_originir——它把
    `measure q -> c` 原样输出为整寄存器 `MEASURE q,c`，司南系统解析器不认，
    报 "not measure node"（任务 3A0E51C7 实测失败）。改用项目已验证的
    starter_kit/adapter.py::_qasm2_to_originir，输出契约格式逐比特测量
    `MEASURE q[0], c[0] / MEASURE q[1], c[1]`。
    """
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "starter_kit"))
    from adapter import _qasm2_to_originir  # 仅标准库依赖，可独立 import
    return _qasm2_to_originir(bell_qasm())


def bell_qasm() -> str:
    """Bell state 的 OpenQASM 2.0 文本（存档用，与 starter_kit/circuits/bell.qasm 同口径）。"""
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        "qreg q[2];",
        "creg c[2];",
        "h q[0];",
        "cx q[0],q[1];",
        "measure q -> c;",
        "",
    ]
    return "\n".join(lines)


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def cmd_submit(args, token):
    """提交任务，落盘 task.json，返回 task_id。"""
    from pyqpanda import QCloud
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    qasm = bell_qasm()
    with open(os.path.join(OUTPUT_DIR, "circuit.qasm"), "w", encoding="utf-8") as f:
        f.write(qasm)
    print(f"[1/4] 电路已保存: {os.path.join(OUTPUT_DIR, 'circuit.qasm')}")

    ir = build_bell_originir()
    print(f"[2/4] OriginIR 构建完成: H q0; CNOT q0,q1; Measure x2")
    print(f"      {ir.strip()}")

    qc = QCloud()
    qc.init_qvm(token)
    print(f"[3/4] 云连接已初始化 (Authorization: oqcs_auth=...)")

    task_name = args.task_name
    print(f"[4/4] 提交任务 chip_id={args.chip_id} shots={args.shots} "
          f"task_name={task_name}，等待平台返回 task_id…")
    task_id = qc.async_real_chip_measure(
        ir, args.shots, chip_id=args.chip_id,
        is_amend=True, is_mapping=True, is_optimization=True,
        task_name=task_name,
    )
    print(f"      任务已提交成功，task_id={task_id}")

    task = {
        "task_id": task_id,
        "experiment": EXPERIMENT,
        "machine": {"chip_id": args.chip_id, "name": MACHINE_NAME},
        "shots": args.shots,
        "task_name": task_name,
        "circuit": {"qasm": qasm, "qubits": 2, "gates": ["h", "cx"]},
        "timestamps": {"submitted_utc": _ts()},
        "status": "submitted",
    }
    _write_json(os.path.join(OUTPUT_DIR, "task.json"), task)
    print(f"      task.json 已落盘: {OUTPUT_DIR}")
    return task_id


def cmd_poll(args, token, max_wait_s=None):
    """查询任务状态。完成则落盘结果并返回 True；未完成返回 False。"""
    from pyqpanda import QCloud
    task_path = os.path.join(OUTPUT_DIR, "task.json")
    if not os.path.exists(task_path):
        sys.exit(f"!! 未找到 {task_path}，请先运行 --mode submit")
    with open(task_path, "r", encoding="utf-8") as f:
        task = json.load(f)
    task_id = task["task_id"]

    qc = QCloud()
    qc.init_qvm(token)

    t0 = time.time()
    while True:
        try:
            status, result = qc.query_task_state_result(task_id)
        except Exception as e:
            print(f"!! 查询异常（重试）: {e}")
            status = None
            result = None

        # pyqpanda TaskStatus 枚举：1=WAITING 2=COMPUTING 3=FINISHED 4=FAILED
        # （v2 修正：曾误用 {2:FINISHED, 3:FAILED}，导致 FINISHED(3) 被误报失败）
        state_name = {1: "WAITING", 2: "COMPUTING", 3: "FINISHED", 4: "FAILED"}.get(status, str(status))
        print(f"    [{_ts()}] 任务 {task_id} 状态={state_name}")

        if status == 3:  # TaskStatus::FINISHED
            return _finalize(task, result)
        if status == 4:  # TaskStatus::FAILED
            task["status"] = "failed"
            task["timestamps"]["finished_utc"] = _ts()
            _write_json(task_path, task)
            sys.exit(f"!! 任务 {task_id} 失败")
        if max_wait_s and (time.time() - t0) > max_wait_s:
            print(f"!! 等待超时（{max_wait_s/60:.0f} 分钟），任务仍在排队/运行。")
            print(f"   稍后重跑本命令即可续查: python scripts/originq_bellstate_wukong180.py --mode poll")
            return False
        time.sleep(args.poll_interval)


def _finalize(task, result):
    """结果落盘 + 统计 + 终端汇总。result 为概率 dict（key=位串）。"""
    shots = task["shots"]
    task_id = task["task_id"]
    ts_done = _ts()

    # 平台返回概率 dict；自适应识别 counts 形式（总和≈shots 的整数）或概率形式（总和≈1）
    probs = dict(result)
    total = sum(probs.values())
    is_counts_form = total > 1.5 and all(abs(v - round(v)) < 1e-9 for v in probs.values())
    if is_counts_form:
        counts = {k: int(round(v)) for k, v in probs.items()}
        probs_norm = {k: v / total for k, v in counts.items()}
    else:
        probs_norm = probs
        counts = {k: round(v * shots) for k, v in probs.items()}

    n_00 = counts.get("00", 0)
    n_11 = counts.get("11", 0)
    n_01 = counts.get("01", 0)
    n_10 = counts.get("10", 0)
    n_total = sum(counts.values())
    bell_ratio = (n_00 + n_11) / n_total if n_total else None

    task["status"] = "finished"
    task["timestamps"]["finished_utc"] = ts_done
    _write_json(os.path.join(OUTPUT_DIR, "task.json"), task)

    raw = {
        "task_id": task_id,
        "machine": task["machine"],
        "shots_submitted": shots,
        "shots_returned": n_total,
        "submitted_utc": task["timestamps"]["submitted_utc"],
        "finished_utc": ts_done,
        "result_prob": probs_norm,
    }
    _write_json(os.path.join(OUTPUT_DIR, "result_raw.json"), raw)

    norm = {
        "experiment": EXPERIMENT,
        "backend": {"sdk": "pyqpanda", "chip_id": task["machine"]["chip_id"],
                    "machine_name": task["machine"]["name"]},
        "circuit": task["circuit"],
        "shots": shots,
        "counts": counts,
        "probabilities": probs_norm,
        "metrics": {
            "n_total": n_total,
            "bell_ratio_00_11": round(bell_ratio, 6) if bell_ratio is not None else None,
            "n_00": n_00,
            "n_11": n_11,
            "noise_01": n_01,
            "noise_10": n_10,
        },
        "task": {"id": task_id, "name": task["task_name"]},
        "timestamps": {"submitted_utc": task["timestamps"]["submitted_utc"], "finished_utc": ts_done},
    }
    _write_json(os.path.join(OUTPUT_DIR, "result_norm.json"), norm)

    # selfcheck
    checks = []
    ok = True
    if n_total == shots:
        checks.append(("shots 完整性", True, f"返回 {n_total} == 提交 {shots}"))
    else:
        ok = False
        checks.append(("shots 完整性", False, f"返回 {n_total} != 提交 {shots}"))
    if bell_ratio is not None and bell_ratio >= 0.9:
        checks.append(("Bell 保真度", True, f"{bell_ratio:.4%} >= 90%"))
    else:
        ok = False
        checks.append(("Bell 保真度", False, f"{bell_ratio:.4%} < 90%"))
    if n_00 + n_11 == n_total:
        checks.append(("零噪声", True, f"01/10 计数 = {n_01}+{n_10} = 0"))
    else:
        ok = False
        checks.append(("零噪声", False, f"存在噪声位串 01={n_01} 10={n_10}"))
    _write_json(os.path.join(OUTPUT_DIR, "selfcheck.json"),
                {"passed": ok, "checks": checks, "checked_utc": _ts()})

    print("\n" + "=" * 64)
    print(f"任务号    : {task_id}")
    print(f"机器      : {MACHINE_NAME} (chip_id={task['machine']['chip_id']})")
    print(f"shots     : 提交 {shots} / 平台返回 {n_total}")
    print(f"counts    : {counts}")
    print(f"概率      : {probs_norm}")
    if bell_ratio is not None:
        print(f"Bell 保真度(00+11 占比): {bell_ratio:.4%}")
    print(f"自检      : {'通过' if ok else '未全过（见 selfcheck.json）'}")
    print(f"产物目录  : {OUTPUT_DIR}")
    print("=" * 64)
    return True


def main():
    ap = argparse.ArgumentParser(description="本源悟空 180 真机 Bell state 实验")
    ap.add_argument("--mode", choices=["submit", "poll", "run"], default="run",
                    help="submit=提交落盘task_id; poll=查询状态/取结果; run=提交+自动轮询（默认）")
    ap.add_argument("--shots", type=int, default=8192, help="测量次数（默认 8192，可改任意值）")
    ap.add_argument("--chip-id", type=int, default=CHIP_ID_WUKONG180,
                    help="本源云真机 chip_id（默认 180 = 本源悟空 180）")
    ap.add_argument("--task-name", default="LoomQ_bellstate_v2_s8192",
                    help="云平台任务名（平台限制 ≤31 字符，勿超长）")
    ap.add_argument("--poll-interval", type=int, default=60,
                    help="轮询间隔秒（默认 60）")
    ap.add_argument("--poll-max-min", type=int, default=240,
                    help="run 模式最长等待分钟数（默认 240，超时后手动 poll 续查）")
    args = ap.parse_args()

    global OUTPUT_DIR
    OUTPUT_DIR = os.path.join(
        PROJECT_ROOT, "results", "originq_20260820",
        f"{EXPERIMENT}_wukong180_shots{args.shots}_v2",
    )

    token = load_token()

    if args.mode in ("submit", "run"):
        cmd_submit(args, token)
        if args.mode == "submit":
            print("已提交。排队可能小时级，稍后运行 --mode poll 查询/取结果。")
            return

    if args.mode in ("poll", "run"):
        max_wait_s = args.poll_max_min * 60 if args.mode == "run" else None
        done = cmd_poll(args, token, max_wait_s=max_wait_s)
        if args.mode == "run" and not done:
            sys.exit(1)


if __name__ == "__main__":
    main()
