#!/usr/bin/env python3
"""LoomQ Web 工作台（Flask 应用）。

布局（CodeBuddy 风格两栏）：
  最左：活动栏（电路库/文档/设置/账号 图标）
  左侧：主区域（电路图 + QASM + 通俗讲解 + 结果）
  右上：执行过程要点（LLM 过程/各后端 fidelity）
  右下：对话框（LLM 对话）

启动：bash web/run_web.sh（或手动设 DYLD_LIBRARY_PATH 后 python web/app.py）
"""

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# macOS 26 + Python 3.10：必须在导入 spinqit 前设置 DYLD_LIBRARY_PATH
# （brew expat 修 pyexpat；spinqit 包目录修 dylib 加载；绕过 shell 继承问题）
_VENV = Path.home() / ".venvs" / "loomq310" / "lib" / "python3.10" / "site-packages"
_dyld_parts = ["/opt/homebrew/opt/expat/lib", str(_VENV / "spinqit")]
_dyld_parts += [p for p in os.environ.get("DYLD_LIBRARY_PATH", "").split(":") if p]
os.environ["DYLD_LIBRARY_PATH"] = ":".join(_dyld_parts)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "loomq_lib"))
sys.path.insert(0, str(ROOT / "public" / "scripts"))

from flask import Flask, jsonify, render_template, request  # noqa: E402

import key_loader  # noqa: E402
import loomq_lib  # noqa: E402
from web import content  # noqa: E402
from web import qc_dict  # noqa: E402
from loomq_lib.noise import noisy_counts, machine_education  # noqa: E402
from loomq_lib.machines import config_loader, status_ping  # noqa: E402

app = Flask(__name__)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/circuits", methods=["GET"])
def api_circuits():
    """电路库列表（含讲解）。"""
    items = []
    for cid in loomq_lib.ALL_IDS:
        info = loomq_lib.get_info(cid)
        if info["kind"] == "gate":
            # id 形如 g01_x → 门名 x；映射到 content.GATES
            gate_id = cid.split("_", 1)[1] if "_" in cid else cid
            explain = content.GATES.get(gate_id, {})
            item = {"id": cid, "kind": "gate", "name": explain.get("name", info["description"]),
                    "plain": explain.get("plain", ""), "analogy": explain.get("analogy", ""),
                    "fun_fact": explain.get("fun_fact", ""), "covers": info["covers"]}
        else:
            explain = content.ALGORITHMS.get(cid, {})
            item = {"id": cid, "kind": "algo", "name": explain.get("name", info["description"]),
                    "plain": explain.get("plain", ""), "why": explain.get("why", ""),
                    "result": explain.get("result", ""), "covers": info["covers"]}
        item["qasm"] = loomq_lib.get_qasm(cid)
        items.append(item)
    return jsonify(items)


@app.route("/api/machines", methods=["GET"])
def api_machines():
    """4 台机器定义 + 词典。"""
    machines = []
    for mid, m in qc_dict.MACHINES.items():
        edu = machine_education(mid)
        machines.append({"id": mid, **m, "education": edu["msg"]})
    return jsonify({
        "machines": machines,
        "tech_terms": qc_dict.TECH_TERMS,
        "people": qc_dict.PEOPLE,
        "concepts": qc_dict.CONCEPTS,
    })


_MACHINE_STATUS_TTL = 3600.0  # 真机在线状态缓存 1h（首页刷新不重复打真机）
_MACHINE_STATUS_CACHE: dict = {"ts": 0.0, "checked_at": "", "items": []}
_MACHINE_STATUS_LOCK = threading.Lock()


@app.route("/api/machines/status", methods=["GET"])
def api_machines_status():
    """三台量子真机在线状态（首页驾驶舱）：driver 只读探活 + 1h 内存缓存。

    只做只读 ping：spinq = SDK 登录 + 机型可用性；wukong = token 校验 + 芯片拓扑
    查询。绝不 submit 作业，不消耗悟空收费机时。任何失败降级为 offline+原因。
    """
    with _MACHINE_STATUS_LOCK:
        if _MACHINE_STATUS_CACHE["items"] and time.time() - _MACHINE_STATUS_CACHE["ts"] < _MACHINE_STATUS_TTL:
            return jsonify({"cached": True, "checked_at": _MACHINE_STATUS_CACHE["checked_at"],
                            "machines": _MACHINE_STATUS_CACHE["items"]})
    ms = config_loader.available_machines()
    items = status_ping.ping_machines(ms)
    for it, m in zip(items, ms):
        it["name"] = m.get("name") or it["id"]
        it["vendor"] = m.get("vendor") or ""
        it["phys"] = m.get("phys") or ""
        it["bits"] = m.get("bits") or 0
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    with _MACHINE_STATUS_LOCK:
        _MACHINE_STATUS_CACHE.update({"ts": time.time(), "checked_at": now, "items": items})
    return jsonify({"cached": False, "checked_at": now, "machines": items})


