# SHARE MANIFEST（分享清单）

> 分享包内容 = `public/` 全量 + 根级白名单。由 `tools/make_share_package.py` 生成。
> 本文件与打包脚本共同维护：**只读 public/，private/ 永不进包**。

## 包内包含

| 路径 | 说明 |
|---|---|
| `public/scripts/` | 程序（相对路径；config.py / key_loader.py） |
| `public/data/` | 可分享数据 |
| `public/docs/experiments/` | 实验报告（_template.md） |
| `public/docs/writing_flow.md` | 写作流程规范 |
| `public/style/QJ_5.md` | 写作模板 |
| `README.md` / `LICENSE` / `requirements.txt` | 标准工程文件 |
| `config.example.yaml` | 空模板（复制为 config.yaml） |
| `SOP.md` | 初始 SOP |
| `SHARE_MANIFEST.md` | 本文档 |

## 绝不进包（一票否决）

- `config.yaml`（本机真实配置：绝对路径 + API key）
- `private/`（私有数据与文档）
- `tools/`（开发工具，含打包器本身）
- `*.duckdb` / `output/` / `*.tar.gz`（可重建产物）

## 打包与校验

```bash
python tools/make_share_package.py --dry   # 防泄漏扫描 + 白名单校验
python tools/make_share_package.py          # 输出 share_<project>_YYYYMMDD.tar.gz
```
