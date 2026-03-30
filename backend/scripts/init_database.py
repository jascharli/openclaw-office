#!/usr/bin/env python3
"""
数据库初始化脚本
- 创建所有表
- 验证数据库连接
"""

import sys
import os

# 添加 backend 目录到 Python 路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from database import Base, engine, SessionLocal, AgentStatus, TaskRecord, Session
from datetime import datetime

def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("🦞 龙虾办公室 - 数据库初始化")
    print("=" * 60)
    print()
    
    # 1. 创建所有表
    print("📝 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    print()
    
    # 2. 验证数据库连接
    print("🔌 验证数据库连接...")
    try:
        db = SessionLocal()
        # 测试查询
        db.query(AgentStatus).count()
        db.query(TaskRecord).count()
        db.query(Session).count()
        print("✅ 数据库连接正常")
        print()
        
        # 3. 显示表信息
        print("📊 数据库表信息:")
        print(f"  - agent_status: Agent 状态表")
        print(f"  - task_records: 任务记录表")
        print(f"  - sessions: Sessions 表")
        print(f"  - token_logs: Token 日志表")
        print(f"  - reminder_logs: 督促记录表")
        print(f"  - task_handovers: 任务交接表")
        print()
        
        db.close()
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")
        return False
    
    print("=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