@app.route("/api/run", methods=["POST"])
def api_run():
    """执行电路：指定 target（或三后端全跑），可选带噪声的机器模拟（L3）。"""
    data = request.get_json(force=True)
    qasm = data.get("qasm", "")
    target = data.get("target", "all")  # all = 三后端
    shots = int(data.get("shots", 8192))
    machine = data.get("machine")        # L3：ideal/linear/grid/noisy

    if not qasm:
        return jsonify({"error": "qasm 为空"}), 400
    ok, err = loomq_lib.validate_qasm(qasm)
    if not ok:
        return jsonify({"error": err}), 400

    # L3：噪声机器模拟（在教育目录下显示）
    if machine:
        if machine not in ("ideal", "linear", "grid", "noisy"):
            return jsonify({"error": f"未知机器: {machine}"}), 400
        try:
            counts = noisy_counts(qasm, machine, shots)
            ref = loomq_lib.reference_distribution(qasm)
            total = sum(counts.values())
            obs = {k: v / total for k, v in counts.items()}
            fid = loomq_lib.hellinger(ref, obs)
            edu = machine_education(machine)
            return jsonify({"results": {machine: {
                "backend": f"noisy_sim_{machine}",
                "job_id": f"noisy-{machine}",
                "shots": shots, "counts": counts, "bit_order": "little",
                "reference": ref, "fidelity": round(fid, 4),
                "passed": fid >= 0.97, "education": edu["msg"],
            }}, "all_pass": fid >= 0.97, "noisy": True, "machine": machine})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    if target == "all":
        result = loomq_lib.verify_all_targets(qasm, shots)
    else:
        try:
            r = loomq_lib.run_circuit(qasm, target, shots)
            result = {"results": {target: r}, "all_pass": r["passed"]}
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500
    return jsonify(result)


@app.route("/api/course", methods=["GET"])
def api_course():
    """课程树（游戏即课程）。"""
    return jsonify(content.COURSE)


@app.route("/api/help", methods=["GET"])
def api_help():
    """帮助内容（模板化，来自 content.py 字典）。"""
    basics = [
        {"title": "量子比特 = 旋转的硬币",
         "body": "一个量子比特可以正面(|0⟩)、反面(|1⟩)，或悬在半空的叠加态。测量=让硬币落地。"},
        {"title": "门 = 操作硬币的玩具",
         "body": "X 翻面、H 抛起、S/T/RZ 涂色、RY 定角度、CX 联动、CCX 双联动、SWAP 换座。"},
        {"title": "算法 = 拼出来的机器",
         "body": "门是零件（12个），算法是机器（9台）。评测电路就是从这些机器里抽。"},
        {"title": "三后端 = 三台同一型号的模拟器",
         "body": "spinq/originq/braket 是三家厂商的本地模拟器。同一个电路它们应该给一样的分布。"},
        {"title": "保真度 = 对答案",
         "body": "实测分布与理论分布对比（Hellinger ≥ 0.97 = 正确）。"},
    ]
    steps = [
        {"step": 1, "text": "点'新电路'，从门托盘拖门到电路线"},
        {"step": 2, "text": "点'运行搭建的电路'，三后端模拟"},
        {"step": 3, "text": "看右上直方图：蓝=实测，灰=参考"},
        {"step": 4, "text": "或用右下对话框：'生成 3 比特 GHZ 态'"},
        {"step": 5, "text": "电路库里有 21 个现成电路，点开即学"},
    ]
    # 词典名词索引（前端做名词链接化用：{zh, en}，按中文名+英文键）
    dict_index = []
    for en, v in qc_dict.DICT.items():
        dict_index.append({"en": en, "zh": v["zh"]})
    return jsonify({
        "basics": basics,
        "gates": [{"id": gid, "name": v["name"], "symbol": v["symbol"],
                   "plain": v["plain"], "analogy": v["analogy"]}
                  for gid, v in content.GATES.items()],
        "algorithms": [{"id": aid, "name": v["name"], "plain": v["plain"],
                        "why": v["why"], "result": v["result"]}
                       for aid, v in content.ALGORITHMS.items()],
        "steps": steps,
        "dict_index": dict_index,
    })


