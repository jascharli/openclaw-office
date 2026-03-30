#!/bin/bash

# 龙虾办公室安装脚本

set -e

echo "🦞 正在安装龙虾办公室..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装"
    exit 1
fi

# 安装后端依赖
echo "📦 安装后端依赖..."
cd backend
pip3 install -r requirements.txt
cd ..

# 创建配置文件
if [ ! -f "config.json" ]; then
    echo "📝 创建配置文件..."
    cp config.example.json config.json
    echo "💡 提示：编辑 config.json 自定义配置"
fi

# 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
echo "🦞 启动龙虾办公室..."

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
echo "✅ 龙虾办公室已启动！"
echo ""
echo "📍 访问地址:"
echo "   前端页面：http://localhost:5173"
echo "   API 文档：http://localhost:8000/docs"
echo "   健康检查：http://localhost:8000/health"
echo ""
echo "🛑 停止服务：kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 保存 PID
echo "$BACKEND_PID" > /tmp/lobster_backend.pid
echo "$FRONTEND_PID" > /tmp/lobster_frontend.pid

# 等待
wait
EOF

chmod +x start.sh

# 创建停止脚本
cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 停止龙虾办公室..."

# 停止前端
if [ -f /tmp/lobster_frontend.pid ]; then
    kill $(cat /tmp/lobster_frontend.pid) 2>/dev/null || true
    rm /tmp/lobster_frontend.pid
fi

# 停止后端
if [ -f /tmp/lobster_backend.pid ]; then
    kill $(cat /tmp/lobster_backend.pid) 2>/dev/null || true
    rm /tmp/lobster_backend.pid
fi

# 查找并终止残留进程
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "http.server.*5173" 2>/dev/null || true

echo "✅ 已停止龙虾办公室"
EOF

chmod +x stop.sh

echo ""
echo "✅ 安装完成！"
echo ""
echo "📖 使用说明:"
echo "   1. 编辑 config.json 自定义配置（可选）"
echo "   2. 运行 ./start.sh 启动服务"
echo "   3. 访问 http://localhost:5173"
echo "   4. 运行 ./stop.sh 停止服务"
echo ""
echo "📄 查看文档：cat README.md"
echo ""
