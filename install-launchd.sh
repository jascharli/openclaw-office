#!/bin/bash

# 龙虾办公室 - launchd 服务安装脚本

set -e

echo "🦞 安装龙虾办公室 launchd 服务..."

# 创建日志目录
mkdir -p /Users/alisa/.openclaw/workspace/projects/openclaw-office/logs

# 停止已存在的服务（如果有）
launchctl unload ~/Library/LaunchAgents/com.lobster.office.plist 2>/dev/null || true

# 复制 plist 文件到 LaunchAgents 目录
cp /Users/alisa/.openclaw/workspace/projects/openclaw-office/com.lobster.office.plist ~/Library/LaunchAgents/

# 加载服务
launchctl load ~/Library/LaunchAgents/com.lobster.office.plist

echo ""
echo "✅ 龙虾办公室 launchd 服务已安装并启动！"
echo ""
echo "📍 服务管理命令："
echo "   查看状态: launchctl list | grep lobster"
echo "   停止服务: launchctl unload ~/Library/LaunchAgents/com.lobster.office.plist"
echo "   启动服务: launchctl load ~/Library/LaunchAgents/com.lobster.office.plist"
echo "   重启服务: launchctl kickstart -k gui/$(id -u)/com.lobster.office"
echo ""
echo "📝 日志文件位置："
echo "   标准输出: logs/launchd_stdout.log"
echo "   错误输出: logs/launchd_stderr.log"
echo "   后端日志: backend.log"
echo "   前端日志: frontend.log"
echo ""
echo "🔄 服务将在以下情况自动启动："
echo "   - 系统启动时"
echo "   - 服务崩溃时"
echo "   - 手动停止后重新加载时"
