/* gates.js — 12 个量子门的标准 SVG 图标
 *
 * 设计约定（国际通行量子门符号）：
 *   - 单比特门：方框内文字（H/X/S/T/...），参数门标注 θ
 *   - 控制门：控制点 ● —— 目标 ⊕ 或方框
 *   - SWAP：× —— ×
 *   - CCX：双控制点 ●● —— ⊕
 *
 * 每个门是独立函数，返回 SVG 字符串。可传 color 着色。
 * 尺寸约定：单比特门 40x40，多比特门用 wireGap 间距横向扩展。
 */

const GATE_SVG = {
  /* 单比特门族：方框 + 文字 */
  _box(name, color = "#2563eb") {
    return `<rect x="4" y="8" width="32" height="24" rx="4" fill="#ffffff" stroke="${color}" stroke-width="2"/>
      <text x="20" y="25" text-anchor="middle" font-size="13" font-family="monospace" fill="${color}">${name}</text>`;
  },

  h()  { return GATE_SVG._box("H"); },
  x()  { return GATE_SVG._box("X"); },
  s()  { return GATE_SVG._box("S"); },
  sdg() { return GATE_SVG._box("S†"); },
  t()  { return GATE_SVG._box("T"); },
  tdg() { return GATE_SVG._box("T†"); },

  /* 参数门：方框 + θ */
  rz(theta = "θ") {
    return `<rect x="4" y="8" width="32" height="24" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
      <text x="20" y="22" text-anchor="middle" font-size="11" font-family="monospace" fill="#2563eb">RZ</text>
      <text x="20" y="33" text-anchor="middle" font-size="8" fill="#6b7280">${theta}</text>`;
  },
  ry(theta = "θ") {
    return `<rect x="4" y="8" width="32" height="24" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
      <text x="20" y="22" text-anchor="middle" font-size="11" font-family="monospace" fill="#2563eb">RY</text>
      <text x="20" y="33" text-anchor="middle" font-size="8" fill="#6b7280">${theta}</text>`;
  },

  /* 双比特门 */
  cx() {
    return `<circle cx="12" cy="20" r="4" fill="#dc2626"/>
      <circle cx="32" cy="20" r="6" fill="none" stroke="#dc2626" stroke-width="2"/>
      <line x1="12" y1="20" x2="32" y2="20" stroke="#dc2626" stroke-width="2"/>
      <line x1="30" y1="18" x2="34" y2="22" stroke="#dc2626" stroke-width="2"/>
      <line x1="34" y1="18" x2="30" y2="22" stroke="#dc2626" stroke-width="2"/>`;
  },
  cu1(theta = "θ") {
    return `<circle cx="12" cy="20" r="4" fill="#2563eb"/>
      <line x1="12" y1="20" x2="32" y2="20" stroke="#2563eb" stroke-width="2"/>
      <rect x="22" y="8" width="20" height="24" rx="4" fill="#ffffff" stroke="#2563eb" stroke-width="2"/>
      <text x="32" y="22" text-anchor="middle" font-size="9" font-family="monospace" fill="#2563eb">U1</text>
      <text x="32" y="31" text-anchor="middle" font-size="7" fill="#6b7280">${theta}</text>`;
  },
  swap() {
    return `<line x1="8" y1="14" x2="28" y2="26" stroke="#16a34a" stroke-width="2.5"/>
      <line x1="28" y1="14" x2="8" y2="26" stroke="#16a34a" stroke-width="2.5"/>`;
  },

  /* 三比特门：CCX（Toffoli）*/
  ccx() {
    return `<circle cx="6" cy="20" r="4" fill="#dc2626"/>
      <circle cx="20" cy="20" r="4" fill="#dc2626"/>
      <line x1="6" y1="20" x2="20" y2="20" stroke="#dc2626" stroke-width="2"/>
      <line x1="20" y1="20" x2="38" y2="20" stroke="#dc2626" stroke-width="2"/>
      <circle cx="38" cy="20" r="6" fill="none" stroke="#dc2626" stroke-width="2"/>
      <line x1="36" y1="18" x2="40" y2="22" stroke="#dc2626" stroke-width="2"/>
      <line x1="40" y1="18" x2="36" y2="22" stroke="#dc2626" stroke-width="2"/>`;
  },

  /* 查询用：返回门的中文名 */
  _names: {
    h: "Hadamard", x: "X (Pauli-X)", s: "S 相位", sdg: "S† 相位",
    t: "T 相位", tdg: "T† 相位", rz: "RZ 旋转", ry: "RY 旋转",
    cx: "CNOT 受控非", cu1: "CU1 受控相位", swap: "SWAP 交换", ccx: "CCX (Toffoli)"
  },

  name(gate) { return GATE_SVG._names[gate] || gate; },

  /* 全部 12 门 ID */
  all() { return ["h", "x", "s", "sdg", "t", "tdg", "rz", "ry", "cx", "cu1", "swap", "ccx"]; }
};
