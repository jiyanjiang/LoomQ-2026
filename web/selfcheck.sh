#!/bin/bash
# LoomQ Web 自检流程 v2
# 用途：启动服务 + playwright 自动化检查所有视图的功能与一致性
# 用法：bash web/selfcheck.sh
# 检查项：
#   0. 术语拼写黑名单（防"用户笔误被一直带着"——全站 grep 历史错误变体）
#   1. 服务可达（HTTP 200）
#   2. 各视图切换无 JS 错误
#   3. 测量按钮文字统一（标准件 = "测量"）
#   4. 布洛赫球/课程/H门 功能点击无错误

set -e
cd "$(dirname "$0")/.."

# Python 解释器（词典 CLI 用）
PY3=${LOOMQ_PY3:-/opt/homebrew/bin/python3.12}
[ -x "$PY3" ] || PY3=$(command -v python3)

echo "=== [0/5] 术语拼写黑名单检查（从词典 aliases 动态生成）==="
# 黑名单 = web/qc_dict.py 各词条 aliases 字段（历史错误变体，单一数据源）
# 新增术语错误时，只需在词典词条 aliases 里登记，此处自动生效
# 排除：词典中"勿写"防错说明行、__pycache__
# --aliases 输出一行一个，用 while read 逐行读（避免按空白分词，别名可能含空格）
TERM_FAIL=0
while IFS= read -r term; do
  [ -z "$term" ] && continue
  HITS=$(grep -rn "$term" --include="*.py" --include="*.js" --include="*.html" --include="*.css" --include="*.md" --include="*.yaml" --include="*.json" . 2>/dev/null \
    | grep -v "node_modules\|.playwright-cli\|__pycache__\|\.pyc" \
    | grep -v "勿写\|勿写：" \
    | grep -v "web/qc_dict.py\|LOG.md" \
    | head -3)
  if [ -n "$HITS" ]; then
    echo "✗ 发现错误拼写 [$term]:"
    echo "$HITS"
    TERM_FAIL=1
  fi
done < <("$PY3" web/qc_dict.py --aliases 2>/dev/null || echo "")
if [ "$TERM_FAIL" -eq 0 ]; then echo "✓ 术语拼写全部正确"; else echo "✗ 术语拼写有误，必须修正后再提交！"; fi

echo "=== [1/5] 游戏可胜性自检（袜子 + 施温格积木）==="
if "$PY3" web/selfcheck_socks.py && "$PY3" web/selfcheck_schwinger.py; then
  echo "✓ 游戏必可胜（袜子配对 + 施温格积木）"
else
  echo "✗ 游戏存在无法胜利的牌局/无解关卡！"; exit 1
fi

echo "=== [2/5] 检查服务可达 ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:5011/ || { echo "服务未启动，先启动"; bash web/run_web.sh; }

PCLI=$(command -v playwright-cli)
if [ -z "$PCLI" ]; then echo "✗ 无 playwright-cli，跳过浏览器自检"; exit 0; fi

echo "=== [3/5] 打开页面 ==="
$PCLI close >/dev/null 2>&1 || true
sleep 1
$PCLI open "http://127.0.0.1:5011/?sc=$(date +%s)" >/dev/null 2>&1
sleep 3

echo "=== [4/5] 测量按钮一致性检查 ==="
# 布洛赫球视图（playwright-cli eval 返回 "### Result" + 值 格式，用 awk 取最后一行）
$PCLI eval "document.querySelector('[data-view=bloch]').click()" >/dev/null 2>&1
sleep 1
get_eval() {
  # 输出格式：### Result\n"值"\n### Ran...\n```js...——取 Result 后第一行，去引号
  $PCLI eval "$1" 2>/dev/null | sed -n '/### Result/,/### Ran/p' | sed -n '2p' | tr -d '"'
}
BLOCH_BTN1=$(get_eval "document.getElementById('bloch-measure').textContent")
BLOCH_BTN2=$(get_eval "document.getElementById('bloch-measure-5000').textContent")
echo "布洛赫球测量按钮: [$BLOCH_BTN1] / [$BLOCH_BTN2]"
if [[ "$BLOCH_BTN1" == *"测量"* ]]; then echo "✓ 按钮1 含'测量'"; else echo "✗ 按钮1 未含'测量'"; fi
if [[ "$BLOCH_BTN2" == *"测量"* ]]; then echo "✓ 按钮2 含'测量'"; else echo "✗ 按钮2 未含'测量'"; fi

echo "=== [5/5] 各视图点击无错误 ==="
for view in library composer tutorial help settings; do
  $PCLI eval "document.querySelector('[data-view=$view]').click()" >/dev/null 2>&1
  sleep 1
done
LATEST=$(ls -t .playwright-cli/console-*.log 2>/dev/null | head -1)
ERRS=$(grep -icE "typeerror|is not defined|referenceerror" "$LATEST" 2>/dev/null || echo 0)
# grep -c 可能输出多行，取数字
ERRS=$(echo "$ERRS" | grep -oE "[0-9]+" | head -1)
echo "最新 console 错误数: $ERRS"
if [ "${ERRS:-0}" -eq 0 ] 2>/dev/null; then echo "✓ 无 JS 错误"; else echo "✗ 有错误，见 $LATEST"; fi

echo "=== 自检完成 ==="
