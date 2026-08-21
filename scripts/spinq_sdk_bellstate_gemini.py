#!/usr/bin/env python3
"""
量旋 SpinQit SDK 真机实验：Bell state 纠缠态（2 比特）

实验配置（用户 2026-08-19 指定，2026-08-20 统一 shots 口径）：
  - 电路  : Bell state (H q0; CX q0->q1)，2 量子比特
  - shots : 8192（组织方明确要求的统一口径，2026-08-20 起取代旧 5000）
  - 机器  : gemini_vp（2Qubit核磁量子计算机，量旋云真机）

用法：
  python scripts/spinq_sdk_bellstate_gemini.py [--key ~/.ssh/id_rsa]

产物（自动落盘 results/spinq_sdk_20260819/bellstate_gemini_vp_shots8192/；旧 5000 产物已归档至 _archive_5000shots/）：
  - circuit.qasm        电路源码（OpenQASM 2.0）
  - result_raw.json     平台返回结果全量转储（task_code/counts/probabilities/shots 等）
  - result_norm.json    规范化结果（含统计汇总）

依赖：spinqit 0.2.4（~/.venvs/loomq310）
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# 账号与平台常量（账号不再硬编码，一律从 config/machines.yaml 读取，见 P0 脱敏）
from loomq_lib.machines.config_loader import get_machine

_MACHINE_CFG = get_machine("spinq_gemini_2q") or {}
SPINQ_USER = _MACHINE_CFG.get("connect", {}).get("user", "") or os.environ.get("SPINQ_USER", "")
MACHINE_PCODE = "gemini_vp"                  # 2Qubit核磁量子计算机（用户指定两比特机器）
MACHINE_NAME = "2Qubit核磁量子计算机"
DEFAULT_SHOTS = 8192
EXPERIMENT = "bellstate"


def get_output_dir(shots: int) -> str:
    """产物目录：results/spinq_sdk_20260819/{experiment}_{machine}_shots{shots}。"""
    return os.path.join("results", "spinq_sdk_20260819",
                        f"{EXPERIMENT}_{MACHINE_PCODE}_shots{shots}")


def build_bell_qc():
    """构造 Bell state 电路（2 量子比特）。

    注：量旋云平台不支持显式 measure 指令（自动在电路末尾测量），
    因此这里只用 H + CX，测量比特由 configure_measure_qubits 指定。
    """
    from spinqit import Circuit, H, CX
    circ = Circuit(name="bellstate")
    circ.allocateQubits(2)
    circ.append(H, [0])
    circ.append(CX, [0, 1])
    return circ


def qc_to_qasm() -> str:
    """返回 Bell state 的 OpenQASM 2.0 文本（存档用，与网页端/原始 msgpack 同口径）。"""
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[2];", "creg c[2];",
             "h q[0];", "cx q[0],q[1];", "measure q[0] -> c[0];", "measure q[1] -> c[1];"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="量旋 SpinQit SDK Bell state 真机实验")
    ap.add_argument("--key", default=os.path.expanduser("~/.ssh/id_rsa"),
                    help="量旋云私钥路径（默认 ~/.ssh/id_rsa）")
    ap.add_argument("--shots", type=int, default=DEFAULT_SHOTS,
                    help="重复试验次数（默认 8192）")
    args = ap.parse_args()

    out_dir = get_output_dir(args.shots)
    os.makedirs(out_dir, exist_ok=True)
    ts_submit = datetime.now(timezone.utc).isoformat()

    # 1) 电路
    from spinqit.compiler import get_compiler
    qc = build_bell_qc()
    qasm = qc_to_qasm()
    with open(os.path.join(out_dir, "circuit.qasm"), "w", encoding="utf-8") as f:
        f.write(qasm)
    print(f"[1/5] 电路已保存: {os.path.join(out_dir, 'circuit.qasm')}")

    # 2) 编译为 IR
    compiler = get_compiler("native")
    ir = compiler.compile(qc, 0)
    print(f"[2/5] 编译完成: qnum={ir.qnum}, cnum={ir.cnum}")

    # 3) 登录云平台
    from spinqit.backend import get_spinq_cloud
    from spinqit import SpinQCloudConfig
    backend = get_spinq_cloud(SPINQ_USER, args.key)
    print(f"[3/5] 登录量旋云成功, 账号={SPINQ_USER}")

    # 4) 校验两比特机器在线
    platform = backend.get_platform(MACHINE_PCODE)
    if not platform.available():
        print(f"!! 机器 {MACHINE_PCODE} 当前不在线（online={platform.machine_count}），任务只能提交排队。")
    print(f"[4/5] 目标机器: {MACHINE_PCODE} ({platform.name}, maxBit={platform.max_bitnum}, "
          f"online={platform.machine_count})")

    # 5) 配置并提交执行（同步等待结果）
    config = SpinQCloudConfig()
    config.configure_platform(MACHINE_PCODE)
    config.configure_shots(args.shots)
    config.configure_measure_qubits([0, 1])
    config.configure_task(f"bellstate_{MACHINE_PCODE}_s{args.shots}",
                          f"LoomQ Bell state via SpinQit SDK, shots={args.shots}")
    print(f"[5/5] 提交任务 (shots={args.shots}) 并等待真机结果，请耐心等待排队/采样…")
    result = backend.execute(ir, config)
    if result is None:
        print("!! 任务失败或未取到结果，请检查上方错误信息。")
        sys.exit(1)

    ts_done = datetime.now(timezone.utc).isoformat()
    counts = result.counts
    probs = result.probabilities
    shots_back = getattr(result, "_shots", None) or args.shots

    # 汇总统计
    total = sum(counts.values()) if counts else 0
    bell_ratio = (counts.get("00", 0) + counts.get("11", 0)) / total if total else None

    raw = {
        "task_code": result.task_code,
        "task_name": result.task_name,
        "platform": result.platform,
        "machine_pcode": MACHINE_PCODE,
        "machine_name": platform.name,
        "submitted_utc": ts_submit,
        "finished_utc": ts_done,
        "shots_submitted": args.shots,
        "shots_returned": shots_back,
        "counts": counts,
        "probabilities": probs,
    }
    with open(os.path.join(out_dir, "result_raw.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    norm = {
        "experiment": EXPERIMENT,
        "backend": {"sdk": "spinqit", "platform_code": MACHINE_PCODE, "platform_name": platform.name},
        "circuit": {"qasm": qasm, "qubits": 2, "gates": ["h", "cx"]},
        "shots": shots_back,
        "counts": counts,
        "probabilities": probs,
        "metrics": {
            "n_total": total,
            "bell_ratio_00_11": round(bell_ratio, 6) if bell_ratio is not None else None,
            "n_00": counts.get("00", 0),
            "n_11": counts.get("11", 0),
            "noise_01": counts.get("01", 0),
            "noise_10": counts.get("10", 0),
        },
        "task": {"code": result.task_code, "name": result.task_name},
        "timestamps": {"submitted_utc": ts_submit, "finished_utc": ts_done},
    }
    with open(os.path.join(out_dir, "result_norm.json"), "w", encoding="utf-8") as f:
        json.dump(norm, f, ensure_ascii=False, indent=2)

    # 终端汇总
    print("\n" + "=" * 60)
    print(f"任务号    : {result.task_code}")
    print(f"机器      : {MACHINE_PCODE} ({platform.name})")
    print(f"shots     : 提交 {args.shots} / 平台返回 {shots_back}")
    print(f"counts    : {counts}")
    print(f"概率      : {probs}")
    if bell_ratio is not None:
        print(f"Bell 保真度(00+11 占比): {bell_ratio:.4%}")
    print(f"产物目录  : {out_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
