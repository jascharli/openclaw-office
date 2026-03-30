#!/bin/bash
echo "🛑 停止 OpenClaw 办公室..."

# 停止前端
if [ -f /tmp/openclaw_frontend.pid ]; then
    kill $(cat /tmp/openclaw_frontend.pid) 2>/dev/null || true
    rm /tmp/openclaw_frontend.pid
fi

# 停止后端
if [ -f /tmp/openclaw_backend.pid ]; then
    kill $(cat /tmp/openclaw_backend.pid) 2>/dev/null || true
    rm /tmp/openclaw_backend.pid
fi

# 查找并终止残留进程
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "http.server.*5173" 2>/dev/null || true

echo "✅ 已停止 OpenClaw 办公室"
