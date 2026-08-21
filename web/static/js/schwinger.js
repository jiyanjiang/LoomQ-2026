/* schwinger.js — 施温格积木（测量代数）游戏
 *
 * 历史原型：Papaliolios 1960s 哈佛"量子玩具"——13 个铝制立方体，
 *   代表投影算符/泡利算符，外刻狄拉克记号。本游戏取核心 4 块投影：
 *   |↑⟩⟨↑| (z+)、|↓⟩⟨↓| (z−)、|+⟩⟨+| (x+)、|−⟩⟨−| (x−)
 *
 * 判定规则（数学确定）：相邻两块积木所代表的态正交 → 粒子被挡（概率 0）；
 *   否则通过（概率 > 0）。"通过"是比喻，表示测量结果是否可能。
 *
 * 通俗解读（水果类比）：两套分类标准——颜色(黄=z+/绿=z−)、形状(香蕉=x+/苹果=x−)。
 *   同标准互斥 → 挡；跨标准兼容 → 通过（黄香蕉，概率 1/2）。
 *
 * 获胜：8 关全部答对。计时器复用袜子模式（首答启动，通关停止）。
 */

const Schwinger = (() => {
  // 四种积木（态 → 通俗名 → 解释文案）
  const BLOCKS = {
    up:    { label: "|↑⟩⟨↑|", state: "|↑⟩", fruit: "黄色",   desc: "z 方向 + 的投影筛子" },
    down:  { label: "|↓⟩⟨↓|", state: "|↓⟩", fruit: "绿色",   desc: "z 方向 − 的投影筛子" },
    plus:  { label: "|+⟩⟨+|", state: "|+⟩", fruit: "香蕉形", desc: "x 方向 + 的投影筛子" },
    minus: { label: "|−⟩⟨−|", state: "|−⟩", fruit: "苹果形", desc: "x 方向 − 的投影筛子" },
  };

  // 正交判定表（true = 正交 = 挡）
  // 只有 4 对正交：↑↓、↓↑、+−、−+（⟨a|b⟩=0）
  const ORTHO = {
    up:    { up: false,    down: true,     plus: false,    minus: false },
    down:  { up: true,     down: false,    plus: false,    minus: false },
    plus:  { up: false,    down: false,    plus: false,    minus: true },
    minus: { up: false,    down: false,    plus: true,     minus: false },
  };

  // 态向量（S_z 基）：用于精确出射强度计算
  const VECTORS = {
    up:    [1, 0],
    down:  [0, 1],
    plus:  [1 / Math.sqrt(2), 1 / Math.sqrt(2)],
    minus: [1 / Math.sqrt(2), -1 / Math.sqrt(2)],
  };
  function ip(a, b) { return a[0] * b[0] + a[1] * b[1]; }
  // 出射强度：首块 |⟨目标|入射⟩|² × 后续每块 |⟨后|前⟩|²
  function beamIntensity(incident, blocks) {
    let r = 1.0;
    let prev = VECTORS[incident];
    for (const b of blocks) {
      const f = ip(VECTORS[b], prev) ** 2;
      if (Math.abs(f) < 1e-9) return 0;
      r *= f;
      prev = VECTORS[b];
    }
    return r;
  }
  // 目标强度匹配（数值容差）
  function matchesTarget(intensity, target) {
    return Math.abs(intensity - target) < 1e-6;
  }

  // 8 关：给定入射粒子态 + 积木串，判断粒子能否通过（透/挡）；第 8 关 build 自由拼
  // 每关 incident = 入射粒子态，blocks = 题面积木串（[] 表示第 8 关自由拼）
  const LEVELS = [
    { incident: "up",   blocks: ["up"],              explain: "一块筛子 |↑⟩⟨↑|：入射 |↑⟩ 已经是 z 方向 +，投影到自己的本征态原样通过（幂等：|↑⟩⟨↑|²=|↑⟩⟨↑|）。粒子通过！" },
    { incident: "up",   blocks: ["up", "up"],        explain: "同一台筛子筛两次，筛过的还是它自己（|↑⟩⟨↑|²=|↑⟩⟨↑|，幂等）。粒子通过！" },
    { incident: "up",   blocks: ["up", "down"],      explain: "先 |↑⟩⟨↑| 通过，再 |↓⟩⟨↓|：|↑⟩ 与 |↓⟩ 正交（⟨↑|↓⟩=0）——|↑⟩ 里没有 |↓⟩ 分量，粒子被挡住！" },
    { incident: "up",   blocks: ["plus", "minus"],   explain: "先 |+⟩⟨+| 放行 |↑⟩ 的一半，再 |−⟩⟨−|：|+⟩ 与 |−⟩ 正交（⟨+|−⟩=0），|+⟩ 里没有 |−⟩ 分量——粒子被挡住！" },
    { incident: "up",   blocks: ["up", "plus"],      explain: "先 |↑⟩⟨↑| 通过，再 |+⟩⟨+|：跨基投影（|⟨+|↑⟩|²=1/2≠0），|↑⟩ 里含 |+⟩ 分量——粒子通过（概率 1/2）！" },
    { incident: "down", blocks: ["down", "plus"],    explain: "入射 |↓⟩，先 |↓⟩⟨↓| 通过，再 |+⟩⟨+|：跨基（|⟨+|↓⟩|²=1/2≠0），粒子通过（概率 1/2）！与第 5 关对称——跨基能否通过与入射是 ↑ 还是 ↓ 无关。" },
    { incident: "up",   blocks: ["up", "plus", "down"], explain: "★核心谜题！|↑⟩ → |↑⟩⟨↑|（通过）→ |+⟩⟨+|（1/2）→ |↓⟩⟨↓|（1/2）：粒子竟然通过！测 x 扰动 z，|↓⟩ 分量重新出现——非对易 [σz,σx]≠0！" },
    { incident: "up",   blocks: [],                  explain: "挑战关完成！原理：挡住粒子 = 让积木串中含一对正交投影（如 |↑⟩ 与 |↓⟩，⟨↑|↓⟩=0），粒子在第一块正交处就全被挡住（排他原理）。" },
  ];

  const state = {
    level: 0,          // 当前关 0-7
    built: [],         // build 关玩家拼的串
    target: "pass",
    correct: 0,
    done: false,
    testMode: false,   // true = 进阶测试模式（8 题）
    testQ: 0,          // 当前测试题下标
    testBuilt: [],     // 测试模式玩家拼的串
    testCorrect: 0,    // 测试答对数
    testTotal: 0,
    questions: null,   // 题库 JSON（/api/schwinger-questions）
    testResult: null,  // 本次提交的判定结果（渲染解读）
  };

  // 计时器（复用袜子模式）
  let _timerId = null, _startTs = null;
  function fmt(ms) { const s = Math.floor(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; }
  function renderTimer() {
    const el = document.getElementById("sw-timer");
    if (el) el.textContent = _startTs ? "⏱ " + fmt(Date.now() - _startTs) : "⏱ 00:00";
  }
  function startTimer() { if (_timerId === null) { _startTs = Date.now(); _timerId = setInterval(renderTimer, 250); renderTimer(); } }
  function stopTimer() { if (_timerId !== null) { clearInterval(_timerId); _timerId = null; } renderTimer(); return _startTs ? Date.now() - _startTs : 0; }
  function resetTimer() { if (_timerId !== null) clearInterval(_timerId); _timerId = null; _startTs = null; renderTimer(); }

  // 判定：相邻正交 → 挡(false)；否则透(true)
  function passes(blocks) {
    for (let i = 0; i + 1 < blocks.length; i++) {
      if (ORTHO[blocks[i]][blocks[i + 1]]) return false;
    }
    return true;
  }

  // 光线 SVG：穿过积木串（遇正交 → 反弹 ❌）
  function beamSvg(blocks, result) {
    const n = Math.max(blocks.length, 1);
    const w = 60 * n + 40;
    let path = `M10,20 L${blocks.length ? 40 + 0 : 60},20`;
    // 简化：画一条穿过所有块的中轴线
    const colors = blocks.map(b => ORTHO ? "" : "");
    return `<svg class="sw-beam" width="${w}" height="40" viewBox="0 0 ${w} 40">
      <line x1="6" y1="20" x2="${w - 6}" y2="20" stroke="${result === "block" ? "#dc2626" : "#16a34a"}" stroke-width="3" stroke-dasharray="${result ? "6,4" : ""}"/>
      ${result === "block" ? `<text x="${w - 30}" y="24" font-size="14" fill="#dc2626">✗</text>` :
        result === "pass" ? `<text x="${w - 30}" y="24" font-size="14" fill="#16a34a">✓</text>` : ""}
    </svg>`;
  }

  // 积木串渲染（方块 + 狄拉克记号）
  function blocksHtml(blocks) {
    return blocks.map((b, i) => `
      <div class="sw-block" data-idx="${i}">
        <span class="sw-ket">${BLOCKS[b].label}</span>
        <span class="sw-fruit">${BLOCKS[b].fruit}</span>
      </div>`).join("") || `<span class="sw-empty">（未拼积木）</span>`;
  }

  // 入射光图形化：|↑⟩ 向上箭头、|↓⟩ 向下箭头、|+⟩ 右上斜箭头、|−⟩ 右下斜箭头、|α⟩ 任意斜箭头
  function incidentSvg(stateName) {
    // 布洛赫球投影箭头（圆的直径方向），圆点 = 态
    let angle = 0; // 与 x 轴夹角（度）
    if (stateName === "up") angle = -90;   // 指向上
    else if (stateName === "down") angle = 90;   // 指向下
    else if (stateName === "plus") angle = -45;  // 右上
    else if (stateName === "minus") angle = -135; // 左上
    else angle = -20; // |α⟩ 任意态：斜上
    const rad = angle * Math.PI / 180;
    const len = 14;
    const x1 = 20 + len * Math.cos(rad), y1 = 20 + len * Math.sin(rad);
    const x2 = 20 - len * Math.cos(rad), y2 = 20 - len * Math.sin(rad);
    // 箭头头
    const hx = x1 + 5 * Math.cos(rad - Math.PI * 3 / 4), hy = y1 + 5 * Math.sin(rad - Math.PI * 3 / 4);
    const gx = x1 + 5 * Math.cos(rad + Math.PI * 3 / 4), gy = y1 + 5 * Math.sin(rad + Math.PI * 3 / 4);
    return `<svg class="sw-incident" width="44" height="44" viewBox="0 0 40 40">
      <circle cx="20" cy="20" r="15" fill="none" stroke="var(--primary)" stroke-opacity=".3" stroke-width="1"/>
      <circle cx="20" cy="20" r="2.2" fill="var(--primary)"/>
      <line x1="${x2}" y1="${y2}" x2="${x1}" y2="${y1}" stroke="var(--primary)" stroke-width="2.2"/>
      <line x1="${x1}" y1="${y1}" x2="${hx}" y2="${hy}" stroke="var(--primary)" stroke-width="2.2"/>
      <line x1="${x1}" y1="${y1}" x2="${gx}" y2="${gy}" stroke="var(--primary)" stroke-width="2.2"/>
    </svg>`;
  }

  function render() {
    const win = document.getElementById("sw-win");
    if (win) win.style.display = "none";
    if (state.testMode) { renderTest(); return; }

    const lv = LEVELS[state.level];
    const isBuild = lv.blocks.length === 0;
    const seq = isBuild ? state.built : lv.blocks;
    const incSym = lv.incident === "up" ? "|↑⟩" : "|↓⟩";

    // 题目说明：build 关（第 8 关）醒目展示目标（只给目标，不给答案）
    const taskTxt = isBuild
      ? `<div class="sw-test-prompt"><b>挑战：</b>入射粒子 ${incSym}（自旋 z 方向 +），请拼出<b>把粒子挡住的积木组合</b>（可从上方托盘选择积木）</div>`
      : `<div class="sw-test-prompt"><b>题目：</b>入射粒子 ${incSym}（自旋 z 方向 ${lv.incident === "up" ? "+" : "−"}），下面这串积木，粒子能否通过？</div>`;

    let html = `
      <div class="sw-level">第 ${state.level + 1} / 8 关 · 已过关 ${state.correct}</div>
      ${taskTxt}
      <div class="sw-seq">
        <div class="sw-seq-title">入射粒子 + 积木串（粒子从左向右穿过）：</div>
        <div class="sw-seq-blocks">
          <div class="sw-incident-block" title="${incSym} ${lv.incident === "up" ? "自旋 z 方向 +" : "自旋 z 方向 −"}">
            ${incidentSvg(lv.incident)}
            <span class="sw-incident-sym">${incSym}</span>
          </div>
          ${blocksHtml(seq)}
        </div>
        <div class="sw-beam-box">${beamSvg(seq, null)}</div>
      </div>
      ${isBuild ? `
        <div class="sw-tray">
          <div class="sw-tray-title">积木托盘（点击加入拼串，目标：挡住入射粒子 |↑⟩）：</div>
          <div class="sw-tray-blocks">
            ${Object.entries(BLOCKS).map(([id, b]) =>
              `<div class="sw-block sw-tray-block ${seq.includes(id) ? "sw-used" : ""}" data-add="${id}">${b.label}</div>`).join("")}
          </div>
        </div>` : `
        <div class="sw-judge">
          <button id="sw-ans-pass" class="btn sm primary">粒子能通过 ✅</button>
          <button id="sw-ans-block" class="btn sm">粒子被挡住 ❌</button>
        </div>`}
      ${isBuild ? `<div class="sw-judge"><button id="sw-ans-block" class="btn sm primary">提交（已拼好）</button><button id="sw-clear" class="btn sm">清空</button></div>` : ""}
      <div id="sw-msg" class="sw-msg"></div>`;

    document.getElementById("sw-game").innerHTML = html;
  }

  function answer(pass) {
    // pass: true=粒子能通过，false=被挡住；build 关：拼串后判断粒子能否通过
    const lv = LEVELS[state.level];
    startTimer();
    const seq = lv.blocks.length === 0 ? state.built : lv.blocks;
    const isBuild = lv.blocks.length === 0;
    const actual = beamIntensity(lv.incident, seq);
    const passed = actual > 0;

    let isCorrect;
    if (isBuild) {
      // 第 8 关：拼出"挡住粒子"（粒子数比=0）——提交即判定，目标 = 挡住
      isCorrect = seq.length > 0 && !passed;
    } else {
      isCorrect = (pass === passed);
    }

    const msg = document.getElementById("sw-msg");
    if (isCorrect) {
      state.correct++;
      msg.innerHTML = `<span class="ok">✓ 正确！粒子${passed ? "通过了" : "被挡住"}。</span> ${lv.explain}`;
      document.querySelector(".sw-beam-box").innerHTML = beamSvg(seq, passed ? "pass" : "block");
    } else {
      msg.innerHTML = `<span class="err">✗ 不对。粒子实际${passed ? "通过了" : "被挡住"}。</span> ${lv.explain}`;
      document.querySelector(".sw-beam-box").innerHTML = beamSvg(seq, passed ? "pass" : "block");
    }
    // 下一关
    setTimeout(() => {
      if (state.correct === LEVELS.length) {
        winGame();
      } else {
        state.level++;
        render();
      }
    }, 1800);
  }

  function winGame() {
    const t = fmt(stopTimer());
    const win = document.getElementById("sw-win");
    win.style.display = "block";
    win.innerHTML = `<div class="sock-win-banner">🎉 8 关全过！你理解了测量代数！用时 ${t}</div>
      <p class="muted">基础关完成！下面是<b>进阶测试</b>——由易到难的 8 道题，拼积木达到指定的出射粒子数比例。</p>
      <button id="sw-start-test" class="btn primary">开始进阶测试 →</button>`;
    win.querySelector("#sw-start-test").addEventListener("click", async () => {
      const res = await fetch("/api/schwinger-questions");
      const data = await res.json();
      state.questions = data;
      state.testMode = true;
      state.testQ = 0;
      state.testBuilt = [];
      state.testCorrect = 0;
      state.testTotal = data.questions.length;
      state.testResult = null;
      startTimer();
      render();
    });
  }

  // ---------- 进阶测试模式 ----------
  function testTargetText(t) {
    if (t === 1) return "出射粒子数 = 入射粒子数（全部通过）";
    if (t === 0.5) return "出射粒子数 = 入射粒子数的 1/2";
    if (t === 0.25) return "出射粒子数 = 入射粒子数的 1/4";
    if (t === 0.125) return "出射粒子数 = 入射粒子数的 1/8";
    if (t === 0) return "出射粒子数 = 0（全部被挡住）";
    return String(t);
  }

  function renderTest() {
    const qs = state.questions.questions;
    const q = qs[state.testQ];
    const inc = q.incident;
    const incSym = inc === "up" ? "|↑⟩" : "|↓⟩";
    const targetTxt = testTargetText(q.target);
    const seq = state.testBuilt;

    // 显示：题目信息 + 拼串区 + 判定区 + 解读区
    let html = `
      <div class="sw-test-header">
        <span class="sw-level">进阶测试 ${state.testQ + 1} / ${state.testTotal} · 答对 ${state.testCorrect}</span>
        <span class="sw-concept">📌 ${q.concept}</span>
      </div>
      <div class="sw-test-prompt">
        <div class="sw-incident-ask"><b>目标：</b>${targetTxt}（入射粒子 ${incSym} ${inc === "up" ? "自旋 z 方向 +" : "自旋 z 方向 −"}）</div>
      </div>
      <div class="sw-seq">
        <div class="sw-seq-title">入射粒子 + 你拼的积木串（粒子从左向右穿过）：</div>
        <div class="sw-seq-blocks">
          <div class="sw-incident-block" title="${incSym} ${inc === "up" ? "自旋 z 方向 +" : "自旋 z 方向 −"}">
            ${incidentSvg(inc)}
            <span class="sw-incident-sym">${incSym}</span>
          </div>
          ${blocksHtml(seq)}
        </div>
        <div class="sw-beam-box">${beamSvg(seq, null)}</div>
        <div class="sw-intensity">当前出射/入射粒子数比：<b>${seq.length ? beamIntensity(inc, seq).toFixed(3) : "—"}</b></div>
      </div>
      <div class="sw-tray">
        <div class="sw-tray-title">积木托盘（每种限用 1 次）：</div>
        <div class="sw-tray-blocks">
          ${Object.entries(BLOCKS).map(([id, b]) =>
            `<div class="sw-block sw-tray-block ${seq.includes(id) ? "sw-used" : ""}" data-add="${id}">${b.label}</div>`).join("")}
        </div>
      </div>
      <div class="sw-judge">
        <button id="sw-test-submit" class="btn sm primary">提交判定</button>
        <button id="sw-clear" class="btn sm">清空</button>
      </div>
      <div id="sw-msg" class="sw-msg"></div>`;

    // 上次提交的解读（对/错都展示，快速学习）
    if (state.testResult) {
      const r = state.testResult;
      html += `<div class="sw-explain ${r.ok ? "ok" : "err"}">${r.html}</div>`;
    }
    document.getElementById("sw-game").innerHTML = html;
  }

  function answerTest() {
    const q = state.questions.questions[state.testQ];
    const seq = state.testBuilt;
    const intensity = beamIntensity(q.incident, seq);
    const ok = matchesTarget(intensity, q.target);
    const targetTxt = testTargetText(q.target);

    let explainHtml;
    if (ok) {
      state.testCorrect++;
      explainHtml = `<b>✓ 正确！出射/入射粒子数比 = ${intensity.toFixed(3)}（目标 ${targetTxt}）</b><br>${q.explain_pass}`;
    } else {
      explainHtml = `<b>✗ 出射/入射粒子数比 = ${intensity.toFixed(3)}（目标 ${targetTxt}）</b><br>${q.explain_fail}`;
    }
    state.testResult = { ok, html: explainHtml };
    // 画光束结果
    render();
    const box = document.querySelector(".sw-beam-box");
    if (box) box.innerHTML = beamSvg(seq, ok ? "pass" : "block");

    // 下一题或完成
    setTimeout(() => {
      if (state.testCorrect >= 0 && state.testQ + 1 < state.testTotal) {
        state.testQ++;
        state.testBuilt = [];
        state.testResult = null;
        render();
      } else if (state.testQ + 1 >= state.testTotal) {
        state.testMode = false;
        testWin();
      }
    }, 2000);
  }

  function testWin() {
    const t = fmt(stopTimer());
    const win = document.getElementById("sw-win");
    win.style.display = "block";
    win.innerHTML = `<div class="sock-win-banner">🎉 进阶测试完成！答对 ${state.testCorrect} / ${state.testTotal} 题！用时 ${t}</div>
      <p class="muted">你掌握了投影保持、正交挡粒子、跨基通过、非对易——测量代数的核心概念齐了。
      这就是施温格"量子玩具"教给学生的东西，矩阵力学真的可以拼着玩。</p>
      <button id="sw-replay" class="btn sm">重新开始</button>`;
    win.querySelector("#sw-replay").addEventListener("click", () => {
      state.level = 0; state.built = []; state.correct = 0; state.testMode = false;
      state.testQ = 0; state.testBuilt = []; state.testCorrect = 0; state.testResult = null;
      resetTimer();
      render();
    });
  }

  function init() {
    state.level = 0; state.built = []; state.correct = 0; state.done = false;
    resetTimer();
    const root = document.getElementById("sw-game");
    if (!root) return;
    if (!root._swBound) {
      root.addEventListener("click", e => {
        const ansPass = e.target.closest("#sw-ans-pass");
        const ansBlock = e.target.closest("#sw-ans-block");
        const add = e.target.closest("[data-add]");
        const clear = e.target.closest("#sw-clear");
        const submit = e.target.closest("#sw-test-submit");
        if (submit && state.testMode) { answerTest(); return; }
        if (ansPass && !state.testMode) {
          if (LEVELS[state.level].blocks.length > 0) { answer(true); return; }
        }
        if (ansBlock && !state.testMode) {
          if (LEVELS[state.level].blocks.length > 0) { answer(false); return; }
          else { answer(true); return; } // build 关：提交拼好的串（目标是挡住粒子）
        }
        if (clear && (state.testMode || LEVELS[state.level].blocks.length === 0)) {
          state.testMode ? (state.testBuilt = []) : (state.built = []);
          render(); return;
        }
        if (add && (state.testMode || LEVELS[state.level].blocks.length === 0)) {
          const id = add.dataset.add;
          if (state.testMode) {
            if (!state.testBuilt.includes(id) && state.testBuilt.length < 4) {
              state.testBuilt.push(id); render();
            }
          } else if (!state.built.includes(id) && state.built.length < 4) {
            state.built.push(id); render();
          }
          return;
        }
      });
      root._swBound = true;
    }
    render();
  }

  return { init };
})();
