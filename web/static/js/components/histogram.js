/* components/histogram.js — 统一直方图组件 v3（对齐 Qiskit plot_histogram 标准）
 *
 * 业界标准（IBM Quantum / Qiskit plot_histogram）：
 *   - X 轴 = 测量位串（每个位串一根柱），如 |0>, |1> 或 00,01,10,11
 *   - Y 轴 = 概率 0~1（固定刻度）
 *   - 多数据对比（实测/理论）= 同一位串处柱子并排，颜色+图例区分
 *   - 多比特时 number_to_keep：只显示前 N 个位串，其余合并为 rest 柱（解决放不下）
 *   - 柱顶标签 = 概率值（bar_labels）
 *
 * 用法：
 *   const h = Histogram.create(container, { title, mini });
 *   h.setData({
 *     keys: ["|0>","|1>"],          // 位串
 *     series: [                     // 并排系列
 *       { name: "实测", counts: [2486,2514], color: "#2563eb" },
 *       { name: "理论", counts: [2500,2500], color: "rgba(148,163,184,.5)" },
 *     ],
 *     shots: 5000,                  // 用于归一化
 *     maxKeys: 8,                   // 多比特：最多显示 N 个位串，其余合并 rest
 *     title,
 *   });
 */

const Histogram = (() => {
  function create(container, opts = {}) {
  const chart = echarts.init(container);
  const mini = opts.mini || false;
  const C = Colors || { theory: "#16a34a", primary: "#2563eb" };

    function setData(d) {
      const { keys, series, shots, title, maxKeys } = d;
      const total = shots || (series[0] ? series[0].counts.reduce((a, b) => a + b, 0) : 1) || 1;

      let dispKeys = keys;
      let rest = null;  // {name: counts} 合并列

      // 多比特：超过 maxKeys 时截断 + rest 合并（Qiskit number_to_keep 标准）
      if (maxKeys && keys.length > maxKeys) {
        dispKeys = keys.slice(0, maxKeys);
        rest = {};
        series.forEach(s => {
          rest[s.name] = s.counts.slice(maxKeys).reduce((a, b) => a + b, 0);
        });
      }

      const dataSeries = series.map(s => ({
        name: s.name,
        type: "bar",
        barWidth: mini ? Math.min(20, 60 / series.length) : Math.min(40, 80 / series.length),
        data: dispKeys.map((k, i) => ({
          value: +(s.counts[i] / total).toFixed(3),
          itemStyle: { color: s.color },
        })).concat(rest && rest[s.name] ? [{ value: +(rest[s.name] / total).toFixed(3),
          itemStyle: { color: s.color }, name: "rest" }] : []),
        label: { show: !mini, position: "top", fontSize: 10, formatter: p => (p.value * 100).toFixed(0) + "%" },
      }));

      const opt = {
        title: title ? { text: title, left: "center", textStyle: { fontSize: mini ? 10 : 13 } } : undefined,
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: params => {
            let s = `<b>${params[0].axisValue}</b><br/>`;
            params.forEach(p => { s += `${p.marker}${p.seriesName}: <b>${(p.value * 100).toFixed(1)}%</b><br/>`; });
            return s;
          },
        },
        legend: series.length > 1 ? { data: series.map(s => s.name), bottom: 0, textStyle: { fontSize: mini ? 8 : 12 } } : undefined,
        grid: mini ? { left: 34, right: 8, top: 26, bottom: 20 }
                    : { left: 50, right: 15, top: 40, bottom: 34 },
        xAxis: { type: "category", data: dispKeys.concat(rest ? ["rest"] : []), axisLabel: { fontSize: mini ? 8 : 12, rotate: dispKeys.length > 6 ? 45 : 0 } },
        yAxis: { type: "value", name: "概率", min: 0, max: 1, axisLabel: { fontSize: mini ? 8 : 11 } },
        series: dataSeries,
      };
      chart.setOption(opt, true);
    }

    return {
      setData,
      resize: () => chart.resize(),
      dispose: () => chart.dispose(),
      getChart: () => chart,
    };
  }

  return { create };
})();
