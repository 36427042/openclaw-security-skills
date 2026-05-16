#!/bin/bash
# 🥔 土豆·任务看板30分钟汇报
# stdout输出会被OpenClaw cron delivery推送到飞书

BOARD="$HOME/.openclaw/workspace/agents/tomato-agent/task_board.md"
if [ ! -f "$BOARD" ]; then
  echo "❌ 看板文件缺失"
  exit 1
fi

NOW=$(date '+%H:%M')
# 提取任务行（排除注释和空行）
TASKS=$(grep -E '^\| [A-Z].*\|' "$BOARD" | grep -v '^| #')

# 统计状态
SOLVED=$(echo "$TASKS" | grep -c '✅' )
INPROG=$(echo "$TASKS" | grep -c '🔴\|⛔' )
WAITING=$(echo "$TASKS" | grep -c '⏳\|📝\|🟡' )

echo "🥔 土豆·看板汇报 $NOW"
echo "━━━━━━━━━━━━━━"
echo "📊 ✅已解决:$SOLVED | 🔴待解决:$INPROG | ⏳等待:$WAITING"
echo ""
echo "🔴 待解决项:"
echo "$TASKS" | grep '🔴\|⛔' | while read line; do
  id=$(echo "$line" | grep -oE '[A-Z][0-9]+' | head -1)
  task=$(echo "$line" | cut -d'|' -f3 | xargs)
  desc=$(echo "$line" | cut -d'|' -f6 | xargs | cut -c1-60)
  echo "  $id $task → $desc"
done

echo ""
echo "⏳ 等待中:"
echo "$TASKS" | grep '⏳\|📝\|🟡' | head -3 | while read line; do
  id=$(echo "$line" | grep -oE '[A-Z][0-9]+' | head -1)
  task=$(echo "$line" | cut -d'|' -f3 | xargs)
  echo "  $id $task"
done

echo ""
echo "💡 下次汇报: $(date -v+30M '+%H:%M')"
