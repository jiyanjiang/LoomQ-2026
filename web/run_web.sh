#!/bin/bash
# LoomQ Web 工作台启动脚本
# 用法：bash web/run_web.sh
# 端口：5011（LoomQ Web；5001=loomsci、5005=STOP、5010=文档展示）
#
# 关键（macOS 26 实测）：
#   1. DYLD_LIBRARY_PATH 必须用 export 显式导出后启动（`VAR=val nohup cmd` 前缀
#      赋值在此环境不传递，进程会缺 DYLD 导致 spinqit 加载失败）
#   2. 用 & + disown 而非 nohup（行为更可靠）

set -e
cd "$(dirname "$0")/.."

lsof -ti :5011 | xargs kill -9 2>/dev/null || true
sleep 1

export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib:$HOME/.venvs/loomq310/lib/python3.10/site-packages/spinqit"

echo "启动 LoomQ Web: http://127.0.0.1:5011"
"$HOME/.venvs/loomq310/bin/python" web/app.py > /tmp/loomq_web.log 2>&1 &
disown
sleep 2
curl -s -o /dev/null -w "状态: HTTP %{http_code}\n" http://127.0.0.1:5011/ || echo "启动失败，见 /tmp/loomq_web.log"
