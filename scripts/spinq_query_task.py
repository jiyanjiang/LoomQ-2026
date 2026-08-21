#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量旋 SpinQ 云 API 查询脚本（只读，不提交任务）

用法:
  python scripts/spinq_query_task.py [username] <task_code> [more task codes...] [--key PATH] [--host URL] [--save DIR]

示例:
  python scripts/spinq_query_task.py S-260819-0001 G-260819-0003
  python scripts/spinq_query_task.py S-260819-0001 --save /tmp/spinq_evidence

说明:
  - username 可省略：默认从 config/machines.yaml 的 spinq_gemini_2q.connect.user 读取
    （P0 脱敏：账号不再硬编码进脚本）。
  - 认证私钥默认 ~/.ssh/id_rsa（平台注册的公钥对应的那把，用 ssh-keygen -t rsa 生成），
    可通过 --key 显式指定其他私钥文件。项目里的 spinq.txt 是错误密钥，绝不再用。
  - 绕过 SDK 的 get_task() 对象解析 bug（服务端返回 bitNum=None 会崩），
    直接走原始 API get_task_by_code / task_status / task_result 取证。
  - --save DIR 会把每个任务的原始信息 JSON + 原始结果 JSON 落盘，供证据整理。
"""
import sys
import json
import os
import argparse


def _json_or_none(res):
    """把 HTTP response 转成 dict，解析失败返回 None"""
    try:
        return json.loads(res.content)
    except Exception:
        return None


def _pick(d, *keys):
    """按候选键名依次取值，兼容服务端大小写变体"""
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return None


def _field(obj, *keys):
    """从嵌套结构中提取字段：obj 可能是 dict 或 {"data": {...}}"""
    if not isinstance(obj, dict):
        return None
    for k in keys:
        if k in obj and obj[k] is not None:
            return obj[k]
    return None


def main():
    parser = argparse.ArgumentParser(description="量旋 SpinQ 云任务查询（只读）")
    parser.add_argument("username", nargs="?", default=None,
                        help="平台账号（省略时从 config/machines.yaml 的 spinq_gemini_2q.connect.user 读取）")
    parser.add_argument("task_codes", nargs="+", help="一个或多个任务编号，如 S-260819-0001")
    parser.add_argument("--key", default=os.path.expanduser("~/.ssh/id_rsa"),
                        help="认证私钥路径（默认 ~/.ssh/id_rsa）")
    parser.add_argument("--host", default="http://cloud.spinq.cn:6060", help="云平台地址")
    parser.add_argument("--save", default=None, help="若指定，把原始信息/结果 JSON 保存到该目录")
    args = parser.parse_args()

    if not args.username:
        # P0 脱敏：账号不再硬编码，省略时从 config/machines.yaml 读取
        from loomq_lib.machines.config_loader import get_machine
        _m = get_machine("spinq_gemini_2q") or {}
        args.username = _m.get("connect", {}).get("user") or os.environ.get("SPINQ_USER", "")
    if not args.username:
        print("[FATAL] 未提供平台账号，且 config/machines.yaml 未配置 spinq_gemini_2q.connect.user")
        sys.exit(1)

    if not os.path.exists(args.key):
        print(f"[FATAL] 私钥文件不存在: {args.key}")
        print("        请先用 ssh-keygen -t rsa -C 'spinq.com' 生成并把公钥注册到平台，")
        print("        或用 --key 指定其他私钥。")
        sys.exit(1)

    from spinqit.backend import get_spinq_cloud

    backend = get_spinq_cloud(args.username, args.key, args.host)
    api = backend._api_client

    if args.save:
        os.makedirs(args.save, exist_ok=True)

    for tcode in args.task_codes:
        print("=" * 70)
        print(f"[task] {tcode}")

        info = None
        try:
            res = api.get_task_by_code(tcode)
            info = _json_or_none(res)
        except Exception as e:
            print(f"  [get_task_by_code ERROR] {e}")
        if info is not None:
            print("  [task info JSON]")
            print("  " + json.dumps(info, ensure_ascii=False, indent=2).replace("\n", "\n  "))
        else:
            print("  [task info] 解析失败（无返回或非 JSON）")

        status = None
        try:
            res = api.task_status(tcode)
            status = _json_or_none(res)
        except Exception as e:
            print(f"  [task_status ERROR] {e}")
        if status is not None:
            print("  [status JSON]")
            print("  " + json.dumps(status, ensure_ascii=False, indent=2).replace("\n", "\n  "))
        else:
            print("  [status] 解析失败（无返回或非 JSON）")

        result = None
        try:
            res = api.task_result(tcode)
            result = _json_or_none(res)
        except Exception as e:
            print(f"  [task_result ERROR] {e}")
        if result is not None:
            print("  [result JSON]")
            print("  " + json.dumps(result, ensure_ascii=False, indent=2).replace("\n", "\n  "))
        else:
            print("  [result] 解析失败（无返回或非 JSON）")

        if args.save:
            safe = tcode.replace("/", "_")
            with open(os.path.join(args.save, f"{safe}.info.json"), "w") as f:
                json.dump({"task_code": tcode, "info": info, "status": status},
                          f, ensure_ascii=False, indent=2)
            with open(os.path.join(args.save, f"{safe}.result.json"), "w") as f:
                json.dump({"task_code": tcode, "result": result},
                          f, ensure_ascii=False, indent=2)
            print(f"  [saved] {args.save}/{safe}.info.json + {safe}.result.json")


if __name__ == "__main__":
    main()
