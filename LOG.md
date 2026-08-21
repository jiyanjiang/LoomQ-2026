# 航海日志（LOG）

> 按时间线追加，每完成一个可交付动作记一行。格式：`YYYY-MM-DD | 事项 | 产物/结果 | 关联文件`

## 2026-08-18
- | 环境决策：LoomQ 统一 Python 3.10 对齐官方容器 | 建 `~/.venvs/loomq310` 专用 venv | SOP.md §0
- | 安装 Python 3.10 | brew `python@3.10` → `/opt/homebrew/bin/python3.10` | SOP.md §0
- | 修复 macOS 26.2 + py3.10 两个坑 | pip 锁 24.3.1（truststore 崩溃）；`DYLD_LIBRARY_PATH` 指 brew expat 2.8.1（pyexpat 缺符号） | SOP.md §0
- | 安装三个 L1 SDK | spinqit 0.2.4 / pyqpanda 3.8.5 / braket 1.95.0+default-sim 1.27.0，实测互兼容 | starter_kit/requirements.txt
- | 实现 L1 adapter | `transpile()` 三目标格式（QASM2/QASM3/OriginIR）+ `run()` 三模拟器 | starter_kit/adapter.py
- | L1 公开自检 6/6 通过 | bell+ghz3 × spinq/originq/braket，fidelity 全部达标，exit=0 | starter_kit/report.json
- | 协作铁律：禁止选择题式提问 | 写入 SOP §0；改用开放式自然语言讨论 | SOP.md
- | 搭建对齐尺子 | qasm_semantics.py（qelib1.inc 矩阵 + 态矢量模拟），bell/ghz3/h_t_h 自验通过 | tests/qasm_semantics.py
- | 12 门对齐度实测 | spinq/originq 12/12 对齐；braket s/sdg/t/tdg 本地模拟器偏差 | tests/alignment_check.py + alignment_spec.md
- | 修复 adapter 三处 | braket 测量重复 bug、寄存器名统一（bits→q）、注释行处理 | starter_kit/adapter.py
- | braket s/t 定性 | P2 探针 + QPT 反推：1.27.0 本地模拟器 pow 幂次门失效，s/t 退化恒等 | braket_s_probe.py + qpt_braket_s.py + braket_notes.md
- | braket s/t→rz 展开 | adapter braket 路径展开 s→rz(π/2) 等，对齐度 8/12→12/12 | starter_kit/adapter.py + alignment_check.py
- | transpile/run 双模式分离 | transpile 契约输出（stdgates.inc+标准s/t），run 本地模式（braket_gates.inc+rz展开），消除绝对路径隐患 | starter_kit/adapter.py + braket_notes.md §三
- | 测试集扩展 | QFT-5/Grover-3/Toffoli-3 加入，20 用例 × 3 后端 60/60 PASS | tests/cases.yaml + gen_algo_circuits.py
- | 容器等价验证 | 干净 venv 仅装 requirements.txt 跑 L1 6/6 PASS，依赖清单完备 | /tmp/loomq_container_sim
- | L2 agent_chat 实现 | LLM 生成 QASM + 三后端自验闭环，公开 GHZ PASS、QFT-4 生成正确 | starter_kit/adapter.py + prompts/l2_qasm_generator_v1.yaml
- | submission.yaml 改 l2:true | declared 模式 7/7 PASS（L1 6/6 + L2 1/1），参赛声明与实现一致 | starter_kit/submission.yaml
- | L2 改用 v4-flash | 本地用正式同模型调试，GHZ/QFT-4/参数门生成均正确 | SOP §3.5
- | wstate_n3 实现 | Wikipedia 构造（ry(2·arccos(1/√3))+受控H+2CNOT+X），001/010/100 各 1/3 | tests/gen_algo_circuits.py + cases.yaml（21/21 用例）
- | L2 边界测试 | v4-flash 生成 GHZ-5/ryrz纠缠/ccx/QFT-5 全部合规且语义正确，v1 提示词无需迭代 | prompts/l2_qasm_generator_v1.yaml
- | loomq_lib 固化 | pip 可装包（尺子+三后端+21电路库+runner），editable 安装验证通过 | loomq_lib/
- | 使用帮助 | USAGE.md + USAGE.html，5010 端口展示 | docs/USAGE.md + docs/USAGE.html
- | 使用帮助加通俗讲解 | 12 门（翻面/抛币/涂色/联动比喻）+ 9 算法（同面硬币/抽屉/传真机），面向新手 | docs/USAGE.md + docs/USAGE.html
- | Web 工作台骨架 | Flask 两栏布局（活动栏+主区+右上过程+右下对话框）+ 门图标 SVG + 电路图渲染器 + 内容字典 | web/（app.py + gates.js + circuit.js + content.py + run_web.sh，端口 5011）
- | Web DYLD 坑解决 | macOS 26 下 `VAR=val nohup cmd` 前缀赋值不传 DYLD，必须 export 后 &+disown 启动 | web/run_web.sh
- | Web 交互升级 | 对话框放大(25-33vh)、文档 iframe 挂接、过程面板直方图+文字讨论、API Key View、拖拽搭电路(门托盘→画布→QASM→运行) | web/（style.css + app.js + builder.js）
- | Web 结构升级 | 输入框固定 22vh 大尺寸、活动栏分工(电路库/新电路/帮助/设置)、Composer 独立默认视图、帮助视图、QASM 一键复制 | web/（index.html + builder.js + style.css）
- | Web 修复 | 多比特门改竖直画法（控制点●/目标⊕竖连，cx/cu1/ccx/swap）、对话框贴浏览器底边（flex 撑满） | web/（circuit.js + builder.js + style.css）
- | PRD 文档 | 产品需求文档固化（布局/功能/架构/主题/出彩规划） | docs/PRD.md
- | Web 模板化 | 帮助视图改 /api/help 模板化渲染（5基础+12门+9算法+5步骤）、主题切换（经典/黑色/清新，localStorage 持久化） | web/（app.py + app.js + index.html + style.css）
- | PRD 自检 + DS 审核 | PRD_SELFCHECK.md（完整性/一致性/待决策）+ DS v4 pro 审核（5矛盾/7缺失/优先级/大富翁判定）| docs/PRD_SELFCHECK.md + data/prd_review_20260818.json
- | 量子游戏竞标 | GAME_DESIGNS.md（A袜子/B转盘/C大富翁/D闯关/E寻宝）+ DS 审核定案（首选B，执行序 B→D→C→A）| docs/GAME_DESIGNS.md + data/game_review_20260818.json
- | 门不透明 | 方框门/cu1目标框改白底，覆盖 wire 线（主题适配待办）| web/static/js/{gates,circuit,builder}.js
- | 布洛赫球组件 | three.js 球+轴+态矢量箭头+OrbitControls，活动栏第5按钮；量子转盘（θ/φ滑块+8门操作+测量坍缩+概率条）| web/static/js/bloch.js + app.js + index.html
- | 修复3问题 | three.js 本地化(vendor r128，CDN不可达)；电路库筛选(vm验证无bug+缓存bust?v=2)；补GHZ-5(算法9→10，评测核心) | web/static/vendor/ + index.html + loomq_lib/circuits.py
- | 修复 init 崩溃 | 布洛赫球异步加载+init()同步setState=TypeError崩溃→中断init→chips绑定失败→筛选失效。修复：onReady回调+移除同步setState | web/static/js/{bloch.js, app.js}
- | playwright 自测 | 控制台0错误(favicon 404除外)；筛选'算法'后电路项10个；详情区正常渲染 | playwright-cli 实测验证
- | 布洛赫球批量测量 | 5000 shots 统计条(蓝|0⟩/橙|1⟩)+理论对比，与单次坍缩互补 | web/static/js/app.js + index.html
- | 伯特曼袜子游戏 | 纠缠配对(同面/异面模式切换)，16牌翻牌+规则讲解+配对判定 | web/static/js/socks.js + index.html + style.css
- | 测量改直方图 | 单次+5000shots都用ECharts直方图，与三后端counts可视化统一；标题含理论值对照 | web/static/js/app.js + index.html
- | 测量统计增强 | 5000 shots 实时累计（setTimeout分批渲染不卡主线程）+ 理论σ对比+ "在2σ内" 提示；确定性态σ=0特殊处理 | web/static/js/app.js
- | 教程+第1课 | 活动栏加"教程"按钮（默认活动），课程树6课（3 ready+3 planned），第1课 H门游戏（黑球白球盒Terry方案3关：探H/不挑色/H²=I）| web/static/js/{app.js, hgate.js} + web/content.py
- | 自检+修bug | Flask旧进程缓存HTML模板导致空白（debug=False未自动reload→必须重启）；活动栏按钮次序按用户要求（电路库/新电路/布洛赫球/互动课程/使用帮助）；课程内容统一折叠展开+返回按钮 | web/templates/index.html + app.js + hgate.js
- | 组件化（首批） | 新增 components/{histogram,measure}.js：Histogram统一ECharts封装，MeasurePanel统一测量（累积式+5000次，去单次测量）；布洛赫球/H门迁移到MeasurePanel（重复轮子消除） | web/static/js/components/ + app.js + hgate.js
- | 测量标准件+自检流程 | 测量按钮统一文案"测量/测量5000次"（去掉自定义名字"再测一粒子"）；建立 web/selfcheck.sh 自动化自检（服务/按钮一致性/视图错误）| web/selfcheck.sh + index.html + hgate.js
- | 测量标准件v2 | Histogram全百分比（Y轴%/标签%/tooltip%/参考柱%）；MeasurePanel惰性init修复echarts隐藏容器空白bug；切换门/滑块reset；切换关卡reset | components/{histogram,measure}.js + app.js + hgate.js
- | 测量标准件v3（Qiskit规范） | 调研Qiskit plot_histogram：X轴位串柱/Y轴0-1概率/同位置并排对比/number_to_keep解决多比特放不下。重写Histogram+MeasurePanel+renderHistogram；batch慢一倍（125/帧→2s看清收敛）| components/{histogram,measure}.js + app.js
- | 颜色统一+三套合一(A) | 统一Colors.theory=#16a34a（消除#10b981/#16a34a混用），新建colors.js；QasmModule组件统一QASM解析：circuit.js parse+builder.js toQasm委托QasmModule；新增toOpSet/equalOpSets/validate（供后续算法匹配/大富翁用） | colors.js + components/qasm.js + circuit.js + builder.js
- | L3噪声模拟(C) | qc_dict词典(4机器+7术语+8人名+5概念)；loomq_lib/noise.py退极化+测量错误+拓扑约束；GHZ-3在4台机器fidelity梯度验证(ideal0.998→linear0.916→grid0.879→noisy0.095)显示"噪声淹没信号"；Web选机器UI+教育提示 | web/qc_dict.py + loomq_lib/noise.py + app.py + app.js
- | 修正伯特曼袜子 | 全站17处"伯纳尔"(用户最早笔误)修正为"伯特曼"(Bertlmann正确音译)，8文件(index.html/socks.js/qc_dict.py/style.css/GAME_DESIGNS.md/prd_review/game_review/LOG)；根因：上次只搜正确拼写变体漏搜笔误源头 | 全站
- | 纠错流程升级 | selfcheck.sh v2 加[0/5]术语黑名单检查(全站grep历史错误变体，防笔误被一直带着)；qc_dict.py人名条目补"勿写伯纳尔/波特曼"防再犯 | web/selfcheck.sh + web/qc_dict.py
- | 词典 v2（9字段 schema） | qc_dict.py 重构：英文唯一键+zh+aliases+def_en/zh+detail_en/zh+prereqs+source；REFERENCES经典文献5篇(Bell 1978/Shor 1994等)；validate()校验(必填/前置存在/无循环/别名冲突)；导出MD/CSV；aliases只存纯错误变体(伯纳尔等6个)；黑名单由词典动态生成(单一数据源)；负向验证：临时写"伯纳尔"被0/5拦截 | web/qc_dict.py + web/selfcheck.sh
- | 统一查询页（帮助+词典合并） | PRD v2.0更新（6按钮/词典schema/查询设计入档）；/api/search词典+帮助双搜；/api/chat词典检索注入（电路意图走自验/问答模式直接LLM）；帮助视图加搜索框+名词链接化+词典卡片；search函数修复：标点切分+中文子串滑窗+停用词+hay全lower；prompts/chat_assistant_v1.yaml独立可替换 | web/app.py + web/templates/index.html + web/static/js/{app.js,style.css} + web/qc_dict.py + prompts/chat_assistant_v1.yaml
- | 伯特曼袜子 v3 | 修复3个真问题：①每对加独特"第N双"徽标(可区分同色不同对)②加背景故事折叠区(出处/典故/与纠缠关系/科学意义)+规则说明(怎么玩+获胜条件)③加胜利判定(配齐8对→绿色胜利横幅+体验总结+词典链接)；修模式逻辑：same/diff 改变牌面而非只改提示；App暴露 searchDict/switchView 给 socks 用；积分榜记入PRD待办P3 | web/static/js/socks.js + web/static/css/style.css + web/templates/index.html + web/static/js/app.js + docs/PRD.md
- | 伯特曼袜子 v4（颜色语义） | 修复真问题：每张牌=单比特|0⟩/|1⟩(双比特标签00/11改为单比特)，颜色统一规则0=红1=绿；same=4对红红+4对绿绿(00全红/11全绿)，diff=8对一红一绿；说明/规则区补充"第N双不可互换"+"0红1绿"颜色规则 | web/static/js/socks.js + web/templates/index.html + web/static/css/style.css
- | 伯特曼袜子 v5（双数可配置） | 减半默认4双(8张牌，快速游戏) + 保留8双完整版下拉切换；解决"随机翻牌玩得久"问题；胜利说明改为动态双数 | web/static/js/socks.js + web/templates/index.html
- | 袜子可胜性自检 | 修真实bug：失败分支setTimeout(1800ms)状态竞争(清掉新选的第三张)+僵尸翻开；改为立即翻回无延迟。新增web/selfcheck_socks.py：800局(4/8双×same/diff×200洗牌)模拟完整对局，验证牌面完整/伙伴唯一/最优策略与随机策略均必达全胜；接入selfcheck.sh[1/5] | web/static/js/socks.js + web/selfcheck_socks.py + web/selfcheck.sh
- | 袜子配色统一管理 | 删掉 filter: hue-rotate 硬凑红色（不可控）。colors.js 加 sockRed/sockGreen 语义色。style.css 三主题定义 --sock-red/--sock-green CSS 变量（classic#dc2626/#16a34a、dark#f87171/#4ade80、fresh#ef4444/#22c55e）。socks.js 用 SVG path 代替 emoji，fill="var(--sock-color)" 随主题变。验证：classic 红袜鲜红、dark 红袜亮红、fresh 红袜鲜红 | colors.js + style.css + socks.js
- | 内容生产流程 + 量子游戏独立视图 | 立内容生产流程：JSON(web/game_content/socks.json) → /api/game-content/<id> 读取 → 前端模板化渲染。后端附加 dict_terms 词典素材。前端 linkifyDict 自动把section里所有词典名词变链接+弹卡片。PRD 活动栏6→7按钮(新增量子游戏独立视图)。socks.js 改事件委托(openGame重建DOM不失效) | web/game_content/socks.json + web/app.py + web/static/js/app.js + web/static/js/socks.js + web/templates/index.html + web/static/css/style.css + docs/PRD.md
- | 量子游戏页 v2 + aliases 零暴露 | ①袜子emoji🧦+边框底色(红/绿)②文字介绍<details open>折叠(游戏本体永不折叠)③词典词条弹小窗(不切视图)④批量审稿脚本+提示词⑤【aliases零暴露】Bertlmann词条detail重写为正常人物介绍，--md/--csv/API/前端全去别名展示，"伯纳德"移出aliases(是另一人)；aliases数据层保留(内部自检黑名单) | socks.js + app.js + app.py + index.html + style.css + qc_dict.py + review_content.py + content_review_v1.yaml
- | 袜子 SVG 重绘（emoji→拟真 SVG） | 用户质疑emoji🧦不能上色——确认：emoji是彩色字形，CSS color/fill无效。改回SVG矢量袜子，重绘拟真造型(袜筒+弯脚+白袜口横条)，fill用--sock-color(随主题变：classic红#dc2626/绿#16a34a，dark亮红#f87171/亮绿#4ade80)。卡片红绿边框/底色保留(双重语义) | socks.js + style.css
- | 计时器 + 文案统一 | 三件事：①文案统一：app.js/socks.json/socks.js三处"16只袜子"改为"8只袜子=4双纠缠对"②胜利横幅动态双数+"你配齐了全部X双伯特曼的袜子！用时 mm:ss"③计时器：state加_timerId/_startTs+startTimer/stopTimer/resetTimer（首翻启动/胜利停止/重置归零），setInterval 250ms刷新显示，UI加橙色⏱ mm:ss元素。8双模式调整暂不做（等用户拍板） | socks.js + app.js + game_content/socks.json + style.css
- | 小游戏开发流程 SOP | docs/game_dev_sop.md v1.0 定稿：8步流水线(创意卡→定位→文案→技术方案→DS审校→分步实施→自检4件套→入库)，含创意卡模板/课程归属规则/文案schema/方案5层/审校方式/基建清单。PRD待办改引用SOP。建议下一个=施温格积木(第5课测量代数) | docs/game_dev_sop.md + docs/PRD.md
- | 施温格积木·调研+创意卡+文案+方案+审校 | 完整调研：历史原型=哈佛Papaliolios 1960s"量子玩具"(13铝立方体刻狄拉克记号,代表代数对象非仪器,入藏CHSI,Gauvin 2018论文记载)。产出：game_content/schwinger.json(4节:施温格是谁/积木由来/怎么玩/为什么有用)+docs/schwinger_blocks_tech.md(8关阶梯+正交判定表+水果类比通俗解读)。词典补：Julian Schwinger/Costas Papaliolios/non-commuting词条+REFERENCES 3篇(schwinger-2001/papaliolios-2018/aspect-1982)。DS v4 pro三轮审校(真key已配)：抓出σxσy=iσz数学错误/施温格年龄年份(1918→1947=29岁)/"黄香蕉"概率性/“透过"是比喻等，全部修复，最终schwinger=pass/socks=pass | web/game_content/schwinger.json + docs/schwinger_blocks_tech.md + web/qc_dict.py + data/schwinger_review_20260819.md
- | 施温格积木 v1 实施 | schwinger.js 落地(4积木+4正交判定+8关卡+build挑战关+计时+胜利)+app.js GAME_LIST集成+content.py第5课ready+COURSE_NAV跳游戏视图+style.css方块/光线/托盘样式+selfcheck_schwinger.py可胜性自检(正交表矩阵验证/8关答案唯一/挑战关存在解,接入selfcheck.sh)。playwright实测：游戏列表2张卡+游戏详情4节文案+狄拉克记号方块+绿/红线透光模拟+计时器+判定按钮全工作 | web/static/js/{schwinger.js,app.js} + web/templates/index.html + web/content.py + web/static/css/style.css + web/selfcheck_schwinger.py + web/selfcheck.sh
- | 符号约定统一（主流 0=↑ 1=↓）| 用户反转：改与量子信息主流一致。落地：①qubit词条补"|0⟩=|↑⟩(S_z+ħ/2)、|1⟩=|↓⟩(−ħ/2)，与Qiskit/IBM一致"②socks.json颜色规则补"(主流约定: |0⟩=自旋z方向+、|1⟩=z方向−；红/绿只是游戏配色)"③schwinger.json四态定义补量子信息记法对应(|↑⟩=|0⟩、|↓⟩=|1⟩、|+⟩=(|0⟩+|1⟩)/√2) | qc_dict.py + socks.json + schwinger.json
- | 施温格挑战关 v2（目标光强）| 用户指出原第8关"选择题"太浅：升级为目标光强组合挑战（入射态+目标+托盘+积木限用1次）。关键修正：**入射态必须指定**——"光强=1"唯一解是 I（自然光入射），|↑⟩⟨↑| 在入射|↑⟩时才=1。新增web/enumerate_schwinger.py(解空间全枚举工具)+prompts/challenge_review_v1.yaml。DS v4 pro审稿：challenge score=9 pass(DS建议ch4补[up,down]实测为0，DS心算错，未采纳)；socks也修4处(期刊名/经典关联声明/测量后坍缩/Aspect全名/8双表述) | web/enumerate_schwinger.py + prompts/challenge_review_v1.yaml + scripts/review_content.py + web/game_content/socks.json
- | 施温格进阶题集 v1（标准组件）| 用户定调模块化：题目全JSON定义+标准组件(入射仅|↑⟩/|↓⟩，取消自然光；积木4投影+I)。新web/game_content/schwinger_questions.json：8题由易到难(q1投影保持/q2正交挡光/q3跨基概率半/q4幂等+跨基组合/q5非对易z→x→z/q6同基正交对称/q7三次跨基1/8/q8对称镜像)，每题含concept标注+explain_pass/explain_fail双向通俗解读(对=强化/错=纠错学习)。DS v4 pro审稿score=9.5 pass(其q4/q7补解建议经数学枚举证伪：q4[plus,up]=0.25≠0.5、q7[plus,up,plus]违反限用1次；未采纳)。全部8题数学验证正确+解集完备(含min_blocks约束)。旧schwinger_challenges.json删除。review_content.py支持questions schema+剥JSON围栏 | web/game_content/schwinger_questions.json + scripts/review_content.py + prompts/challenge_review_v1.yaml
- | 进阶测试模式接入游戏 | 用户拍板：基础8关后进入"测试模式"(读JSON→显示入射+目标+托盘→精确出射强度判定)。实施：app.py加/api/schwinger-questions；schwinger.js加state.testMode/testQ/testBuilt/testResult+beamIntensity()精确光强计算+VECTORS态向量+rendersTest/answerTest/testWin三个函数+winGame添加"开始进阶测试"按钮+init事件委托支持测试模式data-add/submit；CSS补测试头部/概念标签/解读区/已用积木样式。playwright实测：基础8关通关→胜利横幅出现"开始测试"→q1显示"入射|↑⟩目标1倍 📌投影保持"→拼[up]提交→答对+自动跳q2(正交挡光，答对1)。整个流程闭环 | web/app.py + web/static/js/schwinger.js + web/static/css/style.css
- | 基础题v2（光强判定+图形化入射）| 用户反喷：原基础题"判断透/挡"把答案写在题面上+入射光应图形化。修复：①LEVELS全改为(incident, blocks, answer)结构，answer改为精确光强数值(1.0/0.5/0.25/0)；L6改入射|↓⟩避免与L7答案重复；②第1-7关判定按钮从"透/挡"改为4个光强按钮(1/1/2/1/4/0)心算|⟨后|前⟩|²连乘；③入射光SVG图形化：incidentSvg(incident)在布洛赫圆上画圆点+箭头（|↑⟩向上/|↓⟩向下/|+⟩右上斜/|−⟩左上斜/任意态|α⟩），render和renderTest都加；④第8关build关保留(拼出光强0)但托盘逻辑调整；⑤selfcheck_schwinger.py同步新结构(intensity函数精确光强验证+L6改对称考察) | web/static/js/schwinger.js + web/selfcheck_schwinger.py + web/static/css/style.css
- | 基础题v3（粒子透/挡+入射图形化）| 用户再次反喷：v2光强判定(1/2/1/4)对基础太深，基础题应只区分"有粒子通过/被挡住"+入射图形化要放在积木串左侧+统一用"粒子"措辞。修复：①LEVELS去掉answer字段(只有incident+blocks+explain)，answer函数改回透/挡布尔判定；②统一措辞为"粒子"（按钮"粒子能通过/被挡住"，标题"入射粒子+积木串"），但保留历史叙述(origin/who/why)中的"光"(还原真实量子玩具)；③incidentSvg移到积木串最左侧(sw-incident-block虚线框+圆点+箭头+sym)，作为拼串的第一个元素；④selfcheck_schwinger.py同步LEVELS结构(incident, blocks, expected_pass)+验证逻辑改透/挡布尔+挑战关验证改"挡住粒子" | web/static/js/schwinger.js + web/selfcheck_schwinger.py + web/game_content/{schwinger.json,schwinger_questions.json} + web/static/css/style.css
- | 措辞定稿（粒子数比，非光强非概率）| 用户深入分析：光比粒子抽象(光偏振需相位/圆偏振，光子自旋1超出量子信息)；概率也抽象(Born规则/随机性不符竞赛宗旨)。定稿：统一"粒子(自旋-1/2)"图像，进阶测试用"出射粒子数=入射粒子数的1/2/1/4/1/8"(100进50出，具象可数)；origin段加括号说明"(历史玩具用偏振光演示；本游戏用自旋-1/2粒子图像，数学完全等价)"。落地：questions.json全部target_text/explain改粒子数比+note/model.rate_rule同步；schwinger.json why段"光的透过"改"粒子的通过比例(100个|↑⟩过|+⟩⟨+|出来50个)"；schwinger.js testTargetText/answerTest/胜利横幅全改"出射/入射粒子数比" | web/game_content/{schwinger.json,schwinger_questions.json} + web/static/js/schwinger.js
- | 措辞彻底清理+第8关题目醒目化 | 用户反喷：app.js/schwinger.json 仍有"拼积木判断光能否透过"残留+第8关界面没写"挡住粒子"目标。修复：①app.js副标题+游戏卡desc全改"粒子"；②schwinger.json howto"怎么算赢"段"判断光能否透过"残留+origin段"光能否透过"全改"粒子能否通过"（保持括号史实说明）；③schwinger.js render 改题目区逻辑：第1-7关显示"题目：入射粒子|↑⟩，下面这串积木，粒子能否通过？"，第8关（build）显示"挑战：入射粒子|↑⟩，请拼出把粒子挡住的积木组合（放1块|↓⟩⟨↓|即可，或含正交对的组合）"——题目从隐式升为顶部醒目黄底，自己核对全部8关：L1-L7判定对、build关单块[down]即可挡住、题目/提示/答案全部一致 | web/static/js/{app.js,schwinger.js} + web/game_content/schwinger.json
- | 测试截图集中管理 | 根目录65张playwright测试截图移入docs/test_screenshots/，.gitignore忽略该目录 | docs/test_screenshots/ + .gitignore

## 2026-08-19
- | 【官方事实】SpinQit Cloud 后端未配置 shots 默认 1024 | doc.spinq.cn 原文 "If shots are not configured, the default is 1024." | LOG + results/spinq_analysis_evidence_20260819.md §0
- | 【事实澄清·撤回此前"伪造"误判】starter_kit/evidence/ 是官方模板自带的范例文件（创建时间 22:28，早于我们 22:49/22:54 的实验）；README 预填的 G-260819-0003/S-260819-0001、shots=16384 均为模板示例内容，与我们的实验无关，非 AI 伪造 | 依据：文件创建时间 + starter_kit/evidence/README.md 模板结构（此前的"伪造实锤/独立扫描"分析系误判，已整体撤回） | —
- | 【真实情况】web 版 shots=1024 为缺省值、不可设置；SDK 版 shots 可设置，我们统一跑 5000 | 用户 2026-08-19 确认 | —
- | web vs SDK 一致性分析（真实数据版） | 同一平台/同一电路：web(1024) vs SDK(5000) 保真度 Bell 95.6% vs 86.5%、GHZ 89.8% vs 65.9%，差异显著（尤其 GHZ 差 24pp）需重跑量化 | results/spinq_analysis_evidence_20260819.md + scripts/archive_spinq_analysis.py
- | 遗留事项 | web vs SDK 差异(Bell 95.6% vs 86.5%、GHZ 89.8% vs 65.9%)需重复运行量化；建议 SDK GHZ(5000 shots) 重跑 2-3 次确认真实保真度 | —（⚠️ 2026-08-20 已关闭：统一 8192 shots 口径后此对比作废，见当日记录）

## 2026-08-20
- | 【统一口径】8192 shots 为唯一提交口径 | 组织方明确要求；全盘涉及旧数据（web 1024/SDK 5000/16384 模板）的残留一并归档，只保留 8192 shots 数据 | LOG + results/
- | 【归档】SpinQ 旧 5000 产物 4 目录 | bellstate_gemini_vp_shots5000 / _backup_G-260819-0004 / ghz_triangulum_vp_shots5000 / ghz_state_2 → results/spinq_sdk_20260819/_archive_5000shots/（保留不删） | results/spinq_sdk_20260819/
- | 【归档】本源 Bell submitted 失败残留 | bellstate_wukong180_shots8192（job 3A0E... submitted 无结果）→ results/originq_20260820/_archive/（非申报 job 838F...） | results/originq_20260820/
- | 【脚本】SDK shots 默认统一 8192 | spinq_sdk_bellstate_gemini.py / spinq_sdk_ghz_triangulum.py：DEFAULT_SHOTS 5000→8192 + docstring/help/产物目录说明同步 | scripts/spinq_sdk_*.py
- | 【A 任务完成】L1 真机证据双平台 8192 齐全 | SpinQ G-260820-0005 Bell（95.04%）+ S-260820-0001 GHZ（74.95%），本源 838F... Bell（100%）+ 21F3... GHZ（99.93%），全部 selfcheck 绿，evidence/README.md 双平台 7 字段已填 | starter_kit/evidence/README.md + results/{spinq_sdk_20260819,originq_20260820}/
- | 【遗留关闭】web vs SDK 差异量化 | 统一 8192 shots 后旧对比（1024 vs 5000）不再适用，相关重跑建议作废 | LOG 08-19 行 + spinq_analysis_evidence_20260819.md（历史归档保留）

## 2026-08-21
- | L3 申报填写完成 | evidence/README.md L3 段三项已填（规格 docs/l3_riscv_encoding_spec.md / 实现 riscv_emulator.py + adapter.py::compile_hybrid L555 / 测试命令 evaluator.py --level l3）；submission.yaml l3:false→true；evaluator 全量 6/6 PASS + 隐藏变体矩阵 11/11 全过 | starter_kit/evidence/README.md + starter_kit/submission.yaml
- | 文档同步 | SOP §3.7 新增（L3 契约/自验/申报状态）+ PRD 版本记录 v2.2 + PRD_SELFCHECK 竞赛提交物自检节（五人分项全 ✅） | SOP.md + docs/PRD.md + docs/PRD_SELFCHECK.md
- | 【关闭】SpinQ 任务页截图 | 多次讨论定论：SpinQ 云 web 端无任务页截图入口，此项不补（辅助材料，不扣分），PRD_SELFCHECK 一·五节已同步 | docs/PRD_SELFCHECK.md
- | Composer 阶段 A：QASM↔电路图双向同步 | builder-qasm 去 readonly 可编辑 + input 防抖 150ms → loadQasm 反向解析渲染（layoutOps 按列排布复用 circuit.js 算法）；未知门经 GATE_SVG 正常渲染 + log 提示；清空文本同步清空画布；syncQasm 加 syncing 防循环；修复 qasm.js 分号仅替换首处 bug（多门单行解析错误）；版本号 v7→v8；浏览器实测双向闭环（h/cx 单行→画布、rz(pi/4)/y 渲染、拖拽→QASM 回归零破坏） | web/static/js/builder.js + components/qasm.js + templates/index.html + style.css

- | Composer 紧凑布局 + 阶段 B 自动搭建 | renderCanvas 紧凑化（列宽60→42/行高50→44/门中心21，20列电路宽度-30%；QASM 区 min-height 120→190）；透明框缩至不越相邻行/列（修复相邻门框拦截 drop 的隐患）；阶段 B：发送按钮旁「自动搭建」checkbox → sendChat 勾选时 Builder.loadQasm(qasm,true) 自动填画布+切 composer 视图+活动栏高亮+QASM 文本区同步（loadQasm 加 syncText 参数）；不勾选保持静态图预览；浏览器实测：GHZ 端到端自动搭建、cu1/swap 新坐标渲染、有门时拖拽回归通过（此前失败根因=重启后默认视图非 composer 致热区 display:none，非代码 bug） | web/static/js/builder.js + app.js + templates/index.html + style.css

- | Composer 紧凑布局 v2（再缩一轮）+ 修复多比特门透明框越列 | 列宽42→36/行高44→40/门中心18，单比特门图标包 scale(0.8)（40→32px），cu1 盒24→22、swap 图标24→20、控制点 r3.5→3、⊕ r6→5；40门电路 viewBox 1746→1498（-14%），GHZ 3门 234→166；修复多比特门透明框横向越列隐患（span+36 宽会盖住右侧相邻列热区，改固定 28px=gx±14 不越列）；浏览器实测：GHZ 渲染、40门宽度、cx 右侧列横向拖放 drop 全部通过 | web/static/js/builder.js（v10）

- | 文档同步（收口） | 进度小结入档：SOP v1.2→v1.3（版本行同步；§3.7 L3 已在当日文档同步新增）、PRD v2.1→v2.3（版本行同步 + §二/§三 Composer 条目补「双向同步/LLM 自动搭建/紧凑布局 v2」+ 版本记录补 v2.3 行）、PRD_SELFCHECK v1.1→v1.2（版本行同步 + Composer 自检行补三连改）；三文档版本行与实际内容全部对齐 | SOP.md + docs/PRD.md + docs/PRD_SELFCHECK.md

- | Bonus +8 量子 RISC-V 扩展补做完成 | fork riscv_emulator.py 新增 5 条量子指令（qinit/qh/qcnot/qrx/qmeas），RISC-V CUSTOM-0(opcode=0x0B) I-type 编码，4-qubit 态矢量 + 测量投影坍缩写回经典寄存器，经典 7 条指令与 load_program/set_register/get_register/execute 接口逐字不变；量子指令统一经 32 位机器码路径执行（encode_quantum→decode_quantum→_exec_quantum_word）；规格 docs/riscv_quantum_extension_spec.md（编码表机器码为实测校准）；端到端测试 tests/test_riscv_quantum_ext.py 16/16 PASS（官方回归/单门态矢/Bell+GHZ/含参门/测量坍缩一致/分布 8192 次仅 00/11/混合程序/编码往返/机器码等价/L3 契约回归）；evaluator --level all 6/6 + L1 套件 21 用例×3 后端 63/63 回归通过 | starter_kit/riscv_emulator.py + docs/riscv_quantum_extension_spec.md + tests/test_riscv_quantum_ext.py
- | 文档口径修正 + evidence 重写 | docs/l3_riscv_encoding_spec.md 首行"8 分 Bonus"→"15 分 L3"；SOP §3.7 标题去"Bonus"+新增 §3.8 量子扩展节；§5.3 Bonus 行 0-8(存疑)→8、风险点标记已解除；§5.4 清单勾选；evidence/README.md Bonus 段重写为量子扩展三件套（此前误把 L3 15 分内容标为 +8 Bonus） | docs/l3_riscv_encoding_spec.md + SOP.md + starter_kit/evidence/README.md

<!-- 追加格式示例：
- | 完成 EXP001 实验 | ARI=0.85 | public/docs/experiments/EXP001_xxx_20260818.md
-->