@app.route("/api/game-content/<game_id>", methods=["GET"])
def api_game_content(game_id: str):
    """游戏文案（模板化：从 web/game_content/<id>.json 读取）。"""
    path = Path(__file__).resolve().parent / "game_content" / f"{game_id}.json"
    if not path.exists():
        return jsonify({"error": f"游戏文案不存在: {game_id}"}), 404
    data = json.loads(path.read_text(encoding="utf-8"))
    # 附词典词条（dict_refs → 完整词条，供前端渲染/链接）
    refs = set()
    for sec in data.get("sections", []):
        refs.update(sec.get("dict_refs", []))
    dict_terms = []
    for en in refs:
        if en in qc_dict.DICT:
            v = qc_dict.DICT[en]
            dict_terms.append({"en": en, "zh": v["zh"], "def_zh": v["def_zh"], "detail_zh": v["detail_zh"]})
    data["dict_terms"] = dict_terms
    return jsonify(data)


@app.route("/api/dict/<en>", methods=["GET"])
def api_dict(en: str):
    """词典单条词条（词典小窗用）。aliases 为内部防错数据，不对外返回。"""
    v = qc_dict.DICT.get(en)
    if not v:
        return jsonify({"error": f"词典无此词条: {en}"}), 404
    return jsonify({"en": en, **{k: val for k, val in v.items() if k != "aliases"}})


@app.route("/api/schwinger-questions", methods=["GET"])
def api_schwinger_questions():
    """施温格积木进阶测试题集（web/game_content/schwinger_questions.json）。"""
    path = Path(__file__).resolve().parent / "game_content" / "schwinger_questions.json"
    if not path.exists():
        return jsonify({"error": "测试题集不存在"}), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.route("/api/search", methods=["GET"])
def api_search():
    """统一查询：搜词典词条 + 帮助内容。q 参数必填。"""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"terms": [], "help": []})
    # 1. 词典词条（唯一权威源）
    terms = []
    for hit in qc_dict.search(q):
        terms.append({
            "en": hit["key"],
            "zh": hit["zh"],
            "category": hit["category"],
            "def_zh": hit["def_zh"],
            "def_en": hit["def_en"],
            "detail_zh": hit["detail_zh"],
            "detail_en": hit["detail_en"],
            "prereqs": hit["prereqs"],
            "source": hit["source"],
        })
    # 2. 帮助内容（门/算法/基础概念）
    help_hits = []
    ql = q.lower()
    for gid, v in content.GATES.items():
        if ql in gid or ql in v["name"].lower() or ql in v["plain"].lower() or ql in v["analogy"].lower():
            help_hits.append({"kind": "gate", "id": gid, "name": v["name"], "plain": v["plain"]})
    for aid, v in content.ALGORITHMS.items():
        if ql in aid or ql in v["name"].lower() or ql in v["plain"].lower() or ql in v["why"].lower():
            help_hits.append({"kind": "algo", "id": aid, "name": v["name"], "plain": v["plain"]})
    return jsonify({"terms": terms, "help": help_hits})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """读取/保存 Web 用户态 LLM 配置（config.yaml 的 llm_user_* 键）与本源悟空 token（originq_api_token），脱敏：不入 git。"""
    if request.method == "GET":
        return jsonify({"base_url": key_loader.get_secret("llm_user_base_url") or "",
                        "model": key_loader.get_secret("llm_user_model") or "",
                        "has_key": bool(key_loader.get_secret("llm_user_api_key")),
                        "has_originq_key": bool(key_loader.get_secret("originq_api_token"))})
    data = request.get_json(force=True)
    if data.get("api_key"):
        key_loader.set_secret("llm_user_api_key", data["api_key"])
    if data.get("base_url"):
        key_loader.set_secret("llm_user_base_url", data["base_url"])
    if data.get("model"):
        key_loader.set_secret("llm_user_model", data["model"])
    if data.get("originq_api_token"):
        key_loader.set_secret("originq_api_token", data["originq_api_token"])
    return jsonify({"ok": True})


