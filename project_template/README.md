# <项目名> · 项目模板

> 本目录是**新项目初始化模板**（v1.0，2026-08-18）。
> 用法：把本目录整体复制到新项目路径，按 `SOP.md §9 初始化清单` 逐项打勾即可开始。

## 目录结构

```
<project>/
├── SOP.md              # 初始 SOP：环境/路径/报告/写作/日志/Memo 全部规则
├── LOG.md              # 航海日志（时间线）
├── MEMO.md             # 灵感备忘录（结题前不读不排期）
├── config.example.yaml # 空模板（对外分享的唯一配置）
├── config.yaml         # 本机真实配置（绝对路径 + 全部 API key，.gitignore 排除）
├── public/             # ══ 可对外分享区（打包只读这里）══
│   ├── scripts/        # 程序（相对路径；config.py / key_loader.py 已就位）
│   ├── data/           # 可分享数据
│   ├── docs/experiments/  # 实验报告（_template.md）
│   ├── docs/writing_flow.md  # 写作流程规范
│   └── style/QJ_5.md   # 写作模板（奇迹笔记 5.0）
├── private/            # ══ 私有区（绝不分享）══
│   ├── data/
│   └── docs/
└── tools/make_share_package.py  # 分享打包 + 防泄漏扫描
```

## 快速开始

```bash
cp config.example.yaml config.yaml        # 填写绝对路径与 API key
source ~/.venvs/loomsci_py312/bin/activate  # 共享 venv（SOP §0）
pip install -r requirements.txt
python -c "import sys; sys.path.insert(0,'public/scripts'); import config, key_loader; print(config.PUBLIC_DATA_DIR); print(key_loader.get_deepseek()['model'])"
python tools/make_share_package.py --dry  # 防泄漏扫描验证
```

## 三条铁律

1. 新文件默认落 `private/` 或本地工作区；要分享才放 `public/`。
2. 程序只写相对路径；绝对路径与 API key 只在 `config.yaml`。
3. 分享包只读 `public/`，出包前必跑防泄漏扫描。
