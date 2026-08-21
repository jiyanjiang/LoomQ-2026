/* colors.js — 全站统一色板（单一来源，禁止在组件里硬编码其他色号）
 *
 * 语义约定：
 *   实测/主操作   → 蓝 #2563eb
 *   理论/基准/成功 → 绿 #16a34a
 *   警告/错误     → 红 #dc2626
 *   橙色（次要）  → 橙 #f59e0b（如 |1⟩ 柱）
 *   中性/次要     → 灰 #94a3b8
 *   袜子（量子比特）→ 红袜=--sock-red / 绿袜=--sock-green（CSS 变量，随主题变）
 *
 * 注意：袜子颜色由 CSS 变量 --sock-red/--sock-green 驱动（见 style.css 各主题），
 * 以便随 theme 切换。本文件 JS 常量仅供需要 JS 侧取值时使用。
 */
const Colors = {
  primary: "#2563eb",     // 实测/主操作（蓝）
  theory: "#16a34a",      // 理论/基准/成功（绿）——统一为全站绿色
  success: "#16a34a",     // 成功提示
  danger: "#dc2626",      // 错误
  warning: "#f59e0b",     // 次要/警告
  muted: "#94a3b8",       // 中性
  swap: "#16a34a",        // SWAP 门（绿色）
  cnot: "#dc2626",        // CNOT 控制点（红色）
  sockRed: "#dc2626",     // 袜子：红袜（与 danger 同源；CSS 变量 --sock-red 随主题覆盖）
  sockGreen: "#16a34a",   // 袜子：绿袜（与 theory 同源；CSS 变量 --sock-green 随主题覆盖）
};
