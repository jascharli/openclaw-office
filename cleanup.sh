#!/bin/bash

# 龙虾办公室 - 项目清理脚本
# 用于发布前清理临时文件和缓存

set -e

echo "🧹 开始清理龙虾办公室项目..."

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 1. 清理 Python 缓存
echo "📦 清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true

# 2. 清理测试缓存
echo "🧪 清理测试缓存..."
rm -rf test/.pytest_cache 2>/dev/null || true
rm -rf .pytest_cache 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# 3. 清理临时 PID 文件
echo "🗑️  清理临时文件..."
rm -f /tmp/lobster_backend.pid 2>/dev/null || true
rm -f /tmp/lobster_frontend.pid 2>/dev/null || true
rm -f /tmp/lobster_backend.port 2>/dev/null || true
rm -f /tmp/lobster_frontend.port 2>/dev/null || true

# 4. 清理日志文件（保留备份）
echo "📝 清理日志文件..."
if [ -d "backend/logs" ]; then
    echo "   发现日志目录，是否清理？(y/N)"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        rm -rf backend/logs/* 2>/dev/null || true
        echo "   日志已清理"
    else
        echo "   保留日志文件"
    fi
fi

# 5. 询问是否清理数据库
echo ""
echo "🗄️  关于数据库文件 (backend/lobster_office.db):"
echo "   - 如果是发布，建议保留作为示例数据库"
echo "   - 如果是开发清理，可以删除"
echo ""
echo "   是否保留数据库文件？(Y/n)"
read -r answer
if [ "$answer" = "n" ] || [ "$answer" = "N" ]; then
    if [ -f "backend/lobster_office.db" ]; then
        echo "   备份数据库..."
        cp backend/lobster_office.db backend/lobster_office.db.backup
        echo "   已备份为: backend/lobster_office.db.backup"
        rm -f backend/lobster_office.db
        echo "   数据库已删除"
    fi
else
    echo "   保留数据库文件"
fi

# 6. 检查配置文件
echo ""
echo "⚙️  检查配置文件..."
if [ -f "config.json" ]; then
    echo "   发现 config.json"
    echo "   建议：确保 config.json 不包含敏感信息"
    echo "   发布时应该使用 config.example.json 作为模板"
fi

if [ -f ".env" ]; then
    echo "   发现 .env 文件"
    echo "   建议：.env 文件不应提交到 Git"
    echo "   应该使用 .env.example 作为模板"
fi

# 7. 显示清理结果
echo ""
echo "✅ 清理完成！"
echo ""
echo "📊 清理统计:"
echo "   - Python 缓存: 已清理"
echo "   - 测试缓存: 已清理"
echo "   - 临时文件: 已清理"
echo ""
echo "🚀 项目已准备好发布！"
echo ""
echo "下一步操作:"
echo "   1. 检查 git status"
echo "   2. 提交更改"
echo "   3. 推送到 GitHub"
echo "   4. 创建 Release"
echo ""
