#!/usr/bin/env python3
"""
量旋 SpinQit SDK 真机实验：GHZ 三比特纠缠态

实验配置（用户 2026-08-19 指定，2026-08-20 统一 shots 口径）：
  - 电路  : GHZ3 (H q0; CX q0->q1; CX q1->q2)，3 量子比特
  - shots : 8192（组织方明确要求的统一口径，2026-08-20 起取代旧 5000）
  - 机器  : triangulum_vp（3Qubit核磁量子计算机，量旋云真机）

用法：
  python scripts/spinq_sdk_ghz_triangulum.py [--key ~/.ssh/id_rsa] [--tag ghz_state_2]
  python scripts/spinq_sdk_ghz_triangulum.py --selfcheck-only [--tag ghz_state_2]

产物（自动落盘 results/spinq_sdk_20260819/ghz_triangulum_vp_shots8192/；
      带 --tag 时落盘 results/spinq_sdk_20260819/{tag}/；旧 5000 产物已归档至 _archive_5000shots/）：
  - circuit.qasm        电路源码（OpenQASM 2.0）
  - result_raw.json     平台返回结果全量转储（task_code/counts/probabilities/shots 等）
  - result_norm.json    规范化结果（含统计汇总 + 自检）
  - selfcheck.json      自检报告（shots 一致性 / counts 合计 / GHZ 保真度 / 产物齐全）

依赖：spinqit 0.2.4（~/.venvs/loomq310）
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# 账号不再硬编码，一律从 config/machines.yaml 读取（见 P0 脱敏）
from loomq_lib.machines.config_loader import get_machine

_MACHINE_CFG = get_machine("spinq_triangulum_3q") or {}
SPINQ_USER = _MACHINE_CFG.get("connect", {}).get("user", "") or os.environ.get("SPINQ_USER", "")
MACHINE_PCODE = "triangulum_vp"             # 3Qubit核磁量子计算机（用户指定三比特机器）
DEFAULT_SHOTS = 8192
EXPERIMENT = "ghz"

EXPECTED = {"000", "111"}                   # GHZ3 理论非零输出位串


def get_output_dir(tag=None, shots=DEFAULT_SHOTS):
    """产物目录：缺省 ghz_triangulum_vp_shots{shots}；--tag 时以标签命名（如 ghz_state_2）。"""
    if tag:
        return os.path.join("results", "spinq_sdk_20260819", tag)
    return os.path.join("results", "spinq_sdk_20260819",
                        f"{EXPERIMENT}_{MACHINE_PCODE}_shots{shots}")


def build_ghz_qc():
    """构造 GHZ3 电路（H q0; CX q0->q1; CX q1->q2）。"""
    from spinqit import Circuit, H, CX
    circ = Circuit(name="ghz3")
    circ.allocateQubits(3)
    circ.append(H, [0])
    circ.append(CX, [0, 1])
    circ.append(CX, [1, 2])
    return circ


def qc_to_qasm() -> str:
    """GHZ3 的 OpenQASM 2.0 文本（存档用）。"""
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[3];", "creg c[3];",
             "h q[0];", "cx q[0],q[1];", "cx q[1],q[2];",
             "measure q[0] -> c[0];", "measure q[1] -> c[1];", "measure q[2] -> c[2];"]
    return "\n".join(lines) + "\n"


def run_selfcheck(meta: dict, out: dict, out_dir: str) -> dict:
    """自检：产物齐全 / shots 一致性 / counts 合计 / 理论保真度 / 噪声分布。"""
    checks = []
    ok = True

    for f in ("circuit.qasm", "result_raw.json", "result_norm.json"):
        path = os.path.join(out_dir, f)
        exists = os.path.isfile(path)
        checks.append({"item": f"产物存在 {f}", "pass": exists,
                       "detail": "存在" if exists else "缺失"})
        ok = ok and exists

    counts = out.get("counts", {})
    total = sum(counts.values())
    diff = abs(total - meta["shots_returned"])
    checks.append({"item": "counts 合计 ≈ shots (允许±1硬件偏差)",
                   "pass": diff <= 1,
                   "detail": f"合计 {total} vs shots {meta['shots_returned']} (偏差 {diff})"})
    ok = ok and (diff <= 1)

    checks.append({"item": "shots 平台返回 == 提交值", "pass": meta["shots_returned"] == meta["shots_submitted"],
                   "detail": f"{meta['shots_returned']} vs {meta['shots_submitted']}"})
    ok = ok and (meta["shots_returned"] == meta["shots_submitted"])

    ghz_ratio = out["metrics"]["ghz_ratio_000_111"]
    checks.append({"item": "GHZ 保真度 (000+111)/N > 50%", "pass": ghz_ratio > 0.5,
                   "detail": f"{ghz_ratio:.4%}"})
    ok = ok and (ghz_ratio > 0.5)

    ghost = {k: v for k, v in counts.items() if k not in EXPECTED}
    ghost_total = sum(ghost.values())
    checks.append({"item": "噪声位串占比 < 50%", "pass": ghost_total < total * 0.5,
                   "detail": f"{ghost_total} ({ghost_total/total:.4%}) 噪声: {ghost}"})
    ok = ok and (ghost_total < total * 0.5)

    return {"overall_pass": ok, "checks": checks}


def main():
    ap = argparse.ArgumentParser(description="量旋 SpinQit SDK GHZ3 真机实验")
    ap.add_argument("--key", default=os.path.expanduser("~/.ssh/id_rsa"),
                    help="量旋云私钥路径（默认 ~/.ssh/id_rsa）")
    ap.add_argument("--tag", default=None,
                    help="实验标签（如 ghz_state_2），重复实验区分批次；缺省目录为 ghz_triangulum_vp_shots8192")
    ap.add_argument("--selfcheck-only", action="store_true",
                    help="只读已有产物补跑自检，不提交任务")
    ap.add_argument("--shots", type=int, default=DEFAULT_SHOTS,
                    help="重复试验次数（默认 8192）")
    args = ap.parse_args()

    out_dir = get_output_dir(args.tag, args.shots)

    if args.selfcheck_only:
        raw = json.load(open(os.path.join(out_dir, "result_raw.json"), encoding="utf-8"))
        norm = json.load(open(os.path.join(out_dir, "result_norm.json"), encoding="utf-8"))
        sc = run_selfcheck(raw, norm, out_dir)
        with open(os.path.join(out_dir, "selfcheck.json"), "w", encoding="utf-8") as f:
            json.dump(sc, f, ensure_ascii=False, indent=2)
        print(f"任务号    : {raw['task_code']}")
        print(f"机器      : {raw['machine_pcode']} ({raw['machine_name']})")
        print(f"自检      : {'通过 ✔' if sc['overall_pass'] else '未通过 ✘'}")
        for c in sc["checks"]:
            print(f"  [{'✔' if c['pass'] else '✘'}] {c['item']}: {c['detail']}")
        print(f"自检报告  : {os.path.join(out_dir, 'selfcheck.json')}")
        sys.exit(0 if sc["overall_pass"] else 1)

    os.makedirs(out_dir, exist_ok=True)
    ts_submit = datetime.now(timezone.utc).isoformat()

    # 1) 电路
    from spinqit.compiler import get_compiler
    qc = build_ghz_qc()
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

    # 4) 校验三比特机器在线
    platform = backend.get_platform(MACHINE_PCODE)
    if not platform.available():
        print(f"!! 机器 {MACHINE_PCODE} 当前不在线（online={platform.machine_count}），任务将排队。")
    print(f"[4/5] 目标机器: {MACHINE_PCODE} ({platform.name}, maxBit={platform.max_bitnum}, "
          f"online={platform.machine_count})")

    # 5) 配置并提交执行（同步等待结果）
    config = SpinQCloudConfig()
    config.configure_platform(MACHINE_PCODE)
    config.configure_shots(args.shots)
    config.configure_measure_qubits([0, 1, 2])
    task_name = f"ghz3_{MACHINE_PCODE}_s{args.shots}"
    if args.tag:
        task_name = f"{task_name}_{args.tag}"
    config.configure_task(task_name,
                          f"LoomQ GHZ3 via SpinQit SDK, shots={args.shots}, tag={args.tag or 'default'}")
    print(f"[5/5] 提交任务 (shots={args.shots}) 并等待真机结果，请耐心等待排队/采样…")
    result = backend.execute(ir, config)
    if result is None:
        print("!! 任务失败或未取到结果，请检查上方错误信息。")
        sys.exit(1)

    ts_done = datetime.now(timezone.utc).isoformat()
    counts = result.counts
    probs = result.probabilities
    shots_back = getattr(result, "_shots", None) or args.shots

    total = sum(counts.values()) if counts else 0
    ghz_ratio = (counts.get("000", 0) + counts.get("111", 0)) / total if total else None

    meta = {
        "task_code": result.task_code,
        "task_name": result.task_name,
        "machine_pcode": MACHINE_PCODE,
        "machine_name": platform.name,
        "submitted_utc": ts_submit,
        "finished_utc": ts_done,
        "shots_submitted": args.shots,
        "shots_returned": shots_back,
    }
    raw = dict(meta)
    raw.update({"counts": counts, "probabilities": probs})
    with open(os.path.join(out_dir, "result_raw.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

    norm = {
        "experiment": EXPERIMENT,
        "backend": {"sdk": "spinqit", "platform_code": MACHINE_PCODE, "platform_name": platform.name},
        "circuit": {"qasm": qasm, "qubits": 3, "gates": ["h", "cx", "cx"]},
        "shots": shots_back,
        "counts": counts,
        "probabilities": probs,
        "metrics": {
            "n_total": total,
            "ghz_ratio_000_111": round(ghz_ratio, 6) if ghz_ratio is not None else None,
            "n_000": counts.get("000", 0),
            "n_111": counts.get("111", 0),
        },
        "task": {"code": result.task_code, "name": result.task_name},
        "timestamps": {"submitted_utc": ts_submit, "finished_utc": ts_done},
    }
    with open(os.path.join(out_dir, "result_norm.json"), "w", encoding="utf-8") as f:
        json.dump(norm, f, ensure_ascii=False, indent=2)

    # 自检
    selfcheck = run_selfcheck(meta, norm, out_dir)
    with open(os.path.join(out_dir, "selfcheck.json"), "w", encoding="utf-8") as f:
        json.dump(selfcheck, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"任务号    : {result.task_code}")
    print(f"机器      : {MACHINE_PCODE} ({platform.name})")
    print(f"shots     : 提交 {args.shots} / 平台返回 {shots_back}")
    print(f"counts    : {counts}")
    print(f"概率      : {probs}")
    if ghz_ratio is not None:
        print(f"GHZ 保真度(000+111 占比): {ghz_ratio:.4%}")
    print(f"自检      : {'通过 ✔' if selfcheck['overall_pass'] else '未通过 ✘'}")
    for c in selfcheck["checks"]:
        print(f"  [{'✔' if c['pass'] else '✘'}] {c['item']}: {c['detail']}")
    print(f"产物目录  : {out_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
