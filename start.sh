#!/bin/bash

# 龙虾办公室启动脚本 - 支持动态端口

set -e

echo "🦞 启动龙虾办公室..."

# 进入项目目录
cd "$(dirname "$0")"

# 1. 加载 .env 文件（如果存在）
if [ -f ".env" ]; then
    echo "✅ 加载 .env 配置文件..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# 读取配置
BACKEND_PORT=${LOBSTER_BACKEND_PORT:-8000}
FRONTEND_PORT=${LOBSTER_FRONTEND_PORT:-5173}
CONFIG_FILE="./backend/config.json"

# 1. 优先使用环境变量
if [ -n "$LOBSTER_BACKEND_PORT" ]; then
    BACKEND_PORT=$LOBSTER_BACKEND_PORT
    echo "✅ 使用环境变量端口：$BACKEND_PORT"
elif [ -f "$CONFIG_FILE" ]; then
    # 2. 从配置文件读取（如果有 port 字段）
    CONFIG_PORT=$(cat "$CONFIG_FILE" | grep -o '"port"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)
    if [ -n "$CONFIG_PORT" ]; then
        BACKEND_PORT=$CONFIG_PORT
        echo "✅ 从配置文件读取端口：$BACKEND_PORT"
    fi
fi

# 确保端口有默认值
if [ -z "$BACKEND_PORT" ]; then
    BACKEND_PORT=8000
    echo "💡 使用默认端口：$BACKEND_PORT"
fi

# 3. 检查端口是否可用，如果不可用则自动查找
echo "🔍 检查端口 $BACKEND_PORT 是否可用..."
if command -v lsof &> /dev/null; then
    if lsof -i :$BACKEND_PORT &>/dev/null; then
        echo "⚠️  端口 $BACKEND_PORT 已被占用，正在查找可用端口..."
        for port in $(seq $BACKEND_PORT 8100); do
            if ! lsof -i :$port &>/dev/null; then
                BACKEND_PORT=$port
                echo "✅ 找到可用端口：$BACKEND_PORT"
                break
            fi
        done
    fi
else
    # 使用 nc 检查
    if nc -z localhost $BACKEND_PORT 2>/dev/null; then
        echo "⚠️  端口 $BACKEND_PORT 已被占用，正在查找可用端口..."
        for port in $(seq $BACKEND_PORT 8100); do
            if ! nc -z localhost $port 2>/dev/null; then
                BACKEND_PORT=$port
                echo "✅ 找到可用端口：$BACKEND_PORT"
                break
            fi
        done
    fi
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 进入后端目录
cd backend

# 检查依赖
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "📦 安装依赖..."
    pip3 install -r requirements.txt
fi

# 启动后端（使用确定的端口）
echo "🚀 启动后端 API (端口 $BACKEND_PORT)..."
python3 -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 3

# 检查后端是否正常启动
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ 后端启动失败"
    exit 1
fi

# 更新前端配置
echo "📝 更新前端配置..."
cd ../frontend

# 生成前端配置文件（自动检测 hostname，支持局域网访问）
cat > config.js << EOF
// 龙虾办公室前端配置 - 自动生成
// 自动使用当前页面 hostname 连接后端，支持局域网访问
// 由 start.sh 自动生成，每次启动更新
(function() {
  const hostname = window.location.hostname;
  const port = $BACKEND_PORT;
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  window.LOBSTER_CONFIG = {
    API_BASE: \`\${protocol}//\${hostname}:\${port}\`,
    WS_URL: \`\${wsProtocol}//\${hostname}:\${port}/ws\`,
    BACKEND_PORT: port,
    FRONTEND_PORT: $FRONTEND_PORT
  };
})();
EOF

echo "✅ 前端配置已生成（自动适配当前访问地址，支持局域网）"

# 启动前端（绑定所有网络接口）
echo "🚀 启动前端页面 (端口 $FRONTEND_PORT)..."
cd ..
python3 -m http.server $FRONTEND_PORT --bind 0.0.0.0 --directory frontend &
FRONTEND_PID=$!

echo ""
echo "✅ 龙虾办公室已启动！"
echo ""
echo "📍 访问地址:"
echo "   前端页面：http://localhost:$FRONTEND_PORT"
echo "   API 文档：http://localhost:$BACKEND_PORT/docs"
echo "   健康检查：http://localhost:$BACKEND_PORT/health"
echo ""
echo "🔧 配置信息:"
echo "   后端端口：$BACKEND_PORT"
echo "   前端端口：$FRONTEND_PORT"
echo ""
echo "🛑 停止服务：kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 保存 PID 和端口信息
echo "$BACKEND_PID" > /tmp/lobster_backend.pid
echo "$FRONTEND_PID" > /tmp/lobster_frontend.pid
echo "$BACKEND_PORT" > /tmp/lobster_backend.port
echo "$FRONTEND_PORT" > /tmp/lobster_frontend.port

# 等待
wait
