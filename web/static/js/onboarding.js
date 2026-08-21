/* onboarding.js — 新手引导 PPT（S2 → v10 首页模式）
 *
 * 首页即引导：设置开关 localStorage.loomq_guide（默认 on）开着时，
 * 每次进入首页（view-home）都渲染完整引导，从第 0 页开始。
 * 关闭引导后首页显示量子真机驾驶舱（见 app.js showHome()）。
 * 「开始使用 / 跳过引导」→ 回调 onFinish（app.js 切到设置并高亮开关）。
 *
 * API：Onboarding.render(container, { onFinish }) —— 容器内渲染，每次全新开始。
 * 文案来源：data/onboarding_copy_v1_20260820.json（DeepSeek v4-pro 打磨稿，10 页）
 */
(function () {
  "use strict";

  const PAGES = [
    {
      title: "欢迎来到量子工作台",
      subtitle: "不用数学，像搭积木一样搭量子电路",
      svg: `<svg class="ob-svg" viewBox="0 0 260 140">
        <!-- q0 量子线 -->
        <line x1="32" y1="45" x2="242" y2="45" stroke="currentColor" stroke-width="2"/>
        <text x="12" y="49" class="ob-ket">q0</text>
        <!-- H 门 -->
        <rect x="80" y="31" width="34" height="28" rx="6" fill="#7C6CF0"/>
        <text x="97" y="51" class="ob-h" text-anchor="middle">H</text>
        <!-- M 测量门 -->
        <rect x="150" y="31" width="28" height="28" rx="6" fill="#E5484D"/>
        <text x="164" y="51" class="ob-h" text-anchor="middle">M</text>
        <!-- 测量结果连到经典寄存器 -->
        <line x1="164" y1="59" x2="164" y2="113" stroke="#E5484D" stroke-width="2.2"/>
        <path d="M158 107 l6 6 6-6" fill="none" stroke="#E5484D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        <!-- c 经典线（双线表示经典寄存器） -->
        <line x1="24" y1="110" x2="242" y2="110" stroke="currentColor" stroke-width="1.5"/>
        <line x1="24" y1="116" x2="242" y2="116" stroke="currentColor" stroke-width="1.5"/>
        <text x="8" y="119" class="ob-ket">c</text>
        <text x="130" y="136" class="ob-tag" text-anchor="middle">搭好就能运行，边玩边学</text>
      </svg>`,
      text: `不用数学，像搭积木一样搭量子电路，搭好就能运行。左边是电路画布，右边有 AI 助手，你说人话它就能帮你搭。哪怕从没学过量子，10 分钟也能跑通第一个实验。`
    },
    {
      title: "量子比特：一个箭头",
      subtitle: "向上 0，向下 1，还能同时朝两个方向",
      svg: `<svg class="ob-svg" viewBox="0 0 260 150">
        <!-- |0⟩ 向上（箭头头完整可见） -->
        <g fill="#7C6CF0">
          <path d="M40 118 h16 v-40 h14 l-22 -26 -22 26 h14 z"/>
        </g>
        <text x="48" y="140" class="ob-tag" text-anchor="middle">|0⟩ 向上</text>
        <!-- |1⟩ 向下 -->
        <g fill="#FFB020">
          <path d="M118 22 h16 v40 h14 l-22 26 -22 -26 h14 z"/>
        </g>
        <text x="126" y="140" class="ob-tag" text-anchor="middle">|1⟩ 向下</text>
        <!-- 叠加：同一根箭杆同时朝上又朝下（箭头头都完整） -->
        <g fill="#7C6CF0" opacity=".55">
          <path d="M210 62 h16 v-18 h14 l-22 -20 -22 20 h14 z"/>
        </g>
        <g fill="#FFB020" opacity=".55">
          <path d="M210 62 h16 v18 h14 l-22 20 -22 -20 h14 z"/>
        </g>
        <text x="218" y="140" class="ob-tag" text-anchor="middle">叠加：既朝上又朝下</text>
      </svg>`,
      text: `量子比特，你可以想象成一个箭头。向上代表 0，向下代表 1。最神奇的是，量子叠加让这个箭头可以同时既朝上又朝下——这在日常世界里完全没法想象。`
    },
    {
      title: "量子门：量子抛硬币",
      subtitle: "|0⟩ 经过 H 门，变成一半一半",
      svg: `<svg class="ob-svg" viewBox="0 0 260 150">
        <text x="14" y="70" class="ob-ket">|0⟩</text>
        <line x1="14" y1="82" x2="60" y2="82" stroke="currentColor" stroke-width="2"/>
        <rect x="68" y="62" width="38" height="40" rx="7" fill="#7C6CF0"/>
        <text x="87" y="90" class="ob-h" text-anchor="middle">H</text>
        <line x1="106" y1="82" x2="132" y2="82" stroke="currentColor" stroke-width="2"/>
        <rect x="140" y="38" width="72" height="16" rx="8" fill="#7C6CF0" opacity=".30"/>
        <rect x="140" y="38" width="36" height="16" rx="8" fill="#7C6CF0"/>
        <text x="140" y="30" class="ob-tag">|0⟩ 约 50%</text>
        <rect x="140" y="92" width="72" height="16" rx="8" fill="#FFB020" opacity=".30"/>
        <rect x="140" y="92" width="36" height="16" rx="8" fill="#FFB020"/>
        <text x="140" y="128" class="ob-tag">|1⟩ 约 50%</text>
        <text x="130" y="146" class="ob-tag" text-anchor="middle">测量一次，落地才知道正反</text>
      </svg>`,
      text: `让箭头从左向右跑，路上会经过一些操作方块，每个方块就是一个量子门。比如 H 门，就像抛一次量子硬币：朝上的箭头经过它，会变成既朝上又朝下的叠加状态。`
    },
    {
      title: "测量：看箭头朝哪",
      subtitle: "单次随机，多测几次才看得出概率",
      svg: `<svg class="ob-svg" viewBox="0 0 260 150">
        <g fill="#7C6CF0" opacity=".55">
          <path d="M14 96 h16 v-34 h14 l-22 -24 -22 24 h14 z"/>
        </g>
        <g fill="#FFB020" opacity=".55">
          <path d="M14 78 h16 v34 h14 l-22 24 -22 -24 h14 z"/>
        </g>
        <line x1="62" y1="76" x2="92" y2="76" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>
        <rect x="96" y="56" width="26" height="40" rx="7" fill="#E5484D"/>
        <text x="109" y="81" class="ob-h" text-anchor="middle">M</text>
        <line x1="122" y1="76" x2="150" y2="76" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>
        <rect x="156" y="44" width="34" height="34" rx="4" fill="#7C6CF0" opacity=".25"/>
        <rect x="156" y="44" width="17" height="34" rx="4" fill="#7C6CF0"/>
        <rect x="198" y="60" width="34" height="18" rx="4" fill="#FFB020" opacity=".25"/>
        <rect x="198" y="60" width="17" height="18" rx="4" fill="#FFB020"/>
        <text x="156" y="36" class="ob-tag">|0⟩</text>
        <text x="198" y="36" class="ob-tag">|1⟩</text>
        <text x="130" y="130" class="ob-tag" text-anchor="middle">重复很多次 → 从统计里读出答案</text>
      </svg>`,
      text: `想知道箭头到底朝哪，就得测量。单次测量结果没法提前知道，只能知道概率：箭头朝上方向成分越大，测出朝上的可能性就越大。所以实验要重复很多次，才能从统计结果里读出答案。`
    },
    {
      title: "多比特：一起动起来",
      subtitle: "十几扇门 + C-NOT，比特们像一个乐队",
      svg: `<svg class="ob-svg" viewBox="0 0 260 150">
        <line x1="24" y1="40" x2="236" y2="40" stroke="currentColor" stroke-width="2"/>
        <line x1="24" y1="75" x2="236" y2="75" stroke="currentColor" stroke-width="2"/>
        <line x1="24" y1="110" x2="236" y2="110" stroke="currentColor" stroke-width="2"/>
        <rect x="72" y="26" width="30" height="28" rx="6" fill="#7C6CF0"/><text x="87" y="45" class="ob-h" text-anchor="middle">H</text>
        <rect x="118" y="61" width="30" height="28" rx="6" fill="#16A34A"/><text x="133" y="80" class="ob-h" text-anchor="middle">X</text>
        <rect x="164" y="96" width="30" height="28" rx="6" fill="#7C6CF0"/><text x="179" y="115" class="ob-h" text-anchor="middle">H</text>
        <!-- C-NOT 规范画法：control=实心圆点（上线），target=十字+圆圈（下线） -->
        <circle cx="212" cy="40" r="6" fill="#E5484D"/>
        <line x1="212" y1="46" x2="212" y2="68" stroke="#E5484D" stroke-width="2.2"/>
        <circle cx="212" cy="75" r="8" fill="none" stroke="#E5484D" stroke-width="2.2"/>
        <line x1="204" y1="75" x2="220" y2="75" stroke="#E5484D" stroke-width="2.2"/>
        <line x1="212" y1="68" x2="212" y2="82" stroke="#E5484D" stroke-width="2.2"/>
        <text x="20" y="136" class="ob-tag">C-NOT：两个比特连起来，按乐谱同步行动</text>
      </svg>`,
      text: `H 门只是最基础的门之一，工具库里还有十几种单比特门。两个比特之间也可以加门，比如 C-NOT 门。这样很多比特就能连成一个整体，按电路的乐谱同步行动。整体性和叠加，正是量子可能比经典计算更快的关键。`
    },
    {
      title: "纠缠：两双袜子",
      subtitle: "看到一只脚是红的，另一只肯定也是红的",
      svg: `<svg class="ob-svg" viewBox="0 0 260 150">
        <g transform="translate(30,14) scale(2)">
          <path d="M6 2h12v7.5c0 2.6-1.1 4.7-2.9 6.2L12 18.6l-3.1-2.9C7.1 14.2 6 12.1 6 9.5V2z" fill="#DC2626"/>
          <path d="M6 2h12v2.8H6z" fill="#FECACA"/>
          <path d="M6 7h12" stroke="#FECACA" stroke-opacity=".8" stroke-width="1.1"/>
        </g>
        <g transform="translate(166,14) scale(2)">
          <path d="M6 2h12v7.5c0 2.6-1.1 4.7-2.9 6.2L12 18.6l-3.1-2.9C7.1 14.2 6 12.1 6 9.5V2z" fill="#DC2626"/>
          <path d="M6 2h12v2.8H6z" fill="#FECACA"/>
          <path d="M6 7h12" stroke="#FECACA" stroke-opacity=".8" stroke-width="1.1"/>
        </g>
        <g transform="translate(30,80) scale(2)">
          <path d="M6 2h12v7.5c0 2.6-1.1 4.7-2.9 6.2L12 18.6l-3.1-2.9C7.1 14.2 6 12.1 6 9.5V2z" fill="#16A34A"/>
          <path d="M6 2h12v2.8H6z" fill="#BBF7D0"/>
          <path d="M6 7h12" stroke="#BBF7D0" stroke-opacity=".8" stroke-width="1.1"/>
        </g>
        <g transform="translate(166,80) scale(2)">
          <path d="M6 2h12v7.5c0 2.6-1.1 4.7-2.9 6.2L12 18.6l-3.1-2.9C7.1 14.2 6 12.1 6 9.5V2z" fill="#16A34A"/>
          <path d="M6 2h12v2.8H6z" fill="#BBF7D0"/>
          <path d="M6 7h12" stroke="#BBF7D0" stroke-opacity=".8" stroke-width="1.1"/>
        </g>
        <line x1="76" y1="38" x2="166" y2="38" stroke="#E5484D" stroke-width="2" stroke-dasharray="6 5" opacity=".8"/>
        <line x1="76" y1="104" x2="166" y2="104" stroke="#16A34A" stroke-width="2" stroke-dasharray="6 5" opacity=".8"/>
        <text x="130" y="60" class="ob-tag" text-anchor="middle">一双红，一双绿</text>
        <text x="130" y="74" class="ob-tag" text-anchor="middle">你总穿同色 → 见一知二</text>
        <text x="130" y="132" class="ob-tag" text-anchor="middle">两比特纠缠：要么一起朝上，要么一起朝下</text>
      </svg>`,
      text: `两个量子比特可以纠缠在一起。比如其中一种贝尔态：两个箭头要么一起朝上，要么一起朝下，但谁也不知道是哪种。好比两双袜子，一双红一双绿，你总穿同色。看到一只脚是红的，另一只肯定也是红的。`
    },
    {
      title: "量子算法：更强的配方",
      subtitle: "纠缠 + 叠加，经典算不动的任务也能拿下",
      svg: `<svg class="ob-svg" viewBox="0 0 260 150">
        <path d="M20 40 q 10 -8 20 0 t 20 0 t 20 0" fill="none" stroke="#7C6CF0" stroke-width="2.4"/>
        <path d="M20 65 q 10 -8 20 0 t 20 0 t 20 0" fill="none" stroke="#16A34A" stroke-width="2.4"/>
        <path d="M20 90 q 10 -8 20 0 t 20 0 t 20 0" fill="none" stroke="#FFB020" stroke-width="2.4"/>
        <rect x="118" y="30" width="26" height="24" rx="5" fill="#7C6CF0"/><text x="127" y="47" class="ob-h">H</text>
        <rect x="150" y="55" width="26" height="24" rx="5" fill="#16A34A"/><text x="159" y="72" class="ob-h">X</text>
        <rect x="182" y="80" width="26" height="24" rx="5" fill="#FFB020"/><text x="191" y="97" class="ob-h">Z</text>
        <g transform="translate(18,-22)">
          <rect x="196" y="52" width="44" height="46" rx="7" fill="#E5484D"/>
          <path d="M218 52 v-10 a 10 10 0 0 1 0 -14" fill="none" stroke="#E5484D" stroke-width="4" stroke-linecap="round"/>
          <path d="M208 36 l 10 -8 8 8 8 -8" fill="none" stroke="#FFD84D" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M210 80 l 6 6 12 -12" fill="none" stroke="#FFD84D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
        <text x="20" y="132" class="ob-tag">量子门组成算法（如肖尔），能解开经典解不开的锁</text>
      </svg>`,
      text: `借助纠缠和叠加，量子门能组成强大的量子算法，比如肖尔算法，可以快速破解现在银行常用的 RSA 密码。很多经典计算机干不动的任务，量子计算机有希望拿下。`
    },
    {
      title: "电路 = 配方",
      subtitle: "三步走：选 → 看讲解 → 跑实验",
      svg: `<svg class="ob-svg" viewBox="0 0 260 140">
        <rect x="18" y="50" width="60" height="44" rx="9" fill="#7C6CF0"/><text x="48" y="78" class="ob-step" text-anchor="middle">1 选电路</text>
        <path d="M84 72 h 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M92 66 l 8 6 -8 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="102" y="50" width="60" height="44" rx="9" fill="#16A34A"/><text x="132" y="78" class="ob-step" text-anchor="middle">2 看讲解</text>
        <path d="M168 72 h 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M176 66 l 8 6 -8 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="186" y="50" width="60" height="44" rx="9" fill="#E5484D"/><text x="216" y="78" class="ob-step" text-anchor="middle">3 运行</text>
        <text x="18" y="30" class="ob-tag">电路 = 门按顺序排好，像菜谱一步步操作</text>
      </svg>`,
      text: `一个电路就是一份配方。三步走：选电路、看讲解、跑实验。电路库里每个配方都配了大白话逐门讲解和运行结果。看不懂的概念，点一下就有小窗解释。`
    },
    {
      title: "说人话，AI 帮你搭",
      subtitle: "一句话生成电路",
      svg: `<svg class="ob-svg" viewBox="0 0 260 140">
        <rect x="10" y="10" width="240" height="120" rx="12" fill="none" stroke="currentColor" stroke-width="1.5"/>
        <rect x="26" y="24" width="172" height="30" rx="8" fill="#7C6CF0" opacity=".15"/>
        <text x="36" y="44" class="ob-chat">生成一个贝尔态并进行测量</text>
        <rect x="84" y="66" width="150" height="30" rx="8" fill="#16A34A" opacity=".15"/>
        <text x="94" y="86" class="ob-chat">已生成电路，自检通过 ✓</text>
        <rect x="26" y="106" width="208" height="16" rx="8" fill="var(--primary)" opacity=".25"/>
        <text x="36" y="118" class="ob-tag">在右下对话框输入 → 电路自动搭好</text>
      </svg>`,
      text: `不想一个个拖门？直接在右下角对话框说人话：「生成一个贝尔态并测量」。AI 会帮你搭好电路、自动检查，还用通俗语言逐门讲给你听。`
    },
    {
      title: "准备好了吗？",
      subtitle: "去设置看一眼，然后开始搭电路",
      svg: `<svg class="ob-svg" viewBox="0 0 260 120">
        <circle cx="130" cy="52" r="42" fill="#7C6CF0" opacity=".15" stroke="#7C6CF0" stroke-width="2"/>
        <path d="M112 52 l 12 12 l 26 -26" fill="none" stroke="#16A34A" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        <text x="130" y="114" class="ob-tag" text-anchor="middle">点「开始使用」→ 进设置，不想看引导就在这里关掉</text>
      </svg>`,
      text: `想关掉引导，点「开始使用」进设置，取消「新手引导」勾选就行；关掉后，首页会变成三台量子真机的在线驾驶舱。准备好了就开始吧！`
    }
  ];

  function render(container, opts) {
    container.innerHTML = `
      <div class="home-guide">
        <div class="ob-card" role="dialog" aria-label="新手引导">
          <div class="ob-svg-wrap"></div>
          <h2 class="ob-title"></h2>
          <p class="ob-subtitle"></p>
          <p class="ob-text"></p>
          <div class="ob-dots"></div>
          <div class="ob-nav">
            <button class="ob-skip" id="ob-skip" type="button">跳过引导</button>
            <div class="ob-nav-btns">
              <button class="btn" id="ob-prev" type="button">上一步</button>
              <button class="btn primary" id="ob-next" type="button">下一步</button>
            </div>
          </div>
        </div>
      </div>`;

    let idx = 0;
    const card = container.querySelector(".ob-card");
    const elSvg = card.querySelector(".ob-svg-wrap");
    const elTitle = card.querySelector(".ob-title");
    const elSub = card.querySelector(".ob-subtitle");
    const elText = card.querySelector(".ob-text");
    const elDots = card.querySelector(".ob-dots");
    const btnPrev = card.querySelector("#ob-prev");
    const btnNext = card.querySelector("#ob-next");
    const btnSkip = card.querySelector("#ob-skip");

    function render() {
      const p = PAGES[idx];
      elSvg.innerHTML = p.svg;
      elTitle.textContent = p.title;
      elSub.textContent = p.subtitle;
      elText.innerHTML = p.text;
      elDots.innerHTML = PAGES.map((_, i) =>
        `<span class="ob-dot${i === idx ? " active" : ""}"></span>`).join("");
      btnPrev.disabled = idx === 0;
      btnNext.textContent = idx === PAGES.length - 1 ? "开始使用" : "下一步";
    }
    function finish() {
      document.removeEventListener("keydown", onKey);
      container.innerHTML = "";
      if (opts && typeof opts.onFinish === "function") opts.onFinish();
    }
    function go(i) {
      idx = Math.max(0, Math.min(PAGES.length - 1, i));
      render();
    }
    function onKey(e) {
      if (e.key === "ArrowLeft") go(idx - 1);
      if (e.key === "ArrowRight") go(idx + 1);
      if (e.key === "Enter" && idx === PAGES.length - 1) finish();
    }

    btnNext.addEventListener("click", () => (idx === PAGES.length - 1 ? finish() : go(idx + 1)));
    btnPrev.addEventListener("click", () => go(idx - 1));
    btnSkip.addEventListener("click", finish);
    document.addEventListener("keydown", onKey);

    render();
  }

  window.Onboarding = { render };
})();
