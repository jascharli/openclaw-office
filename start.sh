#!/bin/bash
echo "🦞 启动 OpenClaw 办公室..."

# 启动后端
echo "🚀 启动后端 API (端口 8000)..."
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "🚀 启动前端页面 (端口 5173)..."
cd ../frontend
python3 -m http.server 5173 &
FRONTEND_PID=$!

echo ""
echo "✅ OpenClaw 办公室已启动！"
echo ""
echo "📍 访问地址:"
echo "   前端页面：http://localhost:5173"
echo "   API 文档：http://localhost:8000/docs"
echo "   健康检查：http://localhost:8000/health"
echo ""
echo "🛑 停止服务：kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 保存 PID
echo "$BACKEND_PID" > /tmp/openclaw_backend.pid
echo "$FRONTEND_PID" > /tmp/openclaw_frontend.pid

# 等待
wait
