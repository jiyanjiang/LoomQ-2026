#!/usr/bin/env python3
"""L1 正式自检验收：cases.yaml 全量电路 × 三后端。

流程：
  1. 读 tests/cases.yaml 用例清单
  2. 每个电路用"尺子"(qasm_semantics)算精确参考分布
  3. 三后端 adapter.run() 实测 counts → 归一化
  4. Hellinger 比对（≥0.97 PASS）+ schema 校验
  5. 汇总报告 + JSON 落盘

用法：source ~/.venvs/loomq310/bin/activate && python tests/run_test_suite.py
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter_kit"))
sys.path.insert(0, str(ROOT / "tests"))

import yaml  # noqa: E402
import adapter  # noqa: E402
from qasm_semantics import reference_distribution  # noqa: E402

SHOTS = 8192
FID_THRESHOLD = 0.97
TARGETS = ("spinq", "originq", "braket")


def hellinger(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    d = math.sqrt(sum((math.sqrt(p.get(k, 0)) - math.sqrt(q.get(k, 0))) ** 2 for k in keys)) / math.sqrt(2)
    return max(0.0, min(1.0, 1.0 - d))


def validate_schema(result: dict) -> tuple:
    required = ("backend", "job_id", "shots", "counts", "bit_order", "timestamp")
    missing = [f for f in required if f not in result]
    if missing:
        return False, f"缺字段: {missing}"
    if not isinstance(result["counts"], dict) or not result["counts"]:
        return False, "counts 空"
    if sum(result["counts"].values()) != result["shots"]:
        return False, "counts 总和不等于 shots"
    if result["bit_order"] != "little":
        return False, "bit_order 非 little"
    for k in result["counts"]:
        if set(k) - {"0", "1"}:
            return False, f"counts key 非法: {k}"
    return True, "schema 有效"


def resolve_circuit(case: dict) -> Path | None:
    rel = case.get("circuit", "")
    for base in (ROOT / "tests" / "circuits", ROOT / "starter_kit" / "circuits"):
        p = base / rel
        if p.exists():
            return p
    return None


def main() -> int:
    cases_path = ROOT / "tests" / "cases.yaml"
    spec = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    cases = spec["cases"]

    total = passed = failed = 0
    results = {"cases": []}
    summary_rows = []

    for case in cases:
        cid = case["id"]
        path = resolve_circuit(case)
        if path is None:
            results["cases"].append({"id": cid, "status": "SKIP", "reason": "缺电路文件"})
            continue
        qasm = path.read_text(encoding="utf-8")
        try:
            ref = reference_distribution(qasm)
        except Exception as e:
            results["cases"].append({"id": cid, "status": "ERROR", "reason": f"尺子失败: {e}"})
            continue
        row = {"id": cid, "kind": case["kind"], "circuit": case["circuit"],
               "covers": case["covers"], "reference": ref, "targets": {}}
        row_ok = True
        for t in TARGETS:
            total += 1
            try:
                r = adapter.run(qasm, t, SHOTS)
                valid, msg = validate_schema(r)
                if not valid:
                    row["targets"][t] = {"status": "FAIL", "reason": msg}
                    row_ok = False
                    failed += 1
                    continue
                obs = {k: v / SHOTS for k, v in r["counts"].items()}
                fid = hellinger(ref, obs)
                ok = fid >= FID_THRESHOLD
                row["targets"][t] = {"status": "PASS" if ok else "FAIL",
                                     "fidelity": round(fid, 4),
                                     "counts_sample": dict(list(r["counts"].items())[:4])}
                row_ok = row_ok and ok
                passed += ok
                failed += (not ok)
            except Exception as e:
                row["targets"][t] = {"status": "ERROR", "reason": f"{type(e).__name__}: {str(e)[:80]}"}
                row_ok = False
                failed += 1
        row["status"] = "PASS" if row_ok else "FAIL"
        results["cases"].append(row)
        status = "✓" if row_ok else "✗"
        per = " ".join(f"{t}:{row['targets'][t].get('status','?')[:4]}({row['targets'][t].get('fidelity','-')})" for t in TARGETS)
        print(f"{status} {cid:16s} {per}")
        summary_rows.append(f"{cid}: {'PASS' if row_ok else 'FAIL'} {per}")

    results["summary"] = {"total": total, "passed": passed, "failed": failed,
                          "cases_total": len(cases),
                          "cases_passed": sum(1 for c in results["cases"] if c.get("status") == "PASS")}
    out = ROOT / "tests" / "test_suite_report.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 汇总: 用例级 {results['summary']['cases_passed']}/{results['summary']['cases_total']} 通过; "
          f"后端级 {passed}/{total} 通过 ===")
    print(f"报告: {out}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
