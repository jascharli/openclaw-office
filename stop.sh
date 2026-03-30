#!/bin/bash

# 龙虾办公室停止脚本

echo "🛑 停止龙虾办公室..."

# 读取 PID 并停止
if [ -f /tmp/lobster_backend.pid ]; then
    kill $(cat /tmp/lobster_backend.pid) 2>/dev/null
    rm /tmp/lobster_backend.pid
fi

if [ -f /tmp/lobster_frontend.pid ]; then
    kill $(cat /tmp/lobster_frontend.pid) 2>/dev/null
    rm /tmp/lobster_frontend.pid
fi

# 额外清理
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "http.server 5173" 2>/dev/null

echo "✅ 已停止龙虾办公室"