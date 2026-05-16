#!/bin/bash
# 每30分钟记忆存档脚本 — 土豆+6伙伴+Hermes

DATE=$(date '+%Y-%m-%d')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
STAMP=$(date '+%Y%m%d-%H%M')
AGENTS_DIR="$HOME/.openclaw/workspace/agents"
ARCHIVE_DIR="$HOME/.openclaw/memory_archives"
SCRIPTS_DIR="$HOME/.openclaw/workspace/scripts"

mkdir -p "$ARCHIVE_DIR/memory" "$ARCHIVE_DIR/hermes" 2>/dev/null || true

# 1. 土豆记忆检查点（仅追加存档标记）
MEMO_FILE="$AGENTS_DIR/tomato-agent/memory/$DATE.md"
{
  echo ""
  echo "---"
  echo "## ⏰ 自动存档 $TIMESTAMP"
  echo "- Hermes: 运行中"
  echo "- 6伙伴: 保活中"
  echo "- DeerFlow: 运行中"
  echo "- EvoMap: 离线(待质押)"
  echo ""
} >> "$MEMO_FILE" 2>/dev/null || true

# 2. 6伙伴MEMORY.md备份
for agent in booster-agent corn-agent lettuce-agent bittergourd-agent carrot-agent pea-agent; do
  src="$AGENTS_DIR/$agent/MEMORY.md"
  if [ -f "$src" ]; then
    cp "$src" "$ARCHIVE_DIR/memory/${agent}_${STAMP}.md" 2>/dev/null || true
  fi
done

# 3. 6伙伴daily memory轻量检查点
for agent in booster-agent corn-agent lettuce-agent bittergourd-agent carrot-agent pea-agent; do
  daily_file="$AGENTS_DIR/$agent/memory/$DATE.md"
  mkdir -p "$(dirname "$daily_file")" 2>/dev/null || true
  echo "### ⏰ $TIMESTAMP 存档" >> "$daily_file" 2>/dev/null || true
done

# 4. Hermes data/归档
if [ -d "$SCRIPTS_DIR/data" ]; then
  tar -czf "$ARCHIVE_DIR/hermes/hermes_data_${STAMP}.tar.gz" -C "$SCRIPTS_DIR" data/ 2>/dev/null || true
fi

# 5. 备份清理（⚠️ 仅清理Hermes旧tar.gz，永不清理memory备份）
# 天赐铁律：MEMORY.md永不清理、只增不减 — 2026-05-13
archive_cleanup_hermes() {
  local dir="$1" pattern="$2" keep="$3"
  local count
  count=$(find "$dir" -name "$pattern" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$count" -gt "$keep" ]; then
    local del=$((count - keep))
    find "$dir" -name "$pattern" -type f -print0 | sort -z | perl -0ne "print if \$i++ < $del" | xargs -0 rm -f 2>/dev/null || true
  fi
}
archive_cleanup_hermes "$ARCHIVE_DIR/hermes" "*.tar.gz" 50

echo "[$TIMESTAMP] ✅ 记忆存档完成"
