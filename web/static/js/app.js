/* app.js — LoomQ Web 工作台前端逻辑 */

const App = (() => {
  const state = {
    circuits: [],
    selected: null,
    qasm: "",
    lang: "zh",
    chat: [],
    machine: null,     // L3 噪声机器：ideal/linear/grid/noisy
    machines: [],      // 机器定义（/api/machines）
  };

  /* ---------- 活动栏切换 ---------- */
  function initActivity() {
    document.querySelectorAll(".activity-item").forEach(el => {
      el.addEventListener("click", () => {
        document.querySelectorAll(".activity-item").forEach(e => e.classList.remove("active"));
        el.classList.add("active");
        switchView(el.dataset.view);
      });
    });
  }

  function switchView(view) {
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    const el = document.getElementById("view-" + view);
    if (el) el.classList.add("active");
    // 首页视图：每次进入都按设置开关渲染（引导 或 真机驾驶舱）
    if (view === "home") showHome();
  }

  /* ---------- 首页：新手引导（开关开） 或 量子真机驾驶舱（开关关） ---------- */
  function showHome() {
    const guideEl = document.getElementById("home-guide");
    const machinesEl = document.getElementById("home-machines");
    if (!guideEl || !machinesEl) return;
    const guideOff = localStorage.getItem("loomq_guide") === "off";
    guideEl.style.display = guideOff ? "none" : "block";
    machinesEl.style.display = guideOff ? "block" : "none";
    if (guideOff) {
      guideEl.innerHTML = "";
      loadMachineStatus();
    } else if (typeof Onboarding !== "undefined") {
      // 每次进首页都从第 0 页重新渲染引导；「开始使用/跳过」→ 设置视图并高亮开关
      Onboarding.render(guideEl, {
        onFinish: () => { switchView("settings"); highlightGuide(); }
      });
    }
  }

  async function loadMachineStatus() {
    const box = document.getElementById("home-machines");
    box.innerHTML = `
      <div class="home-header">
        <h1>量子真机驾驶舱</h1>
        <p class="muted">三台真机在线状态 · 只读探活，绝不提交作业（不消耗悟空机时）</p>
      </div>
      <div class="machine-grid" id="machine-grid">
        <div class="machine-loading">正在检查量子真机在线状态…</div>
      </div>
      <p class="muted machine-note" id="machine-note"></p>`;
    const grid = document.getElementById("machine-grid");
    try {
      const res = await fetch("/api/machines/status");
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      if (!data.machines || !data.machines.length) {
        grid.innerHTML = `<div class="dict-none">未发现已配置的量子真机（config/machines.yaml 中 status=available）</div>`;
        return;
      }
      grid.innerHTML = data.machines.map(machineCard).join("");
      const note = document.getElementById("machine-note");
      if (note) {
        const t = new Date(data.checked_at);
        note.textContent = `检查于 ${t.toLocaleString()} · ${data.cached ? "1 小时内已检查" : "本次为实时检查"}`;
      }
    } catch (e) {
      grid.innerHTML = `<div class="dict-none">真机状态检查失败：${e.message || e}</div>`;
    }
  }

  const MACHINE_IMG = {
    "spinq_gemini_2q": "/static/img/machines/gemini_2q.png",
    "spinq_triangulum_3q": "/static/img/machines/triangulum_3q.png",
    "wukong180": "/static/img/machines/wukong180.png",
  };
  function machineIcon(id) {
    const src = MACHINE_IMG[id];
    if (src) return `<img class="m-icon" src="${src}" alt="${id}" loading="lazy">`;
    return `<div class="m-icon m-icon-fallback">${(id || "?").slice(0, 2).toUpperCase()}</div>`;
  }

  function machineCard(m) {
    const on = !!m.online;
    return `
      <div class="machine-card ${on ? "online" : "offline"}">
        <div class="machine-art">${machineIcon(m.id)}</div>
        <div class="machine-name">${m.name || m.id}</div>
        <div class="machine-vendor">${m.vendor || ""} · ${m.phys || ""} · ${m.bits || "?"} 比特</div>
        <div class="machine-status">
          <span class="status-dot ${on ? "ok" : "down"}"></span>
          <span class="status-text">${on ? "在线" : "离线"}</span>
        </div>
        <div class="machine-reason">${m.reason || ""}</div>
      </div>`;
  }

  function highlightGuide() {
    const card = document.getElementById("guide-settings-card");
    if (!card) return;
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.classList.remove("guide-flash");
    void card.offsetWidth; // 重启动画
    card.classList.add("guide-flash");
  }

  /* ---------- 量子游戏（独立视图，文案从 JSON 渲染） ---------- */
  const GAME_LIST = [
    { id: "socks", icon: "🧦", name: "伯特曼的袜子", tag: "纠缠", desc: "用一只袜子体验量子纠缠（贝尔的经典比喻）" },
    { id: "schwinger", icon: "🧊", name: "施温格积木", tag: "测量代数", desc: "拼积木判断粒子能否通过——狄拉克记号与矩阵力学的玩具版" },
  ];

  async function loadGames() {
    const list = document.getElementById("games-list");
    list.innerHTML = GAME_LIST.map(g => `
      <div class="game-card" data-id="${g.id}">
        <span class="game-icon">${g.icon}</span>
        <div class="game-body">
          <div class="game-name">${g.name} <span class="game-tag">${g.tag}</span></div>
          <div class="game-desc">${g.desc}</div>
        </div>
        <span class="game-enter">▶ 进入</span>
      </div>`).join("");
    list.querySelectorAll(".game-card").forEach(card => {
      card.addEventListener("click", () => openGame(card.dataset.id));
    });
  }

  async function openGame(id) {
    const detail = document.getElementById("game-detail");
    const res = await fetch(`/api/game-content/${id}`);
    if (!res.ok) { detail.innerHTML = `<div class="dict-none">游戏文案加载失败</div>`; return; }
    const data = await res.json();

    // 文案 section（词典名词链接化）
    let html = `<div class="game-header">
      <h2>${data.title}</h2><p class="muted">${data.subtitle}</p>
      <button id="game-back" class="btn sm">← 返回游戏列表</button>
    </div>`;
    data.sections.forEach(sec => {
      const bodyHtml = sec.body.split("\n").map(p => {
        const trimmed = p.trim();
        if (!trimmed) return "";
        if (trimmed.startsWith("•")) return `<li>${linkifyDict(trimmed.slice(1).trim(), helpDictIndex)}</li>`;
        return `<p>${linkifyDict(trimmed, helpDictIndex)}</p>`;
      }).join("");
      // 文字介绍：details 原生折叠（默认 open=展开，可手动收起），游戏本体永不折叠
      html += `<details class="game-sec" open data-id="${sec.id}">
        <summary>${sec.title}</summary>
        <div class="game-sec-body">${bodyHtml}</div></details>`;
    });
    // 词典词条卡片（可折叠）
    if (data.dict_terms && data.dict_terms.length) {
      html += `<details class="game-sec" open><summary>本页涉及的词典词条（点击查看）</summary>
        <div class="dict-term-row">`;
      data.dict_terms.forEach(t => {
        html += `<a class="dict-term-chip" data-en="${t.en}">${t.en}（${t.zh}）</a>`;
      });
      html += `</div></details>`;
    }
    // 游戏本体容器（socks.js 渲染到 socks-game）——永远展开
    html += `<div class="game-play" id="game-play"></div>`;
    detail.innerHTML = html;

    // 词典链接：点击弹小窗（不切视图）
    detail.querySelectorAll(".dict-link, .dict-term-chip").forEach(a => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        showDictModal(a.dataset.en);
      });
    });
    document.getElementById("game-back").addEventListener("click", () => {
      detail.innerHTML = "";
      document.getElementById("games-list").scrollIntoView({ behavior: "smooth" });
    });

    // 渲染游戏本体（socks.js 委托）
    if (id === "socks") {
      document.getElementById("game-play").innerHTML = `
        <div class="socks-panel">
          <h2 style="margin-bottom:4px">🧦 伯特曼的袜子（纠缠配对）</h2>
          <p class="muted" style="margin:10px 0">8 只袜子 = 4 双"纠缠对"（可切换 8 双完整版）。翻开一只，用纠缠规则推理并找到它的伙伴。</p>
          <div class="socks-ctrl">
            <label>配对模式：
              <select id="socks-mode">
                <option value="same">同面（|00⟩↔|11⟩：每对同色——红红或绿绿）</option>
                <option value="diff">异面（|01⟩↔|10⟩：一红一绿·经典伯特曼）</option>
              </select>
            </label>
            <label>双数：
              <select id="socks-count">
                <option value="4">4 双（快速）</option>
                <option value="8">8 双（完整）</option>
              </select>
            </label>
            <button id="socks-restart" class="btn sm">重新开始</button>
            <span id="socks-timer" class="socks-timer">⏱ 00:00</span>
            <span id="socks-score" class="socks-score">配对：0/4</span>
          </div>
          <div id="socks-board" class="socks-board"></div>
          <div id="socks-msg" class="socks-msg"></div>
          <div id="socks-win" class="socks-win" style="display:none"></div>
        </div>`;
      if (typeof Socks !== "undefined") Socks.init();
    } else if (id === "schwinger") {
      document.getElementById("game-play").innerHTML = `
        <div class="schwinger-panel">
          <h2 style="margin-bottom:4px">🧊 施温格积木（测量代数）</h2>
          <p class="muted" style="margin:10px 0">8 关：拼积木判断粒子能否通过。每块积木 = 一台筛子（投影算符）。</p>
          <div class="sw-ctrl">
            <span id="sw-timer" class="socks-timer">⏱ 00:00</span>
          </div>
          <div id="sw-game"></div>
          <div id="sw-win" class="socks-win" style="display:none"></div>
        </div>`;
      if (typeof Schwinger !== "undefined") Schwinger.init();
    }
  }

  /* ---------- 电路库 ---------- */
  async function loadCircuits() {
    const res = await fetch("/api/circuits");
    state.circuits = await res.json();
    renderCircuitList("all");
  }

  function renderCircuitList(filter) {
    const list = document.getElementById("circuit-list");
    const items = state.circuits.filter(c => filter === "all" || c.kind === filter);
    list.innerHTML = items.map(c => `
      <div class="circuit-item" data-id="${c.id}">
        <span class="circuit-badge ${c.kind}">${c.kind === "gate" ? "门" : "算法"}</span>
        <span class="circuit-name">${c.name}</span>
      </div>`).join("");
    list.querySelectorAll(".circuit-item").forEach(el => {
      el.addEventListener("click", () => selectCircuit(el.dataset.id));
    });
    // 默认选中第一个
    if (items.length) selectCircuit(items[0].id);
  }

  function selectCircuit(id) {
    state.selected = id;
    const c = state.circuits.find(x => x.id === id);
    state.qasm = c.qasm;
    document.querySelectorAll(".circuit-item").forEach(el => el.classList.toggle("active", el.dataset.id === id));
    renderDetail(c);
    renderCircuit(c.qasm);
  }

  function renderDetail(c) {
    const detail = document.getElementById("circuit-detail");
    const explain = c.kind === "gate"
      ? `<p class="explain">${c.plain}</p>
         <p class="analogy">比喻：${c.analogy}</p>
         <p class="funfact">彩蛋：${c.fun_fact}</p>`
      : `<p class="explain">${c.plain}</p>
         <p class="analogy">为什么有意思：${c.why}</p>
         <p class="funfact">结果：${c.result}</p>`;
    detail.innerHTML = `
      <h3>${c.name}</h3>
      ${explain}
      <div class="detail-actions">
        <button class="btn primary" onclick="App.runSelected('all')">三后端运行</button>
        <button class="btn" onclick="App.copyQasm()">复制 QASM</button>
      </div>
      <textarea id="qasm-editor" spellcheck="false">${c.qasm}</textarea>`;
    document.getElementById("qasm-editor").addEventListener("input", e => {
      state.qasm = e.target.value;
      renderCircuit(state.qasm);
    });
  }

  /* ---------- 电路图 ---------- */
  function renderCircuit(qasm) {
    const container = document.getElementById("circuit-detail");
    let svgBox = container.querySelector(".circuit-svg");
    if (!svgBox) {
      svgBox = document.createElement("div");
      svgBox.className = "circuit-svg";
      container.insertBefore(svgBox, container.querySelector("textarea"));
    }
    svgBox.innerHTML = QCircuit.render(qasm);
  }

  /* ---------- 运行 ---------- */
  async function runSelected(target) {
    log("▶ 开始运行（后端: " + target + "）");
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qasm: state.qasm, target: target, machine: state.machine || null }),
    });
    const data = await res.json();
    if (data.error) { log("✗ " + data.error, true); return; }
    // L3 噪声机器：特殊展示（教育提示）
    if (data.noisy) {
      const r = data.results[data.machine];
      const mark = r.passed ? "✓" : "✗";
      log(`🧪 ${r.backend}: fidelity=${r.fidelity} ${mark}`);
      if (r.counts) renderHistogram(r, data.machine);
      log("📊 " + r.education);
      return;
    }
    if (target === "all") {
      const results = data.results;
      const fidLog = [];
      for (const [t, r] of Object.entries(results)) {
        const mark = r.passed ? "✓" : "✗";
        log(`${t}: fidelity=${r.fidelity} ${mark}`);
        if (r.error) { log("  " + r.error, true); continue; }
        if (r.counts) renderHistogram(r, t);
        fidLog.push(`${t}=${r.fidelity}`);
      }
      const summary = data.all_pass
        ? "结论：三个后端都与参考分布一致（Hellinger ≥ 0.97），电路翻译正确。"
        : "结论：存在后端未达阈值，需检查门映射或相位。";
      log("📊 " + summary);
      log("fidelity: " + fidLog.join(" | "));
    } else {
      const r = data.results[target];
      const mark = r.passed ? "✓" : "✗";
      log(`${target}: fidelity=${r.fidelity} ${mark}`);
      if (r.error) log("  " + r.error, true);
      if (r.counts) renderHistogram(r, target);
      log("📊 " + (r.passed ? "与参考一致，电路翻译正确。" : "未达阈值，需检查。"));
    }
  }

  /* ---------- 直方图（标准组件，Qiskit 惯例） ---------- */
  const charts = {};     // 主区大图（Histogram 实例）
  const miniCharts = {}; // 过程面板小图
  function renderHistogram(r, target) {
    const counts = r.counts || {};
    const reference = r.reference || {};
    const allKeys = [...new Set([...Object.keys(counts), ...Object.keys(reference)])].sort();
    const shots = r.shots || 1;
    const series = [
      { name: "实测", counts: allKeys.map(k => counts[k] || 0), color: "#2563eb" },
      { name: "理论", counts: allKeys.map(k => Math.round((reference[k] || 0) * shots)), color: "#16a34a" },
    ];

    // 主区大图（Histogram 组件）
    const detail = document.getElementById("circuit-detail");
    let box = document.getElementById("histogram-box");
    if (!box) {
      box = document.createElement("div");
      box.id = "histogram-box";
      box.style.cssText = "height:240px;margin-top:12px;";
      detail.appendChild(box);
    }
    if (!charts[target]) charts[target] = Histogram.create(box, {});
    charts[target].setData({
      keys: allKeys, series, shots,
      title: `${target} · fidelity=${r.fidelity}`,
      maxKeys: 8,   // 多比特：最多 8 个位串，其余合并 rest
    });

    // 过程面板小图
    const pbox = document.getElementById("process-charts");
    let mb = document.getElementById("mini-" + target);
    if (!mb) {
      mb = document.createElement("div");
      mb.id = "mini-" + target;
      mb.style.cssText = "height:100px;margin:6px 10px;border:1px solid #e5e7eb;border-radius:8px;";
      pbox.appendChild(mb);
    }
    if (!miniCharts[target]) miniCharts[target] = Histogram.create(mb, { mini: true });
    miniCharts[target].setData({
      keys: allKeys, series: [series[0]], shots,
      title: `${target} fid=${r.fidelity}`,
      maxKeys: 6,
    });
  }

  /* ---------- 执行过程日志 ---------- */
  function log(msg, isErr = false) {
    const el = document.getElementById("process-log");
    const line = document.createElement("div");
    line.className = "log-line" + (isErr ? " err" : "");
    line.textContent = msg;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
  }

  /* ---------- 主题 ---------- */
  function initTheme() {
    const saved = localStorage.getItem("loomq_theme") || "classic";
    document.documentElement.dataset.theme = saved;
    document.querySelectorAll(".theme-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.theme === saved);
      btn.addEventListener("click", () => {
        const t = btn.dataset.theme;
        document.documentElement.dataset.theme = t;
        localStorage.setItem("loomq_theme", t);
        document.querySelectorAll(".theme-btn").forEach(b => b.classList.toggle("active", b.dataset.theme === t));
        // 图表颜色也跟随主题
        Object.values(charts).forEach(c => c.dispose());
        Object.values(miniCharts).forEach(c => c.dispose());
        Object.keys(charts).forEach(k => delete charts[k]);
        Object.keys(miniCharts).forEach(k => delete miniCharts[k]);
      });
    });
  }

  /* ---------- L3 机器选择 ---------- */
  async function initMachine() {
    const sel = document.getElementById("machine-select");
    if (!sel) return;
    // 加载机器定义（词典）
    try {
      const res = await fetch("/api/machines");
      const data = await res.json();
      state.machines = data.machines;
    } catch (e) { /* 词典加载失败不阻塞 */ }
    sel.addEventListener("change", () => {
      const v = sel.value;
      state.machine = v === "none" ? null : v;
      // 更新机器描述
      const desc = document.getElementById("machine-desc");
      if (v === "none") {
        desc.textContent = "三后端本地模拟（无噪声）";
      } else {
        const m = state.machines.find(x => x.id === v);
        desc.textContent = m ? `${m.tagline} · 门保真 ${(m.gate_fidelity * 100).toFixed(1)}% · 测量错误 ${(m.readout_error * 100).toFixed(1)}%` : "";
      }
    });
  }

  /* ---------- 对话框（LLM） ---------- */
  function initChat() {
    document.getElementById("chat-send").addEventListener("click", sendChat);
    document.getElementById("chat-input").addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); }
    });
  }

  async function sendChat() {
    const input = document.getElementById("chat-input");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    addChatMessage("user", msg);
    log("⏳ 正在调用 LLM 生成电路…");
    addChatMessage("assistant", "⏳ 思考中…");

    // 先保存 API key（设置面板）
    const key = document.getElementById("set-key").value;
    if (key) {
      const base = document.getElementById("set-baseurl").value;
      const model = document.getElementById("set-model").value;
      await fetch("/api/settings", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: base, api_key: key, model: model }) });
    }

    const res = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });
    const data = await res.json();
    const last = document.querySelector(".chat-message:last-child");
    if (data.error) {
      if (last) last.textContent = "✗ " + data.error;
      log("✗ " + data.error);
      return;
    }
    if (last) last.textContent = data.reply;
    log("✓ LLM 返回电路并通过自验");
    state.qasm = data.qasm;
    // 阶段 B：勾选「自动搭建」时把电路填入 Composer 并切视图（可继续编辑）
    const autoBuildEl = document.getElementById("chat-auto-build");
    if (autoBuildEl && autoBuildEl.checked && data.qasm) {
      const r = Builder.loadQasm(data.qasm, true);
      if (r.ok) {
        switchView("composer");
        document.querySelectorAll(".activity-item").forEach(e =>
          e.classList.toggle("active", e.dataset.view === "composer"));
        log("⚙ 已自动搭建到新电路（Composer），可继续编辑");
      } else {
        log("⚠ 电路无法在 Composer 中搭建（语法不支持），已保留静态图预览");
      }
    }
    renderCircuit(data.qasm);
  }

  function addChatMessage(role, text) {
    const box = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "chat-message " + role;
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  /* ---------- 工具 ---------- */
  function copyQasm() {
    navigator.clipboard.writeText(state.qasm).then(() => log("✓ QASM 已复制"));
  }

  /* ---------- 设置保存 ---------- */
  function initSettings() {
    document.getElementById("save-key").addEventListener("click", async () => {
      const body = {
        base_url: document.getElementById("set-baseurl").value,
        api_key: document.getElementById("set-key").value,
        model: document.getElementById("set-model").value,
      };
      const res = await fetch("/api/settings", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body) });
      const data = await res.json();
      log(data.ok ? "✓ 设置已保存" : "✗ 保存失败");
    });
    // Key View 切换
    const keyInput = document.getElementById("set-key");
    document.getElementById("toggle-key").addEventListener("click", () => {
      const isPw = keyInput.type === "password";
      keyInput.type = isPw ? "text" : "password";
      document.getElementById("toggle-key").textContent = isPw ? "🙈 Hide" : "👁 View";
    });
    // 本源悟空 Token 保存
    document.getElementById("save-originq").addEventListener("click", async () => {
      const token = document.getElementById("set-originq-token").value.trim();
      if (!token) { log("⚠ 请输入本源量子云 Token"); return; }
      const res = await fetch("/api/settings", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ originq_api_token: token }) });
      const data = await res.json();
      if (data.ok) {
        log("✓ 本源悟空 Token 已保存（仅存本机 config/）");
        document.getElementById("set-originq-token").value = "（已保存，输入新值可覆盖）";
      } else {
        log("✗ Token 保存失败");
      }
    });
    // 本源悟空 Token 可见切换
    const originqInput = document.getElementById("set-originq-token");
    document.getElementById("toggle-originq").addEventListener("click", () => {
      const isPw = originqInput.type === "password";
      originqInput.type = isPw ? "text" : "password";
      document.getElementById("toggle-originq").textContent = isPw ? "🙈 Hide" : "👁 View";
    });
    // 新手引导开关（localStorage，首页二分：引导 或 真机驾驶舱）
    const guideBox = document.getElementById("set-guide");
    guideBox.checked = localStorage.getItem("loomq_guide") !== "off";
    guideBox.addEventListener("change", () => {
      localStorage.setItem("loomq_guide", guideBox.checked ? "on" : "off");
      log(guideBox.checked ? "✓ 新手引导已开启" : "✓ 新手引导已关闭");
      // 首页联动：若当前正停在首页，立即按新开关切换（引导 ↔ 真机面板）
      const homeActive = document.getElementById("view-home").classList.contains("active");
      if (homeActive) showHome();
    });
    // 主题切换
    initTheme();
    // 加载已保存配置
    fetch("/api/settings").then(r => r.json()).then(data => {
      if (data.base_url) document.getElementById("set-baseurl").value = data.base_url;
      if (data.model) document.getElementById("set-model").value = data.model;
      if (data.has_key) keyInput.value = "（已保存，输入新值可覆盖）";
      if (data.has_originq_key) originqInput.value = "（已保存，输入新值可覆盖）";
    });
  }

  /* ---------- 初始化 ---------- */
  async function init() {
    initActivity();
    await loadCircuits();
    initChat();
    initSettings();
    initMachine();
    loadHelp();
    loadCourse();
    loadGames();   // 量子游戏视图（socks 等游戏本体在 openGame 时动态初始化）
    if (typeof Builder !== "undefined") Builder.init();
    initBloch();
    // 过滤芯片
    document.querySelectorAll(".chip").forEach(chip => {
      chip.addEventListener("click", () => {
        document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        renderCircuitList(chip.dataset.filter);
      });
    });
    // 首页（S2→v10 首页模式）：首页即引导（设置开）或量子真机驾驶舱（设置关）
    showHome();
  }

  document.addEventListener("DOMContentLoaded", init);

  /* ---------- 帮助 + 词典查询（统一页） ---------- */
  // 词典名词链接化：把帮助文本中出现的词典名词替换为可点击链接
  function linkifyDict(text, dictIndex) {
    if (!text) return text;
    // 按长度降序构造 alternation（避免短词误匹配长词前缀）
    const patterns = dictIndex
      .map(d => d.zh)
      .sort((a, b) => b.length - a.length)
      .map(p => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    if (!patterns.length) return text;
    const re = new RegExp("(" + patterns.join("|") + ")", "g");
    return text.replace(re, (m) => {
      const hit = dictIndex.find(d => d.zh === m);
      return hit ? `<a class="dict-link" data-en="${hit.en}" title="查词典：${hit.zh}">${m}</a>` : m;
    });
  }

  let helpDictIndex = [];
  async function loadHelp() {
    const res = await fetch("/api/help");
    const data = await res.json();
    helpDictIndex = data.dict_index || [];
    const panel = document.getElementById("help-panel");
    let html = `<h2>快速上手</h2><div class="help-steps">`;
    data.steps.forEach(s => {
      html += `<div class="help-step"><span class="step-num">${s.step}</span>${linkifyDict(s.text, helpDictIndex)}</div>`;
    });
    html += `</div><h2>先懂两件事</h2>`;
    data.basics.forEach(b => {
      html += `<div class="help-card"><h3>${b.title}</h3><p>${linkifyDict(b.body, helpDictIndex)}</p></div>`;
    });
    html += `<h2>十二个门</h2><div class="help-grid">`;
    data.gates.forEach(g => {
      html += `<div class="help-card gate"><span class="gate-symbol">${g.symbol}</span>
        <h3>${g.name}</h3><p>${linkifyDict(g.plain, helpDictIndex)}</p><p class="analogy">比喻：${linkifyDict(g.analogy, helpDictIndex)}</p></div>`;
    });
    html += `</div><h2>九个算法</h2><div class="help-grid">`;
    data.algorithms.forEach(a => {
      html += `<div class="help-card algo"><h3>${a.name}</h3><p>${linkifyDict(a.plain, helpDictIndex)}</p>
        <p class="analogy">${linkifyDict(a.why, helpDictIndex)}</p><p class="funfact">结果：${a.result}</p></div>`;
    });
    html += `</div>`;
    panel.innerHTML = html;
    // 名词链接 → 词典小窗
    panel.querySelectorAll(".dict-link").forEach(a => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        showDictModal(a.dataset.en);
      });
    });
    // 搜索框
    const input = document.getElementById("dict-search");
    const btn = document.getElementById("dict-search-btn");
    const doSearch = () => {
      const q = input.value.trim();
      if (q) searchDict(q, false);
    };
    btn.addEventListener("click", doSearch);
    input.addEventListener("keydown", e => { if (e.key === "Enter") doSearch(); });
  }

  // 词典搜索：q 为查询词；exact=true 表示按英文键精确展示卡片
  async function searchDict(q, exact) {
    const box = document.getElementById("dict-results");
    if (!q) { box.innerHTML = ""; return; }
    box.innerHTML = `<div class="dict-loading">搜索中...</div>`;
    const res = await fetch("/api/search?q=" + encodeURIComponent(q));
    const data = await res.json();
    let html = "";
    // 词典词条 → 卡片
    if (data.terms && data.terms.length) {
      html += `<h3 class="dict-sec">词典词条（${data.terms.length}）</h3>`;
      data.terms.forEach(t => {
        html += `<div class="dict-card" id="dc-${t.en}">
          <div class="dict-head"><b>${t.en}</b> <span class="dict-zh">${t.zh}</span>
            <span class="dict-cat">${t.category === "people" ? "人名" : t.category === "tech" ? "术语" : "概念"}</span></div>
          <div class="dict-def">${t.def_zh}</div>
          ${t.detail_zh ? `<div class="dict-detail">${t.detail_zh}</div>` : ""}
          <div class="dict-meta">前置概念：${t.prereqs.length ? t.prereqs.map(p => `<a class="dict-link" data-en="${p}">${p}</a>`).join(", ") : "无"} | 来源：${t.source || "—"}</div>
        </div>`;
      });
    }
    // 帮助内容命中
    if (data.help && data.help.length) {
      html += `<h3 class="dict-sec">帮助内容（${data.help.length}）</h3>`;
      data.help.forEach(h => {
        html += `<div class="help-card"><b>${h.name}</b>（${h.kind === "gate" ? "门" : "算法"}）<p>${h.plain}</p></div>`;
      });
    }
    if (!html) html = `<div class="dict-none">未找到「${q}」相关词条或帮助内容。<br>可尝试：纠缠、量子比特、H 门、QFT、贝尔...</div>`;
    box.innerHTML = html;
    // 卡片里的前置概念链接 → 小窗
    box.querySelectorAll(".dict-link").forEach(a => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        showDictModal(a.dataset.en);
      });
    });
    if (exact) {
      // 精确展示：滚到目标卡片并高亮
      const target = document.getElementById("dc-" + q) || box.querySelector(".dict-card");
      if (target) { target.scrollIntoView({ behavior: "smooth", block: "start" }); target.classList.add("flash"); }
    }
  }

  // 词典小窗（通用 modal，不切视图）：点击词条/链接弹出完整卡片
  async function showDictModal(en) {
    const modal = document.getElementById("dict-modal");
    const body = document.getElementById("dict-modal-body");
    if (!modal) return;
    body.innerHTML = `<div class="dict-loading">加载词条…</div>`;
    modal.style.display = "flex";
    const res = await fetch("/api/dict/" + encodeURIComponent(en));
    if (!res.ok) {
      body.innerHTML = `<div class="dict-none">词典无此词条：${en}</div>`;
      return;
    }
    const t = await res.json();
    const cat = t.category === "people" ? "人名" : t.category === "tech" ? "术语" : "概念";
    const pre = (t.prereqs || []).map(p =>
      `<a class="dict-link" data-en="${p}">${p}</a>`).join(", ");
    body.innerHTML = `
      <div class="dict-head"><b>${t.en}</b> <span class="dict-zh">${t.zh}</span>
        <span class="dict-cat">${cat}</span></div>
      <div class="dict-def">${t.def_zh}</div>
      <div class="dict-detail">${t.detail_zh || t.detail_en || ""}</div>
      <div class="dict-meta">前置概念：${pre || "无"} | 来源：${t.source || "—"}</div>`;
    // 前置概念链接可再点
    body.querySelectorAll(".dict-link").forEach(a => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        showDictModal(a.dataset.en);
      });
    });
  }

  function closeDictModal() {
    const modal = document.getElementById("dict-modal");
    if (modal) modal.style.display = "none";
  }
  document.addEventListener("click", e => {
    if (e.target.closest && e.target.closest("[data-close]")) closeDictModal();
  });

  /* ---------- 教程课程树 ---------- */
  let currentLesson = null;  // 当前展开的课（accordion）
  async function loadCourse() {
    const res = await fetch("/api/course");
    const courses = await res.json();
    const tree = document.getElementById("course-tree");
    tree.innerHTML = courses.map(c => `
      <div class="course-card ${c.status}" data-id="${c.id}" data-game="${c.game}" data-status="${c.status}">
        <div class="course-num">${c.num}</div>
        <div class="course-body">
          <div class="course-title">${c.title}</div>
          <div class="course-sub">${c.subtitle}</div>
          <div class="course-desc">${c.desc}</div>
        </div>
        <div class="course-status">${c.status === "ready" ? "▶ 可玩" : "🔒 规划中"}</div>
      </div>`).join("");
    // 点击课程：折叠展开 lesson-content（统一在课程视图内）
    tree.querySelectorAll(".course-card").forEach(el => {
      el.addEventListener("click", () => openLesson(el));
    });
    // 默认打开第1课
    const first = tree.querySelector(".course-card.ready");
    if (first && first.dataset.game === "hgate" && typeof HGate !== "undefined") {
      openLesson(first);
    }
  }

  function openLesson(el) {
    const game = el.dataset.game;
    const status = el.dataset.status;
    const title = el.querySelector(".course-title").textContent;
    const content = document.getElementById("lesson-content");
    // accordion：点同一关卡折叠，再次点展开
    if (currentLesson === el) {
      currentLesson = null;
      content.innerHTML = "";
      el.classList.remove("active-lesson");
      return;
    }
    // 取消之前的
    document.querySelectorAll(".course-card.active-lesson").forEach(c => c.classList.remove("active-lesson"));
    currentLesson = el;
    el.classList.add("active-lesson");
    if (game === "hgate" && typeof HGate !== "undefined") {
      content.innerHTML = `<div class="lesson-toolbar"><span>📚 当前：${title}</span><button id="lesson-back" class="btn sm">返回课程树</button></div><div id="lesson-body"></div>`;
      document.getElementById("lesson-back").addEventListener("click", () => {
        currentLesson = null; content.innerHTML = ""; el.classList.remove("active-lesson");
      });
      // H门游戏渲染到 lesson-body
      const body = document.getElementById("lesson-body");
      body.innerHTML = "";
      HGate.init(body);
      // 把 HGate 的渲染目标换成 body（默认是 lesson-content，需改造 HGate.render 让其接受容器）
    } else if (game === "bloch") {
      content.innerHTML = `<div class="lesson-toolbar"><span>📚 当前：${title}</span><button id="lesson-back" class="btn sm">返回课程树</button><button id="lesson-open" class="btn primary sm">→ 打开布洛赫球视图</button></div>
        <div class="lesson-preview">
          <h3>本课预览：相位转盘实验</h3>
          <p>拖动 θ/φ 滑块看态矢量在布洛赫球上旋转——相位门的秘密藏在方位角里。点"打开布洛赫球视图"进入完整 3D 互动。</p>
        </div>`;
      document.getElementById("lesson-back").addEventListener("click", () => {
        currentLesson = null; content.innerHTML = ""; el.classList.remove("active-lesson");
      });
      document.getElementById("lesson-open").addEventListener("click", () => switchView("bloch"));
    } else if (game === "socks") {
      content.innerHTML = `<div class="lesson-toolbar"><span>📚 当前：${title}</span><button id="lesson-back" class="btn sm">返回课程树</button><button id="lesson-open" class="btn primary sm">→ 打开伯特曼袜子</button></div>
        <div class="lesson-preview">
          <h3>本课预览：伯特曼的袜子（贝尔的经典比喻）</h3>
          <p>翻开一只袜子，用纠缠规则推理另一只——量子世界就是这样关联的。点"打开伯特曼袜子"在布洛赫球视图下方玩。</p>
        </div>`;
      document.getElementById("lesson-back").addEventListener("click", () => {
        currentLesson = null; content.innerHTML = ""; el.classList.remove("active-lesson");
      });
      document.getElementById("lesson-open").addEventListener("click", () => switchView("bloch"));
    } else if (status === "planned") {
      content.innerHTML = `<div class="lesson-toolbar"><span>📚 ${title}</span><button id="lesson-back" class="btn sm">返回课程树</button></div>
        <div class="lesson-preview">
          <h3>本课规划中</h3>
          <p>${el.querySelector(".course-desc").textContent}</p>
        </div>`;
      document.getElementById("lesson-back").addEventListener("click", () => {
        currentLesson = null; content.innerHTML = ""; el.classList.remove("active-lesson");
      });
    }
    // 滚动到 lesson-content
    content.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ---------- 布洛赫球 + 量子转盘 ---------- */
  let bloch = null;
  function initBloch() {
    if (typeof Bloch === "undefined") return;
    const container = document.getElementById("bloch-container");
    if (!container || bloch) return;
    bloch = Bloch.create(container, { size: 340 });
    // 初始状态 |0⟩（延迟到 THREE 加载完成后，通过回调设置）
    if (typeof bloch.onReady === "function") {
      bloch.onReady(() => {
        bloch.setState(0, 0);
        updateProb();
      });
    }
    // 滑块联动
    const thSlider = document.getElementById("bloch-theta");
    const phSlider = document.getElementById("bloch-phi");
    const syncFromSliders = () => {
      const th = Number(thSlider.value) * Math.PI / 180;
      const ph = Number(phSlider.value) * Math.PI / 180;
      bloch.setState(th, ph);
      updateProb();
    };
    thSlider.addEventListener("input", syncFromSliders);
    phSlider.addEventListener("input", syncFromSliders);
    // 门按钮
    document.querySelectorAll(".gate-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        bloch.applyGate(btn.dataset.gate);
        // 同步滑块
        const st = bloch.getState();
        thSlider.value = Math.round(st.theta * 180 / Math.PI);
        phSlider.value = Math.round(st.phi * 180 / Math.PI);
        document.getElementById("bloch-theta-val").textContent = thSlider.value + "°";
        document.getElementById("bloch-phi-val").textContent = phSlider.value + "°";
        updateProb();
      });
    });
    // 测量：统一 MeasurePanel v2（累积+5000，实时直方图，切换门/滑块重置）
    const blochMeas = (typeof MeasurePanel !== "undefined")
      ? MeasurePanel.create({
          container: document.getElementById("bloch-hist"),
          getProbability: () => Math.pow(Math.cos(bloch.getState().theta / 2), 2),
          labels: ["|0⟩", "|1⟩"],
          // 理论值动态获取（随态变化）
          theory: () => {
            const p0 = Math.pow(Math.cos(bloch.getState().theta / 2), 2);
            return [p0, 1 - p0];
          },
          title: "测量结果",
          // 文字摘要（直方图由 MeasurePanel 内部渲染）
          onUpdate: (st) => {
            const { counts, shots } = st;
            if (!shots) { document.getElementById("bloch-result").textContent = ""; return; }
            document.getElementById("bloch-result").textContent =
              `🎲 已测 ${shots} 次：|0⟩=${counts[0]} (${(counts[0] / shots * 100).toFixed(1)}%), |1⟩=${counts[1]} (${(counts[1] / shots * 100).toFixed(1)}%)`;
          },
        }) : null;

    // "测量"（累积式，实时直方图）
    document.getElementById("bloch-measure").addEventListener("click", () => {
      if (blochMeas) blochMeas.accumulate(1);
    });

    // "测量 5000 次"（渐进式实时直方图）
    document.getElementById("bloch-measure-5000").addEventListener("click", () => {
      if (blochMeas) blochMeas.batch(5000);
    });

    // 切换门/滑块 → 重置测量（避免旧统计混入新态）
    function blochResetMeasure() {
      if (blochMeas && !blochMeas.isRunning()) blochMeas.reset();
    }
    thSlider.addEventListener("input", blochResetMeasure);
    phSlider.addEventListener("input", blochResetMeasure);
    document.querySelectorAll(".gate-btn").forEach(btn => {
      btn.addEventListener("click", blochResetMeasure);
    });
  }

  function updateProb() {
    if (!bloch) return;
    const st = bloch.getState();
    const p0 = Math.pow(Math.cos(st.theta / 2), 2);
    const bar = document.getElementById("prob-p0");
    bar.style.width = (p0 * 100) + "%";
    bar.textContent = "P(|0⟩) = " + Math.round(p0 * 100) + "%";
  }

  /* ---------- 搭建电路运行（builder.js 调用） ---------- */
  function runBuilder(qasm) {
    state.qasm = qasm;
    renderCircuit(qasm);
    log("▶ 运行搭建的电路");
    fetch("/api/run", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qasm: qasm, target: "all", shots: 8192 }),
    }).then(r => r.json()).then(data => {
      if (data.error) { log("✗ " + data.error, true); return; }
      for (const [t, r] of Object.entries(data.results)) {
        const mark = r.passed ? "✓" : "✗";
        log(`${t}: fidelity=${r.fidelity} ${mark}`);
        if (r.counts) renderHistogram(r, t);
      }
      log("📊 " + (data.all_pass ? "搭建的电路三后端一致，正确！" : "存在未达阈值。"));
    });
  }

  return { runSelected, copyQasm, runBuilder, searchDict, switchView, showDictModal, closeDictModal };
})();

// 暴露给其他模块（socks.js 胜利横幅词典链接等）
window.App = App;
window.searchDict = (q, exact) => App.searchDict(q, exact);
window.showDictModal = (en) => App.showDictModal(en);
window.closeDictModal = () => App.closeDictModal();
