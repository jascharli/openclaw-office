#!/bin/bash

# 龙虾办公室 - launchd 服务卸载脚本

echo "🦞 卸载龙虾办公室 launchd 服务..."

# 停止并卸载服务
launchctl unload ~/Library/LaunchAgents/com.lobster.office.plist 2>/dev/null || true

# 删除 plist 文件
rm -f ~/Library/LaunchAgents/com.lobster.office.plist

echo ""
echo "✅ 龙虾办公室 launchd 服务已卸载！"
echo ""
echo "⚠️  服务将不再自动启动，如需手动启动请运行："
echo "   ./start.sh"
