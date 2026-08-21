/* components/measure.js — 统一测量组件（MeasurePanel）v2
 *
 * 设计原则（用户定）：
 *   1. 没有"单次测量"——单次随机对教学无意义且误导
 *   2. 累积式（费曼单光子散射）：每点一次测量，实时直方图更新 → 分布逐渐收敛
 *   3. 标准 5000 次：渐进式实时渲染（分批 setTimeout，看收敛过程）
 *   4. 切换门/滑块后 reset() 重置统计
 *   5. 统一用 Histogram 画直方图（数字太抽象，直方图才是标准件输出）
 *
 * 用法：
 *   const m = MeasurePanel.create({
 *     container,            // DOM 容器（直方图挂这里）
 *     getProbability,       // () => P(|0⟩) 当前态概率，由宿主提供
 *     labels: ["|0>","|1>"],// 输出标签
 *     theory,               // () => [p0, p1] 理论分布（动态获取）或 null
 *     title,                // 标题前缀
 *     onUpdate,             // (state) => {} 每次渲染后回调（可显示文字摘要）
 *   });
 *   m.accumulate(1);    // 测量（累积 1 粒子，实时直方图）
 *   m.batch(5000);      // 标准 5000 次（渐进式渲染）
 *   m.reset();          // 切换门/滑块后清零重计
 *   m.getCounts();      // {counts:[c0,c1], shots}
 */

const MeasurePanel = (() => {
  function create(opts) {
    const container = opts.container;
    const getProb = opts.getProbability;   // () => P(|0>)
    const labels = opts.labels || ["|0>", "|1>"];
    const theoryFn = opts.theory || null;  // () => [p0, p1] 或 null
    const title = opts.title || "测量结果";
    const onUpdate = opts.onUpdate || null;
    // 惰性初始化：首次渲染时才 create（避免容器隐藏时 echarts init 宽度=0 画不出）
    let hist = null;
    function ensureHist() {
      if (!hist) hist = Histogram.create(container, { mini: opts.mini || false });
      return hist;
    }

    const counts = [0, 0];   // [c0, c1]
    let shots = 0;
    let running = false;     // batch 渐进渲染中

    function sample() {
      const p0 = getProb();
      return Math.random() < p0 ? 0 : 1;
    }

    // 渲染直方图（Qiskit 标准：位串柱 + 并排系列；实测/理论）
    function render(sub) {
      const theo = theoryFn ? theoryFn() : null;
      const series = [{
        name: "实测", counts: [counts[0], counts[1]], color: "#2563eb",
      }];
      if (theo) {
        series.push({
          name: "理论", counts: [theo[0] * shots, theo[1] * shots],
          color: Colors.theory,
        });
      }
      const titleTxt = `${title} · ${sub}` + (theo ? ` · 理论 P(|0⟩)=${(theo[0] * 100).toFixed(1)}%` : "");
      ensureHist().setData({ keys: labels, series, shots, title: titleTxt, maxKeys: opts.maxKeys });
      if (onUpdate) onUpdate({ counts: [counts[0], counts[1]], shots });
    }

    // 累积式：测 n 次（默认 1），实时直方图
    function accumulate(n = 1) {
      for (let i = 0; i < n; i++) {
        const idx = sample();
        counts[idx]++;
        shots++;
      }
      render(`累积 ${shots} 次`);
    }

    // 标准批量：渐进式（每批 250 次渲染一帧，总 5000 → 20 帧）
    function batch(n = 5000) {
      if (running) return;   // 进行中忽略重复点击
      const batchSize = 125;   // 每帧 125 次（慢一倍，让用户看清收敛过程）
      const totalBatches = Math.ceil(n / batchSize);
      let done = 0;
      running = true;
      function step() {
        const target = Math.min(done + batchSize, n);
        for (let i = done; i < target; i++) {
          const idx = sample();
          counts[idx]++;
          shots++;
        }
        done = target;
        render(`测量中 ${done} / ${n}`);
        if (done < n) {
          setTimeout(step, 50);   // 每帧 50ms，总耗时约 2s（5000/125 × 50ms）
        } else {
          running = false;
          render(`完成 ${n} 次`);
        }
      }
      step();
    }

    // 重置（切换门/滑块后调用）
    function reset() {
      counts[0] = counts[1] = 0;
      shots = 0;
      render("已重置");
    }

    return {
      accumulate, batch, reset,
      getCounts: () => ({ counts: [counts[0], counts[1]], shots }),
      getRatio: () => shots ? counts[0] / shots : null,
      isRunning: () => running,
    };
  }

  return { create };
})();
