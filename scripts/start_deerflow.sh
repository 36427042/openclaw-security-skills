#!/bin/bash
# DeerFlow 启动脚本
DEERFLOW_DIR="$HOME/.openclaw/deerflow-official/backend"
VENV="$DEERFLOW_DIR/.venv"

echo "🚀 启动 DeerFlow Gateway (port 8001)..."
cd "$DEERFLOW_DIR"
$VENV/bin/uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --no-reload &
echo $! > /tmp/deerflow.pid
echo "✅ DeerFlow PID: $(cat /tmp/deerflow.pid)"
sleep 2
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ DeerFlow 运行中: http://localhost:8001"
else
    echo "⚠️ 启动可能失败，检查日志"
fi
