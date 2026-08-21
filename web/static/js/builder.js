/* builder.js — 拖拽搭建量子电路
 *
 * 交互（对标 IBM Quantum Composer）：
 *   - 门托盘：12 个门图标，可拖拽
 *   - 电路画布：每条 qubit 一根线，可拖放门、可删门、可加/减 qubit
 *   - 实时生成 QASM 2.0，供 run API 执行
 */

const Builder = (() => {
  const GATES = ["h", "x", "s", "sdg", "t", "tdg", "rz", "ry", "cx", "cu1", "swap", "ccx"];
  const PARAM_GATES = { rz: "pi/4", ry: "pi/4", cu1: "pi/4" };

  const state = {
    n: 2,                // qubit 数
    ops: [],             // [{name, theta, qargs, col}]
    dragGate: null,      // 正在拖的门
    dragParam: null,
    syncing: false,      // QASM 文本回写中（防 textarea input 循环触发）
    qasmTimer: null,     // QASM 输入防抖 timer
  };

  /* ---------- 门托盘 ---------- */
  function renderTray() {
    const tray = document.getElementById("gate-tray");
    tray.innerHTML = GATES.map(g => `
      <div class="gate-tile" draggable="true" data-gate="${g}" title="${GATE_SVG.name(g)}">
        <svg viewBox="0 0 40 40" width="36" height="36">${gateIcon(g, {})}</svg>
        <span>${g.toUpperCase()}</span>
      </div>`).join("");
    tray.querySelectorAll(".gate-tile").forEach(el => {
      el.addEventListener("dragstart", e => {
        state.dragGate = el.dataset.gate;
        state.dragParam = PARAM_GATES[el.dataset.gate] || null;
        e.dataTransfer.effectAllowed = "copy";
      });
    });
  }

  /* ---------- 电路画布 ---------- */
  function renderCanvas() {
    const canvas = document.getElementById("builder-canvas");
    // 计算每列最大 qubit 跨度
    const cols = colCount();
    // 紧凑布局 v2：列宽 36 / 行高 40 / 门中心偏移 18（门图标内部 scale 0.8，同宽度容纳更多列）
    const COL_W = 36, ROW_H = 40, X0 = 40, Y0 = 22;
    const width = X0 + cols * COL_W + 18;
    const height = Y0 + (state.n - 1) * ROW_H + 16;
    const gx = c => X0 + c * COL_W + 18;  // 门中心 x
    const qy = q => Y0 + q * ROW_H;       // qubit 线 y

    let html = `<svg viewBox="0 0 ${width} ${height}" width="100%" style="background:#fff;border:1px dashed #cbd5e1;border-radius:8px;min-height:120px">`;
    // qubit 线 + 拖放目标
    for (let q = 0; q < state.n; q++) {
      const y = qy(q);
      html += `<line x1="${X0 - 8}" y1="${y}" x2="${width - 10}" y2="${y}" stroke="#94a3b8" stroke-width="1.2"/>`;
      html += `<text x="${X0 - 6}" y="${y + 4}" text-anchor="end" font-size="11" fill="#64748b">q${q}</text>`;
      // 每列一个放置热区（透明矩形，接收 drop）
      for (let c = 0; c < cols; c++) {
        const x = X0 + c * COL_W;
        html += `<rect x="${x}" y="${y - 16}" width="${COL_W - 4}" height="${ROW_H - 8}" fill="transparent" data-drop="${c},${q}" style="cursor:pointer"/>`;
      }
    }
    // 已放置的门
    for (const op of state.ops) {
      const x = X0 + op.col * COL_W;
      if (op.qargs.length > 1) {
        // 多比特门：竖直画法（控制点 ● / 目标 ⊕，竖线连接）
        const ys = op.qargs.map(q => qy(q));
        const yTop = Math.min(...ys), yBot = Math.max(...ys);
        const color = op.name === "swap" ? "#16a34a" : "#dc2626";
        html += `<line x1="${gx(op.col)}" y1="${yTop}" x2="${gx(op.col)}" y2="${yBot}" stroke="#94a3b8" stroke-width="1.5"/>`;
        if (op.name === "swap") {
          for (const y of ys) {
            html += `<g transform="translate(${gx(op.col) - 10}, ${y - 10})" stroke="${color}" stroke-width="2.5" fill="none">
              <line x1="2" y1="2" x2="18" y2="18"/><line x1="18" y1="2" x2="2" y2="18"/></g>`;
          }
        } else if (op.name === "ccx") {
          for (const y of ys.slice(0, 2)) {
            html += `<circle cx="${gx(op.col)}" cy="${y}" r="3" fill="${color}"/>`;
          }
          html += targetSymbol(gx(op.col), ys[2], color);
        } else {
          html += `<circle cx="${gx(op.col)}" cy="${yTop}" r="3" fill="${color}"/>`;
          if (op.name === "cu1") {
            html += `<rect x="${gx(op.col) - 11}" y="${yBot - 11}" width="22" height="22" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
              <text x="${gx(op.col)}" y="${yBot + 1}" text-anchor="middle" font-size="9" fill="#2563eb">U1</text>
              <text x="${gx(op.col)}" y="${yBot + 10}" text-anchor="middle" font-size="7" fill="#6b7280">${op.theta || "θ"}</text>`;
          } else {
            html += targetSymbol(gx(op.col), yBot, color);
          }
        }
        html += `<g transform="translate(${gx(op.col) - 14}, ${yTop - 16})" class="placed-gate" data-id="${op.id}">
          <rect x="0" y="0" width="28" height="${(yBot - yTop) + 32}" fill="transparent"/>
        </g>`;
      } else {
        // 单比特门（图标 scale 0.8：40px → 32px）
        const y = qy(op.qargs[0]);
        html += `<g transform="translate(${x + 2}, ${y - 16})" class="placed-gate" data-id="${op.id}">
          <g transform="scale(0.8)">${gateIcon(op.name, op)}</g>
          <rect x="-4" y="-4" width="36" height="38" fill="transparent"/>
        </g>`;
      }
    }
    html += "</svg>";
    canvas.innerHTML = html;

    // 绑定放置
    canvas.querySelectorAll("[data-drop]").forEach(rect => {
      rect.addEventListener("dragover", e => e.preventDefault());
      rect.addEventListener("drop", e => {
        e.preventDefault();
        if (!state.dragGate) return;
        const [col, q] = rect.dataset.drop.split(",").map(Number);
        placeGate(state.dragGate, col, q, state.dragParam);
      });
      // 点击也可放置（无障碍）
      rect.addEventListener("click", () => {
        if (!state.dragGate) return;
        const [col, q] = rect.dataset.drop.split(",").map(Number);
        placeGate(state.dragGate, col, q, state.dragParam);
      });
    });
    // 绑定删除（点击已放门）
    canvas.querySelectorAll(".placed-gate").forEach(g => {
      g.addEventListener("click", e => {
        e.stopPropagation();
        const id = Number(g.dataset.id);
        state.ops = state.ops.filter(o => o.id !== id);
        renderCanvas();
        syncQasm();
      });
    });
  }

  function colCount() {
    return Math.max(3, ...state.ops.map(o => o.col + 1));
  }

  let nextId = 1;
  function placeGate(gate, col, q, theta) {
    // 冲突检测：该列该 qubit 已被占用则放到下一列
    while (state.ops.some(o => o.col === col && o.qargs.includes(q))) col++;
    const op = {
      id: nextId++, name: gate, theta: theta,
      qargs: qargsFor(gate, q),
      col: col,
    };
    // 多比特门的控制位在目标位上方
    state.ops.push(op);
    state.dragGate = null;
    renderCanvas();
    syncQasm();
  }

  function qargsFor(gate, q) {
    const n = state.n;
    if (gate === "cx" || gate === "cu1") return [q, (q + 1) % n];
    if (gate === "swap") return [q, (q + 1) % n];
    if (gate === "ccx") return [q, (q + 1) % n, (q + 2) % n];
    return [q];
  }

  /* ---------- 生成 QASM（委托 QasmModule） ---------- */
  function toQasm() {
    const sorted = [...state.ops].sort((a, b) => a.col - b.col);
    return QasmModule.generate(sorted, { n: state.n });
  }

  /* 实时刷新 QASM 显示（写回时置 syncing，避免触发 textarea input → 死循环） */
  function syncQasm() {
    const el = document.getElementById("builder-qasm");
    if (!el || state.syncing) return;
    state.syncing = true;
    el.value = toQasm();
    state.syncing = false;
  }

  /* ---------- 对外接口 ---------- */
  function init() {
    renderTray();
    renderCanvas();
    syncQasm();
    document.getElementById("builder-add-qubit").addEventListener("click", () => {
      if (state.n < 8) { state.n++; renderCanvas(); syncQasm(); }
    });
    document.getElementById("builder-clear").addEventListener("click", () => {
      state.ops = []; renderCanvas(); syncQasm();
    });
    document.getElementById("builder-run").addEventListener("click", () => {
      const qasm = toQasm();
      if (typeof App !== "undefined" && App.runBuilder) App.runBuilder(qasm);
    });
    document.getElementById("builder-copy").addEventListener("click", () => {
      navigator.clipboard.writeText(toQasm()).then(() => {
        const b = document.getElementById("builder-copy");
        const old = b.textContent; b.textContent = "✓ 已复制";
        setTimeout(() => b.textContent = old, 1200);
      });
    });
    // QASM 文本编辑 → 电路图实时同步（防抖；解析失败/无门时静默保持当前画布，不打断输入）
    const qasmEl = document.getElementById("builder-qasm");
    qasmEl.addEventListener("input", () => {
      if (state.syncing) return;
      clearTimeout(state.qasmTimer);
      state.qasmTimer = setTimeout(() => loadQasm(qasmEl.value), 150);
    });
  }

  /* 目标 ⊕ 符号 */
  function targetSymbol(cx, cy, color) {
    return `<circle cx="${cx}" cy="${cy}" r="5" fill="none" stroke="${color}" stroke-width="2"/>
      <line x1="${cx - 3.5}" y1="${cy}" x2="${cx + 3.5}" y2="${cy}" stroke="${color}" stroke-width="2"/>
      <line x1="${cx}" y1="${cy - 3.5}" x2="${cx}" y2="${cy + 3.5}" stroke="${color}" stroke-width="2"/>`;
  }

  /* ---------- QASM → 电路图（反向同步） ---------- */
  /* 把门操作按列排布（同列不能重叠 qubit，与 circuit.js layout 算法一致） */
  function layoutOps(ops) {
    const used = [];
    const out = [];
    for (const op of ops) {
      let col = 0;
      while (true) {
        if (!used[col]) used[col] = new Set();
        if (!op.qargs.some(q => used[col].has(q))) break;
        col++;
      }
      op.qargs.forEach(q => used[col].add(q));
      out.push({ id: nextId++, name: op.name, theta: op.theta, qargs: op.qargs, col });
    }
    return out;
  }

  /* 从 QASM 文本加载电路进画布。
   * 解析失败 / 无门 → 静默（保持当前画布，不打断用户输入）。
   * 成功 → 重排列布局并重绘，返回 {ok, n, unsupported}。 */
  function loadQasm(qasm, syncText = false) {
    if (!(qasm || "").trim()) { state.ops = []; renderCanvas(); if (syncText) syncQasm(); return { ok: true, cleared: true }; }
    let parsed;
    try { parsed = QasmModule.parse(qasm); } catch (e) { return { ok: false }; }
    const ops = (parsed.ops || []).filter(o => o.qargs.length > 0); // 过滤残缺行
    if (ops.length === 0) return { ok: false, reason: "empty" };
    let n = parsed.n || 0;
    for (const op of ops) for (const q of op.qargs) n = Math.max(n, q + 1);
    state.n = Math.max(1, n);
    state.ops = layoutOps(ops);
    renderCanvas();
    if (syncText) syncQasm(); // 外部喂入（如 LLM 自动搭建）时同步 QASM 文本区
    const unsupported = [...new Set(ops.map(o => o.name).filter(name => !GATES.includes(name)))];
    if (unsupported.length && typeof log === "function") {
      log("⚠ 以下门不在拖拽托盘中，仅能通过 QASM 编辑（可删除）：" + unsupported.join(", "));
    }
    if (state.n > 8 && typeof log === "function") {
      log("ℹ 已加载 " + state.n + " 量子比特（超出拖拽上限 8，仅可查看/删除已有门）");
    }
    return { ok: true, n: state.n, unsupported };
  }

  return { init, toQasm, getOps: () => state.ops, syncQasm, loadQasm };

  /* 门图标（内部，避免与 GATE_SVG 依赖冲突） */
  function gateIcon(name, op) {
    if (name === "cx") return GATE_SVG.cx();
    if (name === "ccx") return GATE_SVG.ccx();
    if (name === "swap") return GATE_SVG.swap();
    if (name === "cu1") return GATE_SVG.cu1(op.theta || "θ");
    if (name === "rz") return GATE_SVG.rz(op.theta || "θ");
    if (name === "ry") return GATE_SVG.ry(op.theta || "θ");
    if (GATE_SVG[name]) return GATE_SVG[name]();
    return GATE_SVG._box(name.toUpperCase());
  }
})();
