/* components/qasm.js — 统一 QASM 2.0 模块（QasmModule）
 *
 * 替代三套解析器：
 *   - loomq_lib/loomq_lib/semantics.py (Circuit.parse) — 后端 Python 解析
 *   - web/static/js/circuit.js (QCircuit.parse)      — 前端电路图解析
 *   - web/static/js/builder.js (toQasm)              — 前端门→QASM 生成
 *
 * 统一 API：
 *   parse(qasm)        → { n: qubit数, ops: [{name, theta, qargs, col?}], gates: [...] }
 *   generate(ops)       → QASM 2.0 文本
 *   toOpSet(ops)        → "h[0];cx[0,1]" 字符串（门多集相等比较，忽略顺序/重复）
 *   equalOpSets(a, b)   → boolean
 *   validate(qasm)      → { ok, error }（zod 风格校验）
 *
 * 算法匹配（如布纳尔袜子判定"拼出的电路是否等于目标算法"）：
 *   const user = toOpSet(QasmModule.parse(userQasm).ops);
 *   const target = toOpSet(QasmModule.parse(targetQasm).ops);
 *   QasmModule.equalOpSets(user, target);  // 忽略顺序/门类型的多集比较
 */

const QasmModule = (() => {
  /* ---------- 解析 QASM 2.0 → 操作列表 ---------- */
  function parse(qasm) {
    const text = (qasm || "").replace(/"/g, "");
    const stmts = [];
    let n = 0, cBits = 0;
    const lines = text.split("\n");
    const code = lines.map(l => l.replace(/\/\/.*$/, "")).join("\n");
    for (const raw of code.replace(/;/g, ";\n").split("\n")) {
      const line = raw.trim();
      if (!line) continue;
      let m = line.match(/^OPENQASM\b/i);
      if (m) continue;
      m = line.match(/^include\b/i);
      if (m) continue;
      m = line.match(/^qreg\s+\w+\s*\[\s*(\d+)\s*\]/);
      if (m) { n = parseInt(m[1]); continue; }
      m = line.match(/^creg\s+\w+\s*\[\s*(\d+)\s*\]/);
      if (m) { cBits = parseInt(m[1]); continue; }
      if (/^measure\b/.test(line)) continue;
      if (/^barrier\b/.test(line)) continue;
      m = line.match(/^(\w+)\s*(?:\(([^)]*)\))?\s*(.*)$/);
      if (!m) continue;
      const name = m[1].toLowerCase();
      if (["openqasm","include","qreg","creg","measure","barrier"].includes(name)) continue;
      const params = (m[2] || "").trim();
      const rest = m[3];
      const qargs = [...rest.matchAll(/\[(\d+)\]/g)].map(x => parseInt(x[1]));
      if (qargs.length === 0 && ["h","x","s","sdg","t","tdg","rz","ry"].includes(name)) continue; // 解析错误，跳过
      stmts.push({
        name,
        theta: params || null,
        qargs,
      });
    }
    return { n, cBits, ops: stmts };
  }

  /* ---------- 操作列表 → QASM 2.0 文本 ---------- */
  function generate(ops, opts = {}) {
    const n = opts.n || inferQubits(ops);
    const lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', `qreg q[${n}];`, `creg c[${n}];`];
    for (const op of ops) {
      const qs = op.qargs.map(q => `q[${q}]`).join(", ");
      if (op.theta) lines.push(`${op.name}(${op.theta}) ${qs};`);
      else lines.push(`${op.name} ${qs};`);
    }
    lines.push("measure q -> c;");
    return lines.join("\n") + "\n";
  }

  /* ---------- 推断 qubit 数（生成时用） ---------- */
  function inferQubits(ops) {
    let n = 1;
    for (const op of ops) for (const q of op.qargs) if (q + 1 > n) n = q + 1;
    return n;
  }

  /* ---------- 操作列表 → 多集签名字符串（算法匹配用） ---------- */
  function toOpSet(ops) {
    // 多集：把每个门序列化为"name(t1,t2..):q[0],q[1]"，按门类型分组再排序
    const byKind = {};
    for (const op of ops) {
      const theta = op.theta ? `(${op.theta})` : "";
      const qset = op.qargs.slice().sort((a, b) => a - b).map(q => `q${q}`).join("|");
      const key = `${op.name}${theta}@${qset}`;
      byKind[key] = (byKind[key] || 0) + 1;
    }
    // 输出：门类型1(计数)\n门类型2(计数)\n...
    return Object.entries(byKind).sort(([a], [b]) => a.localeCompare(b)).map(([k, n]) => `${k}*${n}`).join("|");
  }

  function equalOpSets(a, b) { return a === b; }

  /* ---------- 校验（用于表单提交前/对话框生成后） ---------- */
  function validate(qasm) {
    if (!qasm || !qasm.includes("OPENQASM")) return { ok: false, error: "缺少 OPENQASM 头" };
    if (!qasm.includes("qreg")) return { ok: false, error: "缺少 qreg 声明" };
    if (!qasm.includes("measure")) return { ok: false, error: "缺少 measure 测量" };
    try {
      const r = parse(qasm);
      if (r.n === 0) return { ok: false, error: "未声明任何 qubit" };
      if (r.ops.length === 0) return { ok: false, error: "电路为空" };
      return { ok: true, parsed: r };
    } catch (e) {
      return { ok: false, error: "解析失败: " + (e.message || e).slice(0, 80) };
    }
  }

  return { parse, generate, toOpSet, equalOpSets, validate };
})();