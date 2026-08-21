# 新项目初始 SOP（Standard Operating Procedure）

> 版本：v1.0 · 更新：2026-08-18 · 适用范围：本模板生成的所有新项目
> 原则：**从目录结构规划阶段就做隐私隔离**；程序只写相对路径；一切可复现、可复查、留痕。

---

## §0 环境与 venv（反复被问、反复遗忘，先写死）

| 项 | 值 |
|---|---|
| 主力 Python | **3.12**（macOS，`python3.12 -m venv`） |
| venv 复用策略 | **多项目共用**（本项目群共通性强）。共享 venv 固定位置：`~/.venvs/loomsci_py312/` |
| 激活命令 | `source ~/.venvs/loomsci_py312/bin/activate` |
| 验证 | `which python` 应指向 `~/.venvs/loomsci_py312/bin/python` |
| 依赖清单 | 每项目自带 `requirements.txt`；新依赖安装后**必须**追加进 `requirements.txt` |
| 新项目加入共用 venv | `source ~/.venvs/loomsci_py312/bin/activate && pip install -r requirements.txt` |

> 若某项目依赖与共享 venv 冲突 → 单独建 venv 并**在本 SOP 开头追加记录**，绝不静默。

---

## §1 目录结构（隐私隔离是物理的，不是靠 gitignore 提醒）

```
<project>/
├── config.example.yaml   # 空模板（对外分享的唯一配置）
├── config.yaml           # 本机真实配置：绝对路径 + 全部 API key（.gitignore 排除）
├── SOP.md  LOG.md  MEMO.md
├── public/               # ══ 可对外分享区（打包只读这里）══
│   ├── scripts/          # 程序（全部相对路径，禁硬编码 key/绝对路径）
│   ├── data/             # 可分享数据
│   ├── docs/experiments/ # 实验报告（_template.md 起手）
│   └── style/            # 写作模板（QJ_5.md 等）
├── private/              # ══ 私有区（绝不分享，.gitignore 一票否决）══
│   ├── data/             # 私有数据（中间产物、不想公开的语料等）
│   └── docs/             # 私有文档（草稿、未公开调研）
└── tools/
    └── make_share_package.py  # 分享打包 + 防泄漏扫描（不进分享包）
```

**铁律**：
1. 新文件默认落在 `private/` 或本地工作区；要分享才显式放 `public/`。
2. 打包脚本只读 `public/` + 根级白名单文件。
3. `config.yaml` 永远只在本机存在，不进任何分享物。

---

## §2 程序编写规范

1. **全部相对路径**：基于仓库根的相对路径。程序开头统一：
   ```python
   from config import ROOT, DATA_DIR, ...
   ```
2. **绝对路径只出现在 `config.yaml`**（本机），程序一律 `config.py` 读取后拼接。
3. **API key 只从 `key_loader.py` 取**（env → config.yaml），禁止任何脚本内 `sk-...` / `AKLT...` 字面量。
4. 新程序先 `config.example.yaml` 同步新增字段（空值），本机 `config.yaml` 再填真值。

---

## §3 实验报告规范（模板见 `public/docs/experiments/_template.md`）

每个实验/每条命令跑完，写一份报告，固定七段：

1. 研究背景 · 2. 研究目的 · 3. 研究方法 · 4. 研究结果 · 5. 讨论 · 6. 下一步设想 · **7. 复现信息（强制）**

**§7 复现信息四要素**（缺一不可）：
- 运行命令（完整 CLI，含参数）
- 参数设置（theta/freq/seed/…）
- 输入文件（路径 + 版本/日期）
- 输出保存位置（相对路径）
- 附：耗时、数据版本 sha256（如适用）

> 报告编号：`EXP001`、`EXP002`… 按时间递增；文件名 `EXP001_<topic>_YYYYMMDD.md`。

---

## §4 写作/对外分享流程（防幻觉、可复查、留痕）

素材来源只有两条合法通道：

| 素材类型 | 通道 | 留痕要求 |
|---|---|---|
| 事实性数据（论文、数字） | 查数据库 → 查到详情（含 arxiv_id / 记录字段） | 记录查询 SQL / 来源记录 ID |
| 数值实验结论 | 本项目的实验报告（EXPxxx） | 报告编号 + 结果片段 |

**流程**：
1. 把上表中的"详情/报告结果"发送给 DeepSeek（`deepseek-v4-pro`）。
2. 按写作模板生成（默认 `public/style/QJ_5.md`）。
3. 文稿末尾附"制作流程"：用了哪些 EXP、哪些查询、模板版本。
4. **禁止**：凭记忆编造数字、编造 arXiv ID、引用数据库里不存在的文章。

---

## §5 LOG（航海日志）

- 文件 `LOG.md`，按时间线追加：`YYYY-MM-DD | 事项 | 产物/结果 | 关联文件`。
- 每完成一个可交付动作（命令跑完/报告写完/发布打包）记一行。
- 用途：事后检查进度、定位"当时做了什么"。

---

## §6 MEMO（灵感备忘录，严禁拐弯）

- 文件 `MEMO.md`，任何时刻可追加偶发想法/未验证猜想/未来方向。
- **禁止**：把 Memo 点子放进当前开发排期；禁止在执行中"顺手验证一下"。
- **唯一读取时机**：复盘/小结/结题时，统一评估哪些值得立项。

---

## §7 分享打包（`tools/make_share_package.py`）

1. 只读 `public/` + 根级白名单（README/LICENSE/requirements/config.example.yaml/SOP.md/SHARE_MANIFEST）。
2. **内容级防泄漏扫描**（不是只查文件在不在）：
   - 命中模式（具体正则见 `tools/make_share_package.py` 的 `LEAK_PATTERNS`）：本地绝对路径（`/Users/`、`/home/`、Windows 盘符）、`sk-` 开头 key、`AKLT` 开头 key、配置内联 key。
   - 命中即 fail-fast，打印文件+行号，拒绝出包。
3. 输出 `share_<project>_YYYYMMDD.tar.gz` + 校验报告。

---

## §8 重要节点更新 SOP

以下节点必须回看并更新本 SOP（bump 版本号 + 追加变更日志）：
- 新项目初始化完成时
- 首次打包分享成功后
- 出现新的隐私泄露/规避手段后
- 项目结题复盘时

---

## §9 新项目初始化清单（复制本模板后逐项打勾）

- [ ] `cp config.example.yaml config.yaml`，填绝对路径与 API key
- [ ] 激活共享 venv，`pip install -r requirements.txt`
- [ ] 在 `LOG.md` 记第一行（项目启动）
- [ ] 跑一次 `tools/make_share_package.py` 确认扫描通过（哪怕先 dry-run）
- [ ] 确认 `private/` 中无任何需要分享的文件（分享的放 `public/`）
- [ ] 更新本 SOP 头部"环境与 venv"一节为本机实况
