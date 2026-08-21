/* socks.js — 伯特曼袜子（纠缠配对）游戏
 *
 * 背景：J.S. Bell 1978《Bertlmann's Socks and the Nature of Reality》。
 *   Bertlmann 常穿一红一绿袜子 → 看到一只就知道另一只颜色 → 比喻量子纠缠。
 *
 * 颜色规则（统一语义）：0 = 红袜，1 = 绿袜（每只袜子 = 一个比特值）
 *   - 同面模式（|00⟩↔|11⟩）：每对同色 —— 红红（00）或 绿绿（11）
 *     → 伙伴规则：同色 + 同"第 N 双"徽标
 *   - 异面模式（|01⟩↔|10⟩）：每对一红一绿 —— 经典伯特曼袜子
 *     → 伙伴规则：相反色 + 同"第 N 双"徽标
 *
 * 关键：不同对的袜子即使状态相同（同为 |1⟩）也不是纠缠伙伴——
 * 必须"第 N 双"徽标相同（第 1 双的 |1⟩ 与第 8 双的 |1⟩ 不能互换）。
 *
 * 获胜：配齐全部 8 对。
 */

const Socks = (() => {
  const state = {
    mode: "same",
    count: 4,         // 双数：4（默认快速）/ 8（完整）
    pairs: [],        // [{id, bits:[bitL, bitR]}]
    board: [],        // [{pairId, side, bit, color, flipped}]
    selected: null,
    matched: 0,
    total: 4,
    firstFlip: true,
  };

  // 计时器：首次翻牌启动，配齐停止，重开/切模式/切双数重置
  let _timerId = null;
  let _startTs = null;

  function fmtTime(ms) {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    return `${m}:${String(s % 60).padStart(2, "0")}`;
  }

  function renderTimer() {
    const el = document.getElementById("socks-timer");
    if (!el) return;
    el.textContent = _startTs ? "⏱ " + fmtTime(Date.now() - _startTs) : "⏱ 00:00";
  }

  function startTimer() {
    if (_timerId !== null) return;   // 已启动则不动
    _startTs = Date.now();
    _timerId = setInterval(renderTimer, 250);
    renderTimer();
  }

  function stopTimer() {
    if (_timerId !== null) { clearInterval(_timerId); _timerId = null; }
    const ms = _startTs ? Date.now() - _startTs : 0;
    renderTimer();
    return ms;
  }

  function resetTimer() {
    if (_timerId !== null) { clearInterval(_timerId); _timerId = null; }
    _startTs = null;
    const el = document.getElementById("socks-timer");
    if (el) el.textContent = "⏱ 00:00";
  }

  // 每对的独特"第 N 双"徽标（1-8）
  const PAIR_BADGE = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧"];

  // 0 = 红，1 = 绿
  const BIT_COLOR = { 0: "红", 1: "绿" };

  function initPairs() {
    const pairs = [];
    const isSame = state.mode === "same";
    const n = state.count;
    // same: 交替红红(00)/绿绿(11)；diff: 全部一红一绿(01/10)
    const bitsList = [];
    for (let i = 0; i < n; i++) {
      if (isSame) {
        bitsList.push(i % 2 === 0 ? [0, 0] : [1, 1]);
      } else {
        bitsList.push([0, 1]);
      }
    }
    for (let i = 0; i < n; i++) {
      pairs.push({ id: i, bits: bitsList[i] });
    }
    state.pairs = pairs;
    state.board = [];
    for (const p of pairs) {
      state.board.push({ pairId: p.id, side: "L", bit: p.bits[0], color: BIT_COLOR[p.bits[0]], flipped: false });
      state.board.push({ pairId: p.id, side: "R", bit: p.bits[1], color: BIT_COLOR[p.bits[1]], flipped: false });
    }
    shuffle(state.board);
    state.selected = null;
    state.matched = 0;
    state.firstFlip = true;
    resetTimer();
    const win = document.getElementById("socks-win");
    if (win) win.style.display = "none";
  }

  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }

  // 袜子 SVG 图标（拟真造型：袜筒+弯脚+袜口条纹），fill 用 CSS 变量 --sock-color
  //   红袜=var(--sock-red)、绿袜=var(--sock-green)，随主题变；袜口条纹 --sock-cuff
  function sockSvg(color) {
    const cls = color === "绿" ? "sock-svg green" : "sock-svg red";
    return `<svg class="${cls}" width="40" height="40" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 2h12v7.5c0 2.6-1.1 4.7-2.9 6.2L12 18.6l-3.1-2.9C7.1 14.2 6 12.1 6 9.5V2z" fill="var(--sock-color)"/>
      <path d="M6 2h12v2.8H6z" fill="var(--sock-cuff)"/>
      <path d="M6 7h12" stroke="var(--sock-cuff)" stroke-opacity=".55" stroke-width="1.1"/>
    </svg>`;
  }

  function render() {
    const board = document.getElementById("socks-board");
    let html = "";
    for (let i = 0; i < state.board.length; i++) {
      const card = state.board[i];
      const isSel = state.selected && state.selected.index === i;
      if (card.flipped) {
        const c = card.color === "绿" ? "green" : "red";
        html += `<div class="sock-card flipped ${c} ${isSel ? "selected" : ""}" data-i="${i}">
          <div class="sock-badge">第${PAIR_BADGE[card.pairId]}双</div>
          ${sockSvg(card.color)}
          <div class="sock-label">|${card.bit}⟩</div>
          <div class="sock-color">${card.color}袜</div>
        </div>`;
      } else {
        html += `<div class="sock-card" data-i="${i}">
          <div class="sock-back">❓</div>
        </div>`;
      }
    }
    board.innerHTML = html;
    board.querySelectorAll(".sock-card").forEach(el => {
      el.addEventListener("click", () => flip(el.dataset.i));
    });
    document.getElementById("socks-score").textContent = `配对：${state.matched}/${state.total}`;
  }

  function checkWin() {
    if (state.matched === state.total) {
      const elapsedMs = stopTimer();
      const t = fmtTime(elapsedMs);
      const n = state.total;
      const win = document.getElementById("socks-win");
      win.style.display = "block";
      win.innerHTML = `<div class="sock-win-banner">🎉 你配齐了全部 ${n} 双伯特曼的袜子！用时 ${t}</div>
        <p class="muted">这 ${n} 对袜子就像 ${n} 对纠缠粒子——每对里看一只就知道另一只。
        你刚刚体验的就是 <b>量子纠缠</b>（<a class="dict-link" data-en="entanglement">Entanglement</a>）。</p>`;
      win.querySelectorAll(".dict-link").forEach(a => {
        a.addEventListener("click", (e) => {
          e.preventDefault();
          if (window.showDictModal) window.showDictModal(a.dataset.en);
        });
      });
    }
  }

  function flip(i) {
    const card = state.board[i];
    if (card.flipped) return;
    if (state.selected) {
      // 第二张：判定
      card.flipped = true;
      const sel = state.board[state.selected.index];
      const msg = document.getElementById("socks-msg");
      const isMatch = (sel.pairId === card.pairId);
      if (isMatch) {
        state.matched++;
        const p = state.pairs[sel.pairId];
        const pairStr = state.mode === "same"
          ? (p.bits[0] === 0 ? "|00⟩" : "|11⟩")
          : (p.bits[0] === 0 ? "|01⟩" : "|10⟩");
        msg.innerHTML = `<span class="ok">✓ 配对成功！第${PAIR_BADGE[sel.pairId]}双：${sel.color}袜(|${sel.bit}⟩) ↔ ${card.color}袜(|${card.bit}⟩)（纠缠对 ${pairStr}）</span>`;
        state.selected = null;
        render();
        checkWin();
      } else {
        const p = state.pairs[sel.pairId];
        const wantBit = state.mode === "same" ? sel.bit : (1 - sel.bit);
        msg.innerHTML = `<span class="err">✗ 不是一对！第${PAIR_BADGE[sel.pairId]}双的伙伴是同徽标第${PAIR_BADGE[sel.pairId]}双的<b>${BIT_COLOR[wantBit]}袜</b>(|${wantBit}⟩)——不同对的状态不能互换。</span>`;
        // 立即翻回（无延迟：消除状态竞争 + 加快节奏），错误消息已指明正确伙伴
        sel.flipped = false;
        card.flipped = false;
        state.selected = null;
        render();
      }
    } else {
      // 第一张：翻开（同时启动计时）
      card.flipped = true;
      state.selected = { index: i };
      startTimer();
      const msg = document.getElementById("socks-msg");
      const p = state.pairs[card.pairId];
      const isSame = state.mode === "same";
      const wantBit = isSame ? card.bit : (1 - card.bit);
      const rule = isSame
        ? `第${PAIR_BADGE[card.pairId]}双（${card.color}袜 |${card.bit}⟩）是<b>同面纠缠</b>（${p.bits[0] === 0 ? "|00⟩" : "|11⟩"}）：伙伴<b>同色同徽标</b>，找"第${PAIR_BADGE[card.pairId]}双"的另一只<b>${BIT_COLOR[wantBit]}袜</b>(|${wantBit}⟩)。`
        : `第${PAIR_BADGE[card.pairId]}双（${card.color}袜 |${card.bit}⟩）是<b>异面纠缠</b>（|01⟩↔|10⟩，经典伯特曼袜子）：伙伴<b>相反色同徽标</b>，找"第${PAIR_BADGE[card.pairId]}双"的另一只<b>${BIT_COLOR[wantBit]}袜</b>(|${wantBit}⟩)。`;
      msg.innerHTML = `<span class="hint">🧦 ${rule}</span>`;
      if (state.firstFlip) {
        msg.innerHTML += `<br><span class="hint muted">提示：颜色规则 0=红、1=绿。关键是"第 N 双"徽标相同才算一对——不同对的同类袜子不能互换！</span>`;
        state.firstFlip = false;
      }
      render();
    }
  }

  function init() {
    // 双数下拉（默认4）
    const countSel = document.getElementById("socks-count");
    if (countSel) {
      countSel.value = String(state.count);
      countSel.addEventListener("change", e => {
        state.count = Number(e.target.value);
        state.total = state.count;
        initPairs(); render();
        document.getElementById("socks-msg").innerHTML = "";
      });
    }
    // 面板可能被重建（openGame 每次创建新 DOM）→ 用事件委托避免重复绑定/失效
    initPairs();
    render();
    const boardEl = document.getElementById("socks-board");
    if (!boardEl._socksBound) {
      // 模式/双数/重启 用 document 级委托（面板重建后依然有效）
      document.addEventListener("change", e => {
        if (e.target.id === "socks-mode") {
          state.mode = e.target.value;
          state.total = state.count;
          initPairs(); render();
          const msg = document.getElementById("socks-msg");
          if (msg) msg.innerHTML = "";
        } else if (e.target.id === "socks-count") {
          state.count = Number(e.target.value);
          state.total = state.count;
          initPairs(); render();
          const msg = document.getElementById("socks-msg");
          if (msg) msg.innerHTML = "";
        }
      });
      document.addEventListener("click", e => {
        if (e.target.id === "socks-restart") {
          initPairs(); render();
          const msg = document.getElementById("socks-msg");
          if (msg) msg.innerHTML = "";
        }
      });
      boardEl._socksBound = true;
    }
    render();
  }

  return { init };
})();
