/* circuit.js — 电路图渲染器：QASM 2.0 → SVG 电路图
 *
 * 流程：解析 QASM → 门操作列表 → 按时间列排布 → 生成 SVG
 * 布局：
 *   - 每条 qubit 一条水平线（wire），间距 WIRE_GAP
 *   - 门按执行顺序从左到右排布（列）
 *   - 双比特门（cx/cu1/swap）竖线连接控制/目标
 *   - 三比特门（ccx）三条线连接
 */

const QCircuit = (() => {
  const WIRE_GAP = 46;      // 相邻 qubit 间距
  const COL_W = 44;         // 每列宽度
  const MARGIN = { left: 50, top: 24, bottom: 20 };
  const QUBIT_LABEL_W = 40; // qubit 标签区宽度

  /* 解析 QASM 2.0 为门操作列表（委托给 QasmModule） */
  function parse(qasm) {
    const r = QasmModule.parse(qasm);
    return { n: r.n, ops: r.ops };
  }

  /* 把门操作按列排布（同列不能重叠 qubit）*/
  function layout(n, ops) {
    const used = [];   // 每列已占用的 qubit
    const columns = []; // 每列的门列表
    for (const op of ops) {
      // 找第一个不冲突的列
      let col = 0;
      while (true) {
        if (!used[col]) used[col] = new Set();
        const conflict = op.qargs.some(q => used[col].has(q));
        if (!conflict) break;
        col++;
      }
      if (!columns[col]) columns[col] = [];
      columns[col].push(op);
      op.qargs.forEach(q => used[col].add(q));
    }
    return columns.filter(Boolean);
  }

  /* 门图标（复用 gates.js）*/
  function gateIcon(op, qubits) {
    const { name } = op;
    if (name === "cx") return GATE_SVG.cx();
    if (name === "ccx") return GATE_SVG.ccx();
    if (name === "swap") return GATE_SVG.swap();
    if (name === "cu1") return GATE_SVG.cu1(op.theta || "θ");
    if (name === "rz") return GATE_SVG.rz(op.theta || "θ");
    if (name === "ry") return GATE_SVG.ry(op.theta || "θ");
    if (GATE_SVG[name]) return GATE_SVG[name]();
    return GATE_SVG._box(name.toUpperCase());
  }

  /* 渲染 SVG 电路图 */
  function render(qasm, opts = {}) {
    const { n, ops } = parse(qasm);
    if (n === 0) return `<text x="20" y="30" font-size="14" fill="#6b7280">无法解析电路</text>`;
    const columns = layout(n, ops);
    const width = MARGIN.left + columns.length * COL_W + 20;
    const height = MARGIN.top + n * WIRE_GAP + MARGIN.bottom;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;

    // 背景
    svg += `<rect width="${width}" height="${height}" fill="#ffffff"/>`;

    // qubit 线 + 标签
    for (let q = 0; q < n; q++) {
      const y = MARGIN.top + q * WIRE_GAP;
      svg += `<line x1="${MARGIN.left - 10}" y1="${y}" x2="${width - 10}" y2="${y}" stroke="#94a3b8" stroke-width="1.2"/>`;
      svg += `<text x="${MARGIN.left - 16}" y="${y + 4}" text-anchor="end" font-size="11" font-family="monospace" fill="#64748b">q[${q}]</text>`;
    }

    // 门
    for (let c = 0; c < columns.length; c++) {
      const cx = MARGIN.left + c * COL_W;
      for (const op of columns[c]) {
        const { qargs, name } = op;
        if (qargs.length === 1) {
          const y = MARGIN.top + qargs[0] * WIRE_GAP;
          svg += `<g transform="translate(${cx - 20}, ${y - 20})">${gateIcon(op, n)}</g>`;
        } else {
          // 多比特门：竖直画法 —— 控制位 ● / 目标位 ⊕ 或方框，竖线连接两行
          svg += drawMultiQubitGate(cx, qargs, name, op.theta);
        }
      }
    }
    svg += "</svg>";
    return svg;
  }

  /* 竖直画多比特门：控制点在上行，目标 ⊕/方框在下行，竖线连接 */
  function drawMultiQubitGate(cx, qargs, name, theta) {
    const ys = qargs.map(q => MARGIN.top + q * WIRE_GAP);
    const yTop = Math.min(...ys);
    const yBot = Math.max(...ys);
    const color = name === "swap" ? "#16a34a" : "#dc2626";
    let s = `<line x1="${cx}" y1="${yTop}" x2="${cx}" y2="${yBot}" stroke="#94a3b8" stroke-width="1.5"/>`;

    if (name === "swap") {
      // 两端 ×
      for (const y of ys) {
        s += `<g transform="translate(${cx - 12}, ${y - 12})" stroke="${color}" stroke-width="2.5" fill="none">
          <line x1="3" y1="3" x2="21" y2="21"/><line x1="21" y1="3" x2="3" y2="21"/></g>`;
      }
      return s;
    }
    if (name === "ccx") {
      // 两个控制点 ●（上行与中间行），目标 ⊕（下行）
      const ctrlYs = ys.slice(0, 2);
      const tgtY = ys[2];
      for (const y of ctrlYs) {
        s += `<circle cx="${cx}" cy="${y}" r="4" fill="${color}"/>`;
      }
      s += targetCircle(cx, tgtY, color);
      return s;
    }
    // cx / cu1：控制点（最上行），目标（最下行）
    const ctrlY = ys[0];
    const tgtY = ys[ys.length - 1];
    s += `<circle cx="${cx}" cy="${ctrlY}" r="4" fill="${color}"/>`;
    if (name === "cu1") {
      // 目标：方框 U1(θ)
      s += `<rect x="${cx - 16}" y="${tgtY - 14}" width="32" height="28" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
        <text x="${cx}" y="${tgtY + 2}" text-anchor="middle" font-size="10" font-family="monospace" fill="#2563eb">U1</text>
        <text x="${cx}" y="${tgtY + 13}" text-anchor="middle" font-size="8" fill="#6b7280">${theta || "θ"}</text>`;
    } else {
      s += targetCircle(cx, tgtY, color);
    }
    return s;
  }

  /* 目标 ⊕ 符号 */
  function targetCircle(cx, cy, color) {
    return `<circle cx="${cx}" cy="${cy}" r="6" fill="none" stroke="${color}" stroke-width="2"/>
      <line x1="${cx - 4}" y1="${cy}" x2="${cx + 4}" y2="${cy}" stroke="${color}" stroke-width="2"/>
      <line x1="${cx}" y1="${cy - 4}" x2="${cx}" y2="${cy + 4}" stroke="${color}" stroke-width="2"/>`;
  }

  return { parse, render };
})();
