#!/usr/bin/env python3
"""LoomQ 量子计算词典（唯一权威源 · 9 字段统一 schema）。

设计原则：
  1. 英文名 = 唯一标识（查重键），也是规范拼写本身。
  2. 所有界面文案/文档中的术语，必须从这里读取，写作格式：
       - 中文版行文：中文(英文)，如"伯特曼的袜子（Bertlmann's socks）"
       - 英文版行文：仅英文
  3. aliases = 历史上出现过的所有错误变体（自检黑名单来源），
     出现即报错 → 杜绝"用户笔误被一直带着"。
  4. prereqs = 前置概念（须为本词典已存在的英文键），自动形成概念依赖图，
     可校验"前置存在"+"无循环依赖"。
  5. source = 来源（经典文献，指向 REFERENCES 的 key）。
  6. 审稿 = 只审本文件 + validate() 自动校验 + 可导出 Markdown/CSV。

CLI：
  python web/qc_dict.py --validate   # 词典一致性校验
  python web/qc_dict.py --md         # 导出 Markdown（审稿可读）
  python web/qc_dict.py --csv        # 导出 CSV
  python web/qc_dict.py --aliases    # 输出全部别名（自检脚本用）
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 经典文献数据库（来源：REFERENCES 的 key。先登记核心经典，待扩充）
# ---------------------------------------------------------------------------
REFERENCES = {
    "schrodinger-1935": {
        "title": "Die gegenwärtige Situation in der Quantenmechanik",
        "authors": "E. Schrödinger",
        "year": 1935,
        "venue": "Naturwissenschaften",
        "note": "薛定谔的猫思想实验、纠缠的提出（'Verschränkung'）。",
        "url": None,
    },
    "bell-1978": {
        "title": "Bertlmann's Socks and the Nature of Reality",
        "authors": "J.S. Bell",
        "year": 1978,
        "venue": "Journal de Physique Colloque C2",
        "note": "伯特曼袜子典故出处，贝尔不等式的通俗论证。",
        "url": None,
    },
    "feynman-1982": {
        "title": "Simulating Physics with Computers",
        "authors": "R.P. Feynman",
        "year": 1982,
        "venue": "International Journal of Theoretical Physics",
        "note": "提出用量子系统模拟量子系统——量子计算奠基。",
        "url": None,
    },
    "shor-1994": {
        "title": "Algorithms for Quantum Computation: Discrete Logarithms and Factoring",
        "authors": "P.W. Shor",
        "year": 1994,
        "venue": "FOCS 1994",
        "note": "Shor 算法，证明量子计算可破解 RSA。",
        "url": None,
    },
    "grover-1996": {
        "title": "A Fast Quantum Mechanical Algorithm for Database Search",
        "authors": "L.K. Grover",
        "year": 1996,
        "venue": "STOC 1996",
        "note": "Grover 算法，无序搜索的二次加速。",
        "url": None,
    },
    "schwinger-2001": {
        "title": "Quantum Mechanics: Symbolism of Atomic Measurements",
        "authors": "J. Schwinger (ed. B.-G. Englert)",
        "year": 2001,
        "venue": "Springer",
        "note": "施温格量子力学教程：以斯特恩-盖拉赫选择性测量为出发点，用测量代数推导整个量子力学。",
        "url": None,
    },
    "aspect-1982": {
        "title": "Experimental Realization of Einstein-Podolsky-Rosen-Bohm Gedankenexperiment: A New Violation of Bell's Inequalities",
        "authors": "A. Aspect, J. Dalibard, G. Roger",
        "year": 1982,
        "venue": "Physical Review Letters 49, 1804",
        "note": "首次实验确证贝尔不等式被违背，证明量子纠缠是非定域的。",
        "url": None,
    },
    "papaliolios-2018": {
        "title": "Playing with Quantum Toys: Julian Schwinger's Measurement Algebra and the Material Culture of Quantum Mechanics Pedagogy at Harvard in the 1960s",
        "authors": "J.-F. Gauvin",
        "year": 2018,
        "venue": "Physics in Perspective 20, 8-42",
        "note": "记载 Papaliolios 1960 年代哈佛为施温格测量代数课发明的 13 个'量子玩具'铝立方体教具（入藏哈佛 CHSI）。",
        "url": "https://doi.org/10.1007/s00016-018-0213-3",
    },
}


# ---------------------------------------------------------------------------
# 统一词典（键 = 英文名）
# category: tech=技术术语 / people=人名 / concept=物理概念
# ---------------------------------------------------------------------------
DICT = {
    # ================= 物理概念 =================
    "qubit": {
        "zh": "量子比特", "category": "concept", "aliases": [],
        "def_en": "The basic unit of quantum information, a two-level system (|0⟩, |1⟩) that can be in superposition.",
        "def_zh": "量子信息的基本单元，可处于 |0⟩、|1⟩ 或两者的叠加态。",
        "detail_en": "Mainstream convention: |0⟩ = |↑⟩ (spin +z, S_z eigenstate +ħ/2), |1⟩ = |↓⟩ (spin −z, −ħ/2), matching Qiskit/IBM. Measurement collapses it to |0⟩ or |1⟩ with probabilities cos²(θ/2), sin²(θ/2).",
        "detail_zh": "主流约定（与 Qiskit/IBM 一致）：|0⟩=|↑⟩（自旋 z 方向 +，S_z 本征值 +ħ/2），|1⟩=|↓⟩（自旋 z 方向 −，−ħ/2）。经典比特只能是 0 或 1；量子比特可在布洛赫球面上任意一点（θ, φ），测量时才坍缩，概率由态决定。",
        "prereqs": [], "source": None,
    },
    "superposition": {
        "zh": "叠加态", "category": "concept", "aliases": [],
        "def_en": "A qubit state that is a coherent combination of |0⟩ and |1⟩.",
        "def_zh": "量子比特同时处于 |0⟩ 和 |1⟩ 的相干组合，测量时才坍缩到其中之一。",
        "detail_en": "H gate turns |0⟩ into (|0⟩+|1⟩)/√2 (50/50). Superposition is the resource behind quantum parallelism.",
        "detail_zh": "H 门把 |0⟩ 变成 (|0⟩+|1⟩)/√2（各 50%）。叠加是量子并行的资源。",
        "prereqs": ["qubit"], "source": None,
    },
    "entanglement": {
        "zh": "纠缠", "category": "concept", "aliases": [],
        "def_en": "Correlation between two or more qubits stronger than any classical one: measuring one instantly determines the other.",
        "def_zh": "两个或多个量子比特之间的关联，测量一个瞬间确定另一个（无论距离）。",
        "detail_en": "Bell state (|00⟩+|11⟩)/√2: outcomes are always 00 or 11, never mixed. First discussed by Schrödinger (1935), formalized via Bell inequality, confirmed by Aspect 1982.",
        "detail_zh": "Bell 态 (|00⟩+|11⟩)/√2：测量结果恒为 00 或 11。薛定谔 1935 年提出，贝尔不等式形式化，Aspect 1982 实验证实。",
        "prereqs": ["qubit", "superposition"], "source": "schrodinger-1935",
    },
    "measurement-collapse": {
        "zh": "测量坍缩", "category": "concept", "aliases": [],
        "def_en": "Measurement projects a superposition onto one definite outcome; irreversible.",
        "def_zh": "测量把叠加态'落地'成确定结果，概率由态决定，坍缩后不可逆。",
        "detail_en": "Born rule: P(outcome) = |amplitude|². Repeating measurement on the same state yields a statistical distribution (counts histogram).",
        "detail_zh": "玻恩规则：P(结果) = |振幅|²。对同一态反复测量得到统计分布（counts 直方图）。",
        "prereqs": ["qubit", "superposition"], "source": None,
    },
    "non-commuting": {
        "zh": "非对易", "category": "concept", "aliases": [],
        "def_en": "Two observables A, B are non-commuting if AB ≠ BA; they cannot be simultaneously determined.",
        "def_zh": "两个可观测量 A、B 若 AB ≠ BA 则称非对易；非对易的物理量不能同时确定。",
        "detail_en": "σxσy = iσz: measuring x disturbs z. This is why particles pass through the z→x→z block sequence — the middle x measurement 'scrambles' the z result. Non-commutation is the mathematical root of quantum measurement disturbance.",
        "detail_zh": "σxσy = iσz：测 x 会扰动 z。这就是 z→x→z 积木串粒子能通过的原因——中间的 x 测量'打乱'了 z 结果。非对易是量子测量扰动的数学根源。",
        "prereqs": ["measurement-collapse"], "source": None,
    },
    "decoherence": {
        "zh": "退相干", "category": "concept", "aliases": [],
        "def_en": "Loss of coherence as the quantum system interacts with the environment; T1/T2 quantify the speed.",
        "def_zh": "量子系统与环境相互作用，叠加/纠缠逐渐'散掉'的过程，T1/T2 衡量速度。",
        "detail_en": "The main enemy of quantum computing: information decays before computation finishes. Mitigated by error correction.",
        "detail_zh": "量子计算的最大敌人——信息还没算完就丢了，靠纠错缓解。",
        "prereqs": ["qubit", "superposition"], "source": None,
    },
    "quantum-error-correction": {
        "zh": "量子纠错", "category": "concept", "aliases": [],
        "def_en": "Encoding one logical qubit into many physical qubits to detect and fix errors in real time.",
        "def_zh": "用多个物理比特编码一个逻辑比特，实时探测并修复错误。",
        "detail_en": "Surface code and LDPC are mainstream. Needed because single-qubit fidelity can never be 100%.",
        "detail_zh": "表面码/LDPC 是主流方案。因为单比特保真度不可能 100%，必须靠纠错——这是量子计算走向实用的关键。",
        "prereqs": ["qubit", "decoherence"], "source": None,
    },
    "surface-code": {
        "zh": "表面码", "category": "concept", "aliases": [],
        "def_en": "A 2D lattice QEC code; syndrome measurement detects and corrects errors.",
        "def_zh": "一种 2D 格点量子纠错码，通过稳定性子测量探测并修复错误。",
        "detail_en": "Realized on grid topology: data qubits + ancilla qubits. Threshold ~1% gate error.",
        "detail_zh": "在棋盘拓扑上实现：数据比特 + 辅助比特。阈值约 1% 门错误率。",
        "prereqs": ["quantum-error-correction", "entanglement"], "source": None,
    },
    "bell-state": {
        "zh": "Bell 态", "category": "concept", "aliases": [],
        "def_en": "Maximally entangled two-qubit states, e.g. (|00⟩+|11⟩)/√2.",
        "def_zh": "最大纠缠的双比特态，如 (|00⟩+|11⟩)/√2。",
        "detail_en": "Four Bell states form an orthonormal basis of 2-qubit space: (|00⟩+|11⟩)/√2, (|00⟩−|11⟩)/√2, (|01⟩+|10⟩)/√2, (|01⟩−|10⟩)/√2. Prepared by H + CNOT. The (|01⟩+|10⟩) form is the 'opposite-sock' entanglement.",
        "detail_zh": "四个 Bell 态构成 2 比特空间的正交基：(|00⟩+|11⟩)/√2、(|00⟩−|11⟩)/√2、(|01⟩+|10⟩)/√2、(|01⟩−|10⟩)/√2，用 H + CNOT 制备。其中 (|01⟩+|10⟩) 即'异面袜子'式纠缠。",
        "prereqs": ["entanglement", "qubit"], "source": "bell-1978",
    },
    # ================= 技术术语 =================
    "T1": {
        "zh": "T1（能量弛豫时间）", "category": "tech", "aliases": [],
        "def_en": "Time for a qubit in |1⟩ to decay to |0⟩; longer is better.",
        "def_zh": "量子比特从 |1⟩ 自发衰落到 |0⟩ 的时间。越长越好。单位微秒(µs)。",
        "detail_en": "T1 short = qubit 'leaks', information lost before it is read. Standard spec in backend.properties().",
        "detail_zh": "T1 短 = 量子比特'漏电'快，信息在读出前就丢了。IBM backend.properties() 标准字段。",
        "prereqs": ["qubit", "decoherence"], "source": None,
    },
    "T2": {
        "zh": "T2（相位相干时间）", "category": "tech", "aliases": [],
        "def_en": "Phase coherence time; reflects how long superposition survives.",
        "def_zh": "量子比特相位保持相干的时间。比 T1 更能反映'叠加态能维持多久'。单位微秒(µs)。",
        "detail_en": "T2 short = superposition 'dissolves', the basis of quantum advantage (interference) is gone.",
        "detail_zh": "T2 短 = 叠加态'散掉'，量子优势的根基（叠加/干涉）就没了。",
        "prereqs": ["qubit", "decoherence"], "source": None,
    },
    "gate-error": {
        "zh": "门错误率", "category": "tech", "aliases": [],
        "def_en": "Probability a quantum gate fails; fidelity = 1 - gate_error.",
        "def_zh": "执行一个量子门的出错概率（gate_error）。保真度 = 1 - gate_error。",
        "detail_en": "Each gate has small error; deeper circuits accumulate fatal errors. Depolarizing model adds random Pauli error with prob p.",
        "detail_zh": "每个门都有小概率出错，线路越深（门越多）累积错误越致命。退极化模型以概率 p 加随机泡利错误。",
        "prereqs": ["decoherence"], "source": None,
    },
    "readout-error": {
        "zh": "测量错误率", "category": "tech", "aliases": [],
        "def_en": "Probability the measurement result is read wrongly.",
        "def_zh": "读测量结果时出错的概率。如 1% = 100 次测量有 1 次把 0 读成 1。",
        "detail_en": "Readout is imperfect; terminal errors directly corrupt the final answer.",
        "detail_zh": "测量本身不完美，末端的错误直接影响最终答案。",
        "prereqs": ["measurement-collapse"], "source": None,
    },
    "depolarizing-noise": {
        "zh": "退极化噪声", "category": "tech", "aliases": [],
        "def_en": "With probability p the qubit is 'washed' toward a random state (random X/Y/Z error).",
        "def_zh": "以一定概率把量子比特'洗白'成随机态（等概率 X/Y/Z 错误）。最常用的噪声模型。",
        "detail_en": "Engineering simplification: gate errors become random Pauli errors, easy to simulate on statevector.",
        "detail_zh": "工程上把门错误简化为'随机泡利错误'，便于态矢量模拟。",
        "prereqs": ["gate-error"], "source": None,
    },
    "coupling-map": {
        "zh": "耦合映射（拓扑）", "category": "tech", "aliases": [],
        "def_en": "Describes which qubit pairs can directly perform two-qubit gates.",
        "def_zh": "描述哪些量子比特对能直接做双比特门。链式=相邻，网格=四邻。",
        "detail_en": "Topology determines routing: non-adjacent qubits need SWAP gates, adding errors.",
        "detail_zh": "拓扑决定布线——不直接耦合的比特要插 SWAP 门搬过去，增加错误。",
        "prereqs": ["qubit", "gate-error"], "source": None,
    },
    "fidelity": {
        "zh": "保真度（Hellinger）", "category": "tech", "aliases": [],
        "def_en": "Agreement between measured and theoretical distribution (0~1); ≥0.97 counts as correct.",
        "def_zh": "实测分布与理论分布的重合度（0~1）。0.97 以上视为正确。",
        "detail_en": "We use Hellinger distance to judge whether 'this machine running this circuit' is trustworthy.",
        "detail_zh": "用于判断'这台机器跑这个电路是否可信'的指标。",
        "prereqs": ["measurement-collapse"], "source": None,
    },
    "hadamard-gate": {
        "zh": "H 门（Hadamard）", "category": "tech", "aliases": [],
        "def_en": "Single-qubit gate creating superposition: |0⟩→(|0⟩+|1⟩)/√2; H²=I.",
        "def_zh": "制造叠加的单比特门：|0⟩→(|0⟩+|1⟩)/√2；H²=I（两次 H 等于没操作）。",
        "detail_en": "The 'entry gate' of quantum circuits. In Terry Rudolph's scheme it's the 'PETE box'.",
        "detail_zh": "量子电路的'起手式'。Terry Rudolph 教学法里称'PETE 盒'。",
        "prereqs": ["qubit", "superposition"], "source": None,
    },
    "SWAP": {
        "zh": "SWAP 门", "category": "tech", "aliases": [],
        "def_en": "Two-qubit gate exchanging the states of two qubits.",
        "def_zh": "交换两个量子比特状态的双比特门。",
        "detail_en": "Used for routing on limited topologies (non-adjacent qubits).",
        "detail_zh": "用于受限拓扑下的布线（非相邻比特）。",
        "prereqs": ["qubit", "coupling-map"], "source": None,
    },
    "Toffoli": {
        "zh": "Toffoli 门（CCX）", "category": "tech", "aliases": [],
        "def_en": "Three-qubit gate: flips target only if both controls are |1⟩.",
        "def_zh": "三比特门：两个控制位都是 |1⟩ 才翻转目标位。",
        "detail_en": "Universality: H + Toffoli is universal for quantum computation.",
        "detail_zh": "通用性：H + Toffoli 对量子计算是通用的。",
        "prereqs": ["qubit"], "source": None,
    },
    "QFT": {
        "zh": "量子傅里叶变换", "category": "tech", "aliases": [],
        "def_en": "Quantum version of the discrete Fourier transform; maps frequency to position.",
        "def_zh": "离散傅里叶变换的量子版：把'频率'翻译成'位置'。",
        "detail_en": "Foundation of many algorithms (Shor, phase estimation). Built from H + controlled-phase (CU1) + SWAP.",
        "detail_zh": "很多算法（Shor、相位估计）的地基，由 H + 受控相位(CU1) + SWAP 构成。",
        "prereqs": ["superposition", "entanglement"], "source": None,
    },
    "Grover-algorithm": {
        "zh": "Grover 算法", "category": "tech", "aliases": [],
        "def_en": "Quantum search: finds a marked item among N with O(√N) queries.",
        "def_zh": "量子搜索：在 N 个条目中找标记项，仅需 O(√N) 次查询（经典 O(N)）。",
        "detail_en": "Oracle + diffusion (amplitude amplification). Each iteration boosts target probability.",
        "detail_zh": "Oracle + 扩散算子（振幅放大）。每次迭代把目标概率放大。",
        "prereqs": ["superposition", "Toffoli"], "source": "grover-1996",
    },
    "teleportation": {
        "zh": "隐形传态", "category": "tech", "aliases": [],
        "def_en": "Transferring an unknown quantum state using entanglement + classical communication.",
        "def_zh": "用纠缠 + 经典通信传送未知量子态（不传送物体）。",
        "detail_en": "Alice-Bob protocol: Bell pair + Bell measurement + classical corrections.",
        "detail_zh": "Alice-Bob 协议：Bell 对 + Bell 测量 + 经典校正。",
        "prereqs": ["entanglement", "bell-state"], "source": None,
    },
    # ================= 人名 =================
    "Richard Feynman": {
        "zh": "费曼", "category": "people", "aliases": [],
        "def_en": "Proposed simulating quantum systems with quantum computers (1982).",
        "def_zh": "提出'用量子计算机模拟量子系统'（1982），量子计算之父。",
        "detail_en": "Nobel laureate; the single-photon double-slit experiment metaphor is the basis of our cumulative measurement.",
        "detail_zh": "诺奖得主；其单光子双缝实验比喻是我们'累积式测量'设计的基础。",
        "prereqs": ["superposition"], "source": "feynman-1982",
    },
    "Peter Shor": {
        "zh": "Shor", "category": "people", "aliases": [],
        "def_en": "Proposed quantum factoring algorithm (1994), breaking RSA in principle.",
        "def_zh": "提出量子因数分解算法（1994），证明量子计算能破解 RSA。",
        "detail_en": "Shor's algorithm combines QFT with modular exponentiation.",
        "detail_zh": "Shor 算法 = QFT + 模幂运算。",
        "prereqs": ["QFT"], "source": "shor-1994",
    },
    "Lov Grover": {
        "zh": "Grover", "category": "people", "aliases": [],
        "def_en": "Proposed quantum search algorithm (1996) with quadratic speedup.",
        "def_zh": "提出量子搜索算法（1996），二次加速。",
        "detail_en": "Named after Grover's algorithm.",
        "detail_zh": "Grover 算法以其命名。",
        "prereqs": ["Grover-algorithm"], "source": "grover-1996",
    },
    "John Bell": {
        "zh": "贝尔", "category": "people", "aliases": [],
        "def_en": "Derived Bell inequality; popularized entanglement via 'Bertlmann's socks'.",
        "def_zh": "提出贝尔不等式，用'伯特曼的袜子'通俗化纠缠。",
        "detail_en": "Bell's theorem rules out local hidden variables: quantum correlations cannot be explained by pre-agreed classical states (local realism), implying quantum mechanics is inherently nonlocal.",
        "detail_zh": "贝尔定理排除定域隐变量：纠缠的关联无法用'事先商量好的经典状态'（定域实在论）解释，量子力学本质是非定域的。Aspect 1982 实验证实。",
        "prereqs": ["entanglement"], "source": "bell-1978",
    },
    "Erwin Schrödinger": {
        "zh": "薛定谔", "category": "people", "aliases": [],
        "def_en": "Created the cat thought experiment (1935); coined 'entanglement'.",
        "def_zh": "'薛定谔的猫'思想实验（1935），命名'纠缠'。",
        "detail_en": "Cat state (|000⟩+|111⟩)/√2 is the basis of QEC codes (surface code etc.).",
        "detail_zh": "猫态 (|000⟩+|111⟩)/√2 是量子纠错码（表面码等）的基石。",
        "prereqs": ["superposition", "entanglement"], "source": "schrodinger-1935",
    },
    "Costas Papaliolios": {
        "zh": "帕帕利奥利奥斯", "category": "people", "aliases": [],
        "def_en": "Harvard physics grad student who invented the 'quantum toys' (1960s) to teach Schwinger's measurement algebra.",
        "def_zh": "哈佛物理系博士生，1960 年代为教学施温格测量代数发明\"量子玩具\"（13 个铝制立方体教具）。",
        "detail_en": "Built 13 aluminum cubes inscribed with Dirac notation, representing projection operators; dubbed them 'quantum toys'. His invention is documented in Gauvin 2018 (Physics in Perspective).",
        "detail_zh": "制作 13 个刻有狄拉克记号的铝制立方体，代表投影算符，称\"量子玩具\"。其发明记载于 Gauvin 2018 论文（Physics in Perspective）。",
        "prereqs": ["Julian Schwinger", "measurement-collapse"], "source": "papaliolios-2018",
    },
    "Julian Schwinger": {
        "zh": "施温格", "category": "people", "aliases": [],
        "def_en": "QED Nobel laureate (1965); taught QM from measurement algebra, materialized as 1960s Harvard 'quantum toys'.",
        "def_zh": "1965 年诺贝尔物理学奖得主（QED）；其量子力学教学从'测量代数'出发，被制作成 1960s 哈佛'量子玩具'教具。",
        "detail_en": "Co-founded QED with Feynman and Tomonaga (1965 Nobel). His textbook 'Quantum Mechanics: Symbolism of Atomic Measurements' derives QM from Stern-Gerlach selective measurements. The 'quantum toys' were built by Papaliolios to make his measurement algebra tangible.",
        "detail_zh": "与费曼、朝永振一郎共建量子电动力学（1965 诺奖）。其教程《量子力学：原子测量的符号体系》从斯特恩-盖拉赫选择性测量出发推导整个量子力学。'量子玩具'是帕帕利奥利奥斯（Papaliolios）为把他的测量代数变得可触摸而制作的教具。",
        "prereqs": ["measurement-collapse", "superposition"], "source": "schwinger-2001",
    },
    "Terry Rudolph": {
        "zh": "特里·鲁道夫", "category": "people", "aliases": [],
        "def_en": "Schrödinger's grandson; quantum professor; author of 'Q is for Quantum'.",
        "def_zh": "薛定谔亲外孙，量子物理教授，《Q is for Quantum》作者。",
        "detail_en": "His black/white ball + box scheme is the pedagogical basis of our H-gate lesson.",
        "detail_zh": "其'黑白球 + 盒子'教学法是本平台 H 门课程的方案基础。",
        "prereqs": ["hadamard-gate"], "source": None,
    },
    "Reinhold Bertlmann": {
        "zh": "伯特曼", "category": "people", "aliases": ["伯纳尔", "波特曼", "贝特曼", "Bertman", "Bettlmann"],
        "def_en": "Physicist whose socks inspired Bell's famous entanglement metaphor.",
        "def_zh": "其'袜子'典故被贝尔引用于纠缠比喻（1978）。",
        "detail_en": "An Austrian theoretical physicist who spent most of his career at CERN. Bell used Bertlmann's habit of wearing one red and one green sock as a metaphor for quantum entanglement — seeing one sock instantly determines the color of the other, no matter how far apart.",
        "detail_zh": "奥地利理论物理学家，长期任职于 CERN。贝尔用他'一红一绿两只袜子'的着装习惯比喻量子纠缠：看到一只袜子，就立刻知道另一只的颜色——无论相隔多远。",
        "prereqs": ["entanglement"], "source": "bell-1978",
    },
}

# ---------------------------------------------------------------------------
# 四台"机器"定义（L3 噪声模拟预设，参数来自真实硬件量级）
# ---------------------------------------------------------------------------
MACHINES = {
    "ideal": {
        "name": "理想机",
        "tagline": "完美的量子计算机（教学对照）",
        "gate_fidelity": 1.0,
        "readout_error": 0.0,
        "t1_us": None,
        "t2_us": None,
        "topology": "full",
        "coupling_map": "所有比特两两相连（任意两比特可耦合）",
        "desc": "没有任何噪声的理想机器。用于对照——看到理论分布应该长什么样。",
    },
    "linear": {
        "name": "链式机",
        "tagline": "入门真实硬件（1D 链条）",
        "gate_fidelity": 0.995,
        "readout_error": 0.005,
        "t1_us": 100.0,
        "t2_us": 80.0,
        "topology": "line",
        "coupling_map": "相邻比特耦合（q[i]-q[i+1]），非相邻需 SWAP 路由",
        "desc": "量子比特排成一条线，只能和邻居耦合。跨线操作要先 SWAP。",
    },
    "grid": {
        "name": "棋盘机",
        "tagline": "主流超导量子计算机（2D 网格，对标 IBM Eagle/Heron）",
        "gate_fidelity": 0.99,
        "readout_error": 0.01,
        "t1_us": 200.0,
        "t2_us": 150.0,
        "topology": "grid",
        "coupling_map": "上下左右四邻居耦合（2D 网格）",
        "desc": "比特排列成棋盘，能上下左右耦合。主流超导机的拓扑。",
    },
    "noisy": {
        "name": "噪声机",
        "tagline": "受噪声主导的设备（感受'噪声淹没信号'）",
        "gate_fidelity": 0.97,
        "readout_error": 0.03,
        "t1_us": 30.0,
        "t2_us": 20.0,
        "topology": "line",
        "coupling_map": "相邻比特耦合（简化链式）",
        "desc": "噪声很大的设备。跑稍微深的电路，结果基本是噪声——这就是为什么要纠错。",
    },
}

# ---------------------------------------------------------------------------
# 分类视图（兼容 app.py /api/machines 的返回结构）
# ---------------------------------------------------------------------------
def _by_category(cat: str) -> dict:
    return {k: v for k, v in DICT.items() if v["category"] == cat}


TECH_TERMS = _by_category("tech")
PEOPLE = _by_category("people")
CONCEPTS = _by_category("concept")

DICTIONARY = {
    "machines": MACHINES,
    "tech_terms": TECH_TERMS,
    "people": PEOPLE,
    "concepts": CONCEPTS,
}


def get_machine(mid):
    """按 id 取机器定义。"""
    return MACHINES.get(mid)


def search(query):
    """分词搜索：标点切分 + 去停用词 + 中文长 query 子串滑窗，任一命中。"""
    import re
    if not query:
        return []
    q = query.lower()
    STOP = {"什么", "怎么", "为什么", "为啥", "和", "与", "或", "是", "的", "在",
            "what", "how", "why", "is", "are", "the", "a", "an", "in", "of", "to",
            "请", "问", "下", "我", "你", "他", "她", "它"}
    tokens = set()
    # 1. 标点切分（按空白+标点）
    for t in re.split(r"[\s,.，。?？!！:：;；()（）\[\]【】\"']+", q):
        if len(t) >= 2 and t not in STOP:
            tokens.add(t)
    # 2. 中文长 query 子串滑窗（修复"什么是量子纠错"类问句无标点问题）
    if len(q.replace(" ", "")) >= 4:
        compact = re.sub(r"[\s,.，。?？!！:：;()（）\[\]【】\"']", "", q)
        for n in (2, 3, 4):
            for i in range(len(compact) - n + 1):
                sub = compact[i:i + n]
                if sub not in STOP:
                    tokens.add(sub)
    if not tokens:
        return []
    import re as _re
    compact = _re.sub(r"[\s,.，。?？!！:：;()（）\[\]【】\"'·\-]", "", q)
    if compact not in tokens:
        tokens.add(compact)
    hits = []
    for k, v in DICT.items():
        # hay 全 lowercase（中文 lower 无害，修复"H 门"类大小写匹配）
        hay = " ".join([k.lower(), v["zh"].lower(), v["def_zh"].lower(), v["def_en"].lower()])
        hay_compact = _re.sub(r"[\s,.，。?？!！:：;()（）\[\]【】\"'·\-]", "", hay)
        if any(t in hay or t in hay_compact for t in tokens):
            hits.append({"key": k, **v})
    return hits


# ---------------------------------------------------------------------------
# 词典一致性校验（自检第一层）
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = ["zh", "category", "aliases", "def_en", "def_zh", "detail_en", "detail_zh", "prereqs", "source"]


def validate():
    """校验词典：唯一键/必填/前置概念存在/无循环依赖/别名冲突。

    返回 (ok: bool, errors: list[str])。
    """
    errors = []

    # 1. 必填字段存在；字符串字段非空（list 字段允许为空：无前置/无别名是合法的）
    for k, v in DICT.items():
        for f in REQUIRED_FIELDS:
            if f not in v:
                errors.append(f"[{k}] 缺字段 {f}")
            elif isinstance(v[f], str) and not v[f].strip():
                errors.append(f"[{k}] 字符串字段 {f} 为空")
        if v.get("category") not in ("tech", "people", "concept"):
            errors.append(f"[{k}] category 非法: {v.get('category')}")

    # 2. 前置概念必须存在且无循环依赖（DFS 环检测）
    visiting, visited = set(), set()

    def has_cycle(node, stack):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        stack.append(node)
        for pre in DICT[node]["prereqs"]:
            if pre not in DICT:
                errors.append(f"[{node}] 前置概念不存在: {pre}")
                continue
            if has_cycle(pre, stack):
                errors.append(f"[{node}] 前置概念循环依赖: {' -> '.join(stack)} -> {pre}")
        stack.pop()
        visiting.discard(node)
        visited.add(node)
        return False

    for k in DICT:
        has_cycle(k, [])

    # 3. 别名冲突：别名不得与任何规范名相同，别名之间不得重复
    all_en = set(DICT.keys())
    seen_alias = {}
    for k, v in DICT.items():
        for a in v.get("aliases", []):
            if a in all_en:
                errors.append(f"[{k}] 别名 '{a}' 与其他词条规范名冲突")
            if a in seen_alias:
                errors.append(f"[{k}] 别名 '{a}' 与 [{seen_alias[a]}] 重复")
            else:
                seen_alias[a] = k

    # 4. source 必须指向 REFERENCES 存在的 key（或为 None）
    for k, v in DICT.items():
        s = v.get("source")
        if s is not None and s not in REFERENCES:
            errors.append(f"[{k}] source 引用了不存在的文献: {s}")

    return (len(errors) == 0), errors


def all_aliases() -> list[str]:
    """全部别名（自检脚本黑名单来源）。"""
    out = []
    for v in DICT.values():
        out.extend(v.get("aliases", []))
    return sorted(set(out))


# ---------------------------------------------------------------------------
# 导出（审稿可读）
# ---------------------------------------------------------------------------
def to_markdown() -> str:
    """导出 Markdown（按分类分组）。"""
    lines = ["# LoomQ 量子计算词典（唯一权威源）", ""]
    for cat, title in [("concept", "物理概念"), ("tech", "技术术语"), ("people", "人名")]:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| 英文（唯一键） | 中文 | 一句话解释 | 前置概念 | 来源 |")
        lines.append("|---|---|---|---|---|")
        for k in sorted((kk for kk in DICT if DICT[kk]["category"] == cat), key=lambda x: DICT[x]["zh"]):
            v = DICT[k]
            src = v["source"] if v["source"] else "—"
            lines.append(f"| {k} | {v['zh']} | {v['def_zh']} | {', '.join(v['prereqs']) or '—'} | {src} |")
        lines.append("")
    lines.append("## 经典文献")
    lines.append("")
    lines.append("| 编号 | 文献 | 年份 | 说明 |")
    lines.append("|---|---|---|---|")
    for rk, r in REFERENCES.items():
        lines.append(f"| {rk} | {r['authors']}, *{r['title']}*, {r['venue']} | {r['year']} | {r['note']} |")
    lines.append("")
    return "\n".join(lines)


def to_csv() -> str:
    """导出 CSV（UTF-8 BOM，Excel 友好）。"""
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["en", "zh", "category", "def_en", "def_zh", "detail_en", "detail_zh", "prereqs", "source"])
    for k, v in DICT.items():
        w.writerow([k, v["zh"], v["category"],
                    v["def_en"], v["def_zh"], v["detail_en"], v["detail_zh"],
                    ";".join(v["prereqs"]), v["source"] or ""])
    return "\ufeff" + buf.getvalue()


def main():
    import sys
    args = sys.argv[1:]
    if "--validate" in args:
        ok, errors = validate()
        print("✓ 词典校验通过" if ok else "✗ 词典校验失败：")
        for e in errors:
            print("  ", e)
        sys.exit(0 if ok else 1)
    if "--md" in args:
        print(to_markdown())
        return
    if "--csv" in args:
        print(to_csv())
        return
    if "--aliases" in args:
        for a in all_aliases():
            print(a)
        return
    print("用法: python web/qc_dict.py [--validate | --md | --csv | --aliases]")


if __name__ == "__main__":
    main()
