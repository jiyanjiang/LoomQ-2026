#!/usr/bin/env python3
"""LoomQ Web 内容字典（数据层）。

设计：所有面向用户的文案（12 门讲解、9 算法讲解、UI 文案、提示词片段）
统一存为结构化字典。界面从字典渲染；也可提取任意条目拼装成 LLM 提示词，
返回后再拼装回界面 —— 教育引导的灵活机制。

与 loomq_lib.circuits 对应：circuit_id 一致。
"""

# ---------------------------------------------------------------------------
# 12 门讲解（通俗版，面向新手）
# ---------------------------------------------------------------------------
GATES = {
    "x": {
        "name": "X 门", "symbol": "X",
        "plain": "拨动开关。把 |0⟩ 变成 |1⟩，|1⟩ 变成 |0⟩，像反转硬币。",
        "analogy": "翻转硬币",
        "fun_fact": "X 门在经典世界对应的就是 NOT 门——唯一的量子比特反转开关。",
    },
    "h": {
        "name": "H 门", "symbol": "H",
        "plain": "抛硬币。把确定的 |0⟩ 变成悬空态，测量 50/50。量子计算的起手式。",
        "analogy": "抛起硬币",
        "fun_fact": "H 门是'创造叠加'的门——量子比特第一次有了'不确定性'。",
    },
    "s": {
        "name": "S 门", "symbol": "S",
        "plain": "涂色（1/4 圈）。给硬币'反面'涂一种颜色。测量看不到变化，但干涉时起作用。",
        "analogy": "给反面涂色（1/4 圈）",
        "fun_fact": "S 门是 Z 门的'平方根'——涂两次 S 等于一次 Z。",
    },
    "sdg": {
        "name": "S† 门", "symbol": "S†",
        "plain": "涂色（反向 1/4 圈）。S 的反向操作，用来抵消 S。",
        "analogy": "反向涂色（-1/4 圈）",
        "fun_fact": "S 和 S† 是彼此的'撤销'按钮：S 再 S† 等于什么都没做。",
    },
    "t": {
        "name": "T 门", "symbol": "T",
        "plain": "涂色（1/8 圈）。比 S 更细的涂色。S 和 T 合起来能涂出任意颜色。",
        "analogy": "细涂色（1/8 圈）",
        "fun_fact": "S 是 T 的平方：涂两次 T 等于一次 S。",
    },
    "tdg": {
        "name": "T† 门", "symbol": "T†",
        "plain": "涂色（反向 1/8 圈）。T 的反向操作，抵消用。",
        "analogy": "反向细涂色（-1/8 圈）",
        "fun_fact": "T 和 T† 也是彼此的'撤销'按钮。",
    },
    "rz": {
        "name": "RZ(θ) 门", "symbol": "RZ",
        "plain": "任意角度旋钮。给'反面'涂上任意角度（θ）的颜色。S/T 只是它的特例。",
        "analogy": "任意角度涂色",
        "fun_fact": "S=RZ(π/2)，T=RZ(π/4)——S 和 T 都是 RZ 的特定角度。",
    },
    "ry": {
        "name": "RY(θ) 门", "symbol": "RY",
        "plain": "任意角度翻硬币。按 θ 控制硬币悬空角度：0° 不变、180° 全翻、90° 就 50/50。",
        "analogy": "任意角度翻转",
        "fun_fact": "RY(180°) 等于 X 门——翻转角度调到最大就是反转。",
    },
    "cx": {
        "name": "CX 门", "symbol": "CX",
        "plain": "联动开关。控制位是 1 才翻转目标位。制造纠缠的核心：两枚硬币从此'永远同面'。",
        "analogy": "联动开关",
        "fun_fact": "CX 是量子世界第一个'两比特'门——没有它就没有纠缠。",
    },
    "cu1": {
        "name": "CU1(θ) 门", "symbol": "CU1",
        "plain": "受控涂色。控制位是 1 才给目标位涂色。QFT 全靠它。",
        "analogy": "受控涂色",
        "fun_fact": "QFT（量子傅里叶变换）的核心零件就是 CU1 的级联。",
    },
    "swap": {
        "name": "SWAP 门", "symbol": "SWAP",
        "plain": "换座位。两枚硬币交换位置。布线常用。",
        "analogy": "交换座位",
        "fun_fact": "SWAP 可以由 3 个 CX 拼出来——两个比特交换位置。",
    },
    "ccx": {
        "name": "CCX 门", "symbol": "CCX",
        "plain": "双开关。两个控制位都是 1 才翻转目标位。有了它 + H，理论上能做任何量子计算。",
        "analogy": "双联动开关",
        "fun_fact": "CCX（Toffoli）是量子计算的'万能砖'——它和 H 门组合是通用计算基。",
    },
}

