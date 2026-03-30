#!/bin/bash

# 查找可用端口脚本
# 用法：./find-available-port.sh [start_port] [end_port]

START_PORT=${1:-8000}
END_PORT=${2:-8100}

echo "🔍 在端口范围 $START_PORT-$END_PORT 中查找可用端口..."

for port in $(seq $START_PORT $END_PORT); do
    # 检查端口是否被占用
    if ! command -v lsof &> /dev/null; then
        # 使用 nc 检查
        if ! nc -z localhost $port 2>/dev/null; then
            echo $port
            exit 0
        fi
    else
        # 使用 lsof 检查
        if ! lsof -i :$port &>/dev/null; then
            echo $port
            exit 0
        fi
    fi
done

echo "❌ 未找到可用端口" >&2
exit 1
