# 龙虾办公室 - Docker 镜像
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY start.sh ./
COPY requirements.txt ./backend/

# 设置执行权限
RUN chmod +x start.sh

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# 创建数据目录
RUN mkdir -p /app/backend/data

# 暴露端口（环境变量可覆盖）
EXPOSE 8000 5173

# 环境变量
ENV LOBSTER_BACKEND_PORT=8000
ENV LOBSTER_FRONTEND_PORT=5173
ENV LOBSTER_HOST=0.0.0.0

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${LOBSTER_BACKEND_PORT}/health || exit 1

# 启动服务
CMD ["./start.sh"]