# ---------------------------------------------------------------------------
# 9 算法讲解（通俗版）
# ---------------------------------------------------------------------------
ALGORITHMS = {
    "a01_ghz3": {
        "name": "GHZ-3", "qubits": 3,
        "plain": "三枚硬币永远同面。测一个就知道另外两个。三比特纠缠的教科书案例。",
        "why": "量子纠缠的经典展示——三个比特的命运绑定在一起。",
        "result": "00...0 或 11...1 各 50%",
    },
    "a02_cat4": {
        "name": "猫态-4", "qubits": 4,
        "plain": "四枚硬币永远同面。薛定谔的猫从 1 只变 4 只。纠缠规模扩大。",
        "why": "把 GHZ 从 3 比特扩展到 4 比特，看纠缠如何'传染'。",
        "result": "0000 或 1111 各 50%",
    },
    "a03_qft4": {
        "name": "QFT-4", "qubits": 4,
        "plain": "量子版傅里叶变换。把'频率'翻译成'位置'。很多算法的地基。",
        "why": "量子傅里叶变换是 Shor 算法（破解 RSA）的核心，考的是相位转译精度。",
        "result": "均匀分布（取决于输入态）",
    },
    "a04_grover2": {
        "name": "Grover-2", "qubits": 2,
        "plain": "在 4 个抽屉里找目标。经典要找 4 次，量子 1 次就放大出答案。",
        "why": "Grover 搜索是量子加速的招牌——'放大正确答案'的直觉体验。",
        "result": "目标态高概率（一次迭代）",
    },
    "a05_teleport3": {
        "name": "隐形传态", "qubits": 3,
        "plain": "量子传真机。不传送物体，传送'状态'。用纠缠当信道。",
        "why": "量子隐形传态是量子网络的基础——'状态'可以瞬间'复制'到另一个比特。",
        "result": "多峰分布（测量决定）",
    },
    "a06_qft5": {
        "name": "QFT-5", "qubits": 5,
        "plain": "QFT 升级到 5 比特。32 个状态均匀分布，测你对大电路的转译能力。",
        "why": "从 4 比特到 5 比特，电路复杂度翻倍——验证转译器的大规模正确性。",
        "result": "32 个状态均匀",
    },
    "a07_grover3": {
        "name": "Grover-3", "qubits": 3,
        "plain": "8 个抽屉找目标。一次迭代后目标概率放大到 78%，'放大答案'的直观感受。",
        "why": "从 2 比特扩到 3 比特，8 个抽屉——Grover 的规模效应。",
        "result": "目标态约 78%",
    },
    "a08_toffoli3": {
        "name": "Toffoli-3", "qubits": 3,
        "plain": "双开关门。确定性的 111，最简单也最可靠的验证。",
        "why": "Toffoli 门是最简单的三比特确定性门——验证转译器的基础可靠性。",
        "result": "|111⟩ 100%",
    },
    "a09_wstate3": {
        "name": "W 态", "qubits": 3,
        "plain": "恰好一盏灯亮。三枚硬币恰好一枚正面，且无法拆开看。另一种纠缠，和 GHZ 不同家族。",
        "why": "W 态和 GHZ 是两种'不等价'的纠缠——丢一个比特仍保持纠缠，这是它的独特性。",
        "result": "001/010/100 各 1/3",
    },
    "a10_ghz5": {
        "name": "GHZ-5", "qubits": 5,
        "plain": "五枚硬币永远同面。从 3 比特扩到 5 比特，纠缠继续'传染'给每个新成员。",
        "why": "评测核心算法之一（QUANTUM_101 明确点名 GHZ-5）——验证大规模纠缠的转译。",
        "result": "00000/11111 各 50%",
    },
}