def _load_llm_env() -> bool:
    """把 config.yaml 的 llm_user_* 配置注入环境变量（供 adapter.agent_chat 用）。"""
    import os
    key = key_loader.get_secret("llm_user_api_key")
    if not key:
        return False
    os.environ["LOOMQ_LLM_API_KEY"] = key
    os.environ["LOOMQ_LLM_BASE_URL"] = key_loader.get_secret("llm_user_base_url") or "https://api.deepseek.com"
    os.environ["LOOMQ_LLM_MODEL"] = key_loader.get_secret("llm_user_model") or "deepseek-v4-flash"
    return True


def _dict_context(message: str, limit: int = 4) -> str:
    """词典检索注入：把与消息相关的词条拼成提示词上下文。"""
    hits = qc_dict.search(message)[:limit]
    if not hits:
        return "（无相关词典条目）"
    lines = []
    for h in hits:
        pre = ", ".join(h["prereqs"]) if h["prereqs"] else "无"
        src = h["source"] or "—"
        lines.append(f"- {h['key']}（{h['zh']}）: {h['def_zh']} | 前置: {pre} | 来源: {src}")
    return "\n".join(lines)


def _llm_ask(system_prompt: str, user_msg: str) -> str:
    """直接调 LLM（OpenAI 兼容）。"""
    import urllib.request
    import urllib.error
    base = os.environ.get("LOOMQ_LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("LOOMQ_LLM_MODEL", "deepseek-v4-flash")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
        "temperature": 0,
        "max_tokens": 2000,
    }
    if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
        payload["thinking"] = {"type": "disabled"}
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + os.environ["LOOMQ_LLM_API_KEY"],
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]


_CIRCUIT_INTENT = ["生成", "搭一个", "写一个", "电路", "QASM", "ghz", "bell", "量子电路", "measure"]


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """LLM 对话：词典检索注入 → 电路意图走自验闭环，否则问答。"""
    data = request.get_json(force=True)
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "消息为空"}), 400

    try:
        import os
        if not os.environ.get("LOOMQ_LLM_API_KEY"):
            _load_llm_env()
        if not os.environ.get("LOOMQ_LLM_API_KEY"):
            return jsonify({"error": "未配置 LLM：请在设置面板填写 API Key"}), 400

        ctx = _dict_context(message)
        ml = message.lower()

        # 电路生成意图 → agent_chat 自验闭环（词典注入提示词）
        if any(k in ml for k in _CIRCUIT_INTENT):
            sys.path.insert(0, str(ROOT / "starter_kit"))
            from adapter import agent_chat
            qasm = agent_chat(f"参考词典：{ctx}\n\n{message}")
            return jsonify({"qasm": qasm, "reply": f"已生成电路并通过三后端自验：\n{qasm}",
                            "dict_context": ctx})

        # 问答 → 基于词典回答
        from web.qc_dict import DICT
        sys_prompt = f"""你是 LoomQ 量子计算工作台的智能助手，面向想入门量子计算的普通人。

回答规则：
1. 必须基于用户提供的"词典定义"回答，禁止编造与词典冲突的定义。
2. 词典里有的术语，用"中文(英文)"格式引用，如"纠缠（Entanglement）"。
3. 用大白话解释，像在给一个聪明但没学过量子的人讲，避免堆术语。
4. 若问题与量子无关，礼貌说明并引导到量子话题。
5. 回答简洁，100-200 字内；若需要例子可用 1 个比喻。

【词典定义（本次相关）】
{ctx}

【词典中可引用的完整定义（若需要更细）】
{json.dumps([{k: {"zh": DICT[k]["zh"], "def_zh": DICT[k]["def_zh"], "detail_zh": DICT[k]["detail_zh"]}} for k in DICT if any(w in message for w in (k, DICT[k]["zh"]))], ensure_ascii=False)[:1500]}"""
        reply = _llm_ask(sys_prompt, message)
        return jsonify({"reply": reply, "dict_context": ctx})
    except Exception as exc:
        return jsonify({"error": f"LLM 调用失败: {str(exc)[:200]}"}), 500


# ---------------------------------------------------------------------------
# 页面
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # 注意：不能用 debug=True（reloader 子进程不继承 DYLD_LIBRARY_PATH，
    # 导致 spinqit 二进制加载失败）。产品/开发都用 debug=False。
    app.run(host="127.0.0.1", port=5011, debug=False)
