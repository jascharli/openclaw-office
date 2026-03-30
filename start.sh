#!/bin/bash

# OpenClaw 办公室启动脚本
# 支持前台/后台运行模式

set -e

# 默认前台运行，加 -d 参数后台运行
DAEMON_MODE=false

while getopts "d" opt; do
  case $opt in
    d)
      DAEMON_MODE=true
      ;;
    \?)
      echo "用法: $0 [-d]"
      echo "  -d  后台运行模式"
      exit 1
      ;;
  esac
done

echo "🦞 启动 OpenClaw 办公室..."

# 检查是否已在运行
if [ -f /tmp/openclaw_backend.pid ] && kill -0 $(cat /tmp/openclaw_backend.pid) 2>/dev/null; then
    echo "⚠️  服务已在运行中！"
    echo "   前端: http://localhost:5173"
    echo "   停止服务: ./stop.sh"
    exit 1
fi

# 启动后端
echo "🚀 启动后端 API (端口 8000)..."
cd backend
if [ "$DAEMON_MODE" = true ]; then
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
else
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
fi
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "🚀 启动前端页面 (端口 5173)..."
cd frontend
if [ "$DAEMON_MODE" = true ]; then
    nohup python3 -m http.server 5173 --bind 0.0.0.0 > ../frontend.log 2>&1 &
else
    python3 -m http.server 5173 --bind 0.0.0.0 &
fi
FRONTEND_PID=$!
cd ..

# 保存 PID
echo "$BACKEND_PID" > /tmp/openclaw_backend.pid
echo "$FRONTEND_PID" > /tmp/openclaw_frontend.pid

echo ""
echo "✅ OpenClaw 办公室已启动！"
echo ""
echo "📍 访问地址:"
echo "   前端页面：http://localhost:5173"
echo "   局域网访问：http://$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -1):5173"
echo "   API 文档：http://localhost:8000/docs"
echo "   健康检查：http://localhost:8000/health"
echo ""

if [ "$DAEMON_MODE" = true ]; then
    echo "📝 后台运行模式"
    echo "   日志文件: backend.log, frontend.log"
    echo "   停止服务: ./stop.sh"
    echo ""
else
    echo "🛑 停止服务：kill $BACKEND_PID $FRONTEND_PID"
    echo "   或运行: ./stop.sh"
    echo ""
    # 前台运行，等待进程结束
    wait
fi
