/* hgate.js — 第1课：叠加态 H 门游戏（Terry Rudolph 黑球白球方案）
 *
 * 玩法：把球（黑=0 白=1）丢进 H 门盒子，看出来的球。
 * 关卡：
 *   关1 探 H：黑球进 H 盒 → 5000 次统计 → 约 50/50
 *   关2 不挑色：白球进 H 盒 → 也是 50/50（H 不区分颜色）
 *   关3 H²=I：球连续过两次 H 盒 → 100% 回原色
 *
 * 规范术语：界面上标"H 门"，借喻用"神奇的盒子"。
 */

const HGate = (() => {
  const state = {
    level: 1,          // 当前关
    ballColor: "black",// 当前球色
    path: [],          // 路径：经过的盒子序列
    result: null,      // 最终结果
  };

  const LEVELS = [
    { n: 1, title: "关 1：探 H 门", desc: "把黑球（|0⟩）丢进 H 门盒子，观察出来的球（测 5000 次）", init: { ball: "black", path: ["h"] } },
    { n: 2, title: "关 2：H 门不挑色", desc: "把白球（|1⟩）丢进 H 门盒子，结果应该和黑球一样", init: { ball: "white", path: ["h"] } },
    { n: 3, title: "关 3：H² = I", desc: "同一个球连续过两次 H 门盒子——它竟然变回原色！", init: { ball: "black", path: ["h", "h"] } },
  ];

  /* H 门作用：|0⟩→(|0⟩+|1⟩)/√2, |1⟩→(|0⟩-|1⟩)/√2 → 测量都是 50/50 */
  function getProbability() {
    // 球经过 N 次 H 门后测量的 P(|0⟩)
    let p0 = state.ballColor === "black" ? 1 : 0;
    for (let i = 0; i < state.path.length; i++) p0 = 0.5;
    // H² = I：偶数次 H 恢复原态
    if (state.path.length % 2 === 0) {
      p0 = state.ballColor === "black" ? 1 : 0;
    }
    return p0;
  }

  /* SVG：黑球 / 白球 / H 盒子 */
  function ballSVG(color, size = 40) {
    const fill = color === "black" ? "#1e293b" : "#f8fafc";
    const stroke = color === "black" ? "#0f172a" : "#94a3b8";
    return `<svg width="${size}" height="${size}" viewBox="0 0 40 40">
      <circle cx="20" cy="20" r="16" fill="${fill}" stroke="${stroke}" stroke-width="2"/>
      <ellipse cx="15" cy="14" rx="5" ry="3" fill="rgba(255,255,255,.3)"/>
    </svg>`;
  }

  function hboxSVG(width = 90, height = 60, label = "H") {
    return `<svg width="${width}" height="${height}" viewBox="0 0 90 60">
      <rect x="5" y="5" width="80" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
      <text x="45" y="34" text-anchor="middle" font-size="22" font-family="monospace" fill="#2563eb">${label}</text>
      <text x="45" y="50" text-anchor="middle" font-size="9" fill="#6b7280">H 门（神奇的盒子）</text>
      <circle cx="5" cy="30" r="3" fill="#2563eb"/>
      <circle cx="85" cy="30" r="3" fill="#2563eb"/>
    </svg>`;
  }

  function render() {
    const lv = LEVELS[state.level - 1];
    const content = state._container || document.getElementById("lesson-content");
    if (!content) return;
    // 路径链
    let chain = "";
    for (let i = 0; i < state.path.length; i++) {
      chain += `<div class="chain-box">${hboxSVG()}</div>`;
      if (i < state.path.length - 1) chain += `<div class="chain-arrow">→</div>`;
    }
    content.innerHTML = `
      <div class="hgate-stage">
        <h3 style="margin-bottom:4px">${lv.title}</h3>
        <p class="muted" style="margin-bottom:14px">${lv.desc}</p>
        <div class="hgate-chain">
          <div class="chain-ball">${ballSVG(state.ballColor)}<span class="chain-label">${state.ballColor === "black" ? "黑球 |0⟩" : "白球 |1⟩"}</span></div>
          <div class="chain-arrow">→</div>
          ${chain}
        </div>
        <div class="hgate-actions">
          <button id="hg-run" class="btn primary">📊 测量 5000 次</button>
          <button id="hg-reset" class="btn">重置</button>
          <span id="hg-level-nav"></span>
        </div>
        <div id="hg-result" class="hgate-result"></div>
        <div id="hg-hist" class="hgate-hist" style="height:160px;margin-top:12px"></div>
      </div>`;
    document.getElementById("hg-run").addEventListener("click", run);
    document.getElementById("hg-reset").addEventListener("click", () => {
      state.result = null;
      render();
    });
    // 关卡导航
    const nav = document.getElementById("hg-level-nav");
    nav.innerHTML = LEVELS.map((l, i) =>
      `<button class="chip ${i + 1 === state.level ? "active" : ""}" onclick="HGate.goLevel(${i + 1})">关${i + 1}</button>`).join("");
  }

  function goLevel(n) {
    state.level = n;
    const init = LEVELS[n - 1].init;
    state.ballColor = init.ball;
    state.path = init.path;
    state.result = null;
    // 切换关卡 → 重置测量（避免旧关统计混入）
    if (state.measure && !state.measure.isRunning()) state.measure.reset();
    render();
  }

  function run() {
    const shots = 5000;
    const p0 = getProbability();
    if (!state.measure) {
      state.measure = MeasurePanel.create({
        container: document.getElementById("hg-hist"),
        getProbability,
        labels: ["黑 |0⟩", "白 |1⟩"],
        theory: () => {
          const pp0 = getProbability();
          return [pp0, 1 - pp0];
        },
        title: "测量结果",
      });
    }
    state.measure.batch(shots);
    const { counts, shots: total } = state.measure.getCounts();
    const c0 = counts[0], c1 = counts[1];
    const result = document.getElementById("hg-result");
    let msg;
    if (state.level === 3) {
      const isBlack = state.ballColor === "black";
      const gotBlack = c0 > total * 0.98;
      msg = gotBlack === isBlack
        ? `<span class="ok">✓ 太棒了！球连续过两次 H 门，变回了原来的${state.ballColor === "black" ? "黑" : "白"}色！这就是 H² = I（两次 H 门等于没操作）</span>`
        : `<span class="err">✗ 结果不符：期望回${state.ballColor === "black" ? "黑" : "白"}色。再试一次？</span>`;
    } else {
      const near5050 = Math.abs(c0 / total - 0.5) < 0.03;
      msg = near5050
        ? `<span class="ok">✓ 看到了吗？${state.ballColor === "black" ? "黑" : "白"}球进 H 门，出来是约一半黑一半白（${(c0 / total * 100).toFixed(1)}% 黑）——这就是叠加态！</span>`
        : `<span class="err">✗ 统计偏差过大，重测一次看看。</span>`;
    }
    result.innerHTML = msg + `<br><span class="muted">实测：黑=${c0} (${(c0 / total * 100).toFixed(1)}%), 白=${c1} (${(c1 / total * 100).toFixed(1)}%) · 理论 P(|0⟩)=${(p0 * 100).toFixed(1)}%</span>`;
  }

  function init(container) {
    state._container = container || null;
    render();
  }

  return { init, goLevel };
})();