# ---------------------------------------------------------------------------
# UI 文案（中英双语模板）
# ---------------------------------------------------------------------------
UI = {
    "zh": {
        "app_name": "LoomQ 量子工作台",
        "tagline": "不懂量子力学，也能玩量子电路",
        "circuit_lib": "电路库",
        "documentation": "文档",
        "settings": "设置",
        "account": "账号",
        "run": "运行",
        "select_circuit": "选择一个电路",
        "custom_qasm": "或粘贴自定义 QASM",
        "dialog_placeholder": "用自然语言描述你想要的电路，例如：生成 3 比特 GHZ 态…",
        "executing": "执行中…",
        "fidelity": "保真度",
        "reference": "参考分布",
        "measured": "实测分布",
        "chat_title": "量子助手",
        "process_title": "执行过程",
    },
    "en": {
        "app_name": "LoomQ Quantum Workbench",
        "tagline": "Play with quantum circuits without a physics degree",
        "circuit_lib": "Circuit Library",
        "documentation": "Docs",
        "settings": "Settings",
        "account": "Account",
        "run": "Run",
        "select_circuit": "Select a circuit",
        "custom_qasm": "Or paste custom QASM",
        "dialog_placeholder": "Describe a circuit in plain language, e.g. make a 3-qubit GHZ state…",
        "executing": "Executing…",
        "fidelity": "Fidelity",
        "reference": "Reference",
        "measured": "Measured",
        "chat_title": "Quantum Assistant",
        "process_title": "Execution Log",
    },
}

# ---------------------------------------------------------------------------
# 课程树（互动量子教程：游戏即课程）
# ---------------------------------------------------------------------------
COURSE = [
    {
        "id": "c1_hgate",
        "num": "第 1 课",
        "title": "叠加态：H 门",
        "subtitle": "神奇的盒子（Terry Rudolph 的黑球白球方案）",
        "status": "ready",
        "desc": "把一个球丢进 H 盒子，出来一定一半黑一半白。再丢一次，它又变回原色。",
        "game": "hgate",
    },
    {
        "id": "c2_phase",
        "num": "第 2 课",
        "title": "相位：转盘实验",
        "subtitle": "用滑块看相位如何改变态",
        "status": "ready",
        "desc": "拖 θ/φ 滑块，看态矢量在布洛赫球上旋转，相位门的秘密藏在方位角里。",
        "game": "bloch",
    },
    {
        "id": "c3_entangle",
        "num": "第 3 课",
        "title": "纠缠：伯特曼的袜子",
        "subtitle": "两只袜子，永远一对（贝尔的经典比喻）",
        "status": "ready",
        "desc": "翻开一只袜子，用纠缠规则推理另一只。贝尔说：量子世界就是这样关联的。",
        "game": "socks",
    },
    {
        "id": "c4_measure",
        "num": "第 4 课",
        "title": "测量：斯特恩-盖拉赫",
        "subtitle": "让自旋决定命运（规划中）",
        "status": "planned",
        "desc": "银原子穿过磁场，随机偏转——测量坍缩的教科书实验。",
        "game": "sg",
    },
    {
        "id": "c5_algebra",
        "num": "第 5 课",
        "title": "测量代数：施温格积木",
        "subtitle": "狄拉克记号与矩阵力学的玩具版",
        "status": "ready",
        "desc": "把测量积木拼起来，看粒子能否通过——1960s 哈佛'量子玩具'，施温格测量代数的具象化。",
        "game": "schwinger",
    },
    {
        "id": "c6_algorithm",
        "num": "第 6 课",
        "title": "算法：量子大富翁",
        "subtitle": "收集门，拼算法（规划中）",
        "status": "planned",
        "desc": "投骰子走格子收集量子门，拼出算法得高分。",
        "game": "monopoly",
    },
]

# 课程跳转目标（game id → 前端处理）
COURSE_NAV = {
    "hgate": "lesson:hgate",     # 内置课程（H门游戏在教程视图内）
    "bloch": "view:bloch",       # 跳到布洛赫球视图
    "socks": "view:games",       # 量子游戏视图
    "sg": None,
    "schwinger": "view:games",   # 量子游戏视图
    "monopoly": None,
}


# ---------------------------------------------------------------------------
# 提示词片段（教育引导：讲解某门/算法时拼装发给 LLM）
# ---------------------------------------------------------------------------
PROMPT_FRAGMENTS = {
    "explain_gate": (
        "你是量子教学助手，面对完全不懂量子力学的初学者。"
        "用下面这个门的中文介绍，扩展成 3 句话以内的友好讲解，"
        "继续用'硬币'比喻，不要出现任何公式或狄拉克符号以外的术语：\n{content}"
    ),
    "explain_algo": (
        "你是量子教学助手，面对完全不懂量子力学的初学者。"
        "用下面这个算法电路的中文介绍，扩展成 5 句话以内的讲解，"
        "说清楚'它在干什么'和'为什么有意思'，不要出现任何数学公式：\n{content}"
    ),
    "generate_circuit": (
        "请生成满足以下需求的 OpenQASM 2.0 电路：\n{prompt}\n\n"
        "约束：只用 12 门白名单（h,x,s,sdg,t,tdg,rz,ry,cx,cu1,swap,ccx），"
        "必须含 qreg/creg/measure，直接输出 QASM 代码。"
    ),
}
