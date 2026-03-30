"""
Session 同步模块
- 扫描所有 Agent 的 Sessions 目录
- 提取 Session 元数据
- 同步到 sessions 表

配置说明：
- agents.scan_mode: auto(自动扫描) | manual(手动配置)
- agents.scan_base_dir: OpenClaw agents 目录路径
- agents.custom_agents: 自定义 Agent 列表
"""

import os
import glob
import json
from datetime import datetime, timezone, timedelta
from database import SessionLocal, Session as SessionTable
from config import get_config
from typing import List, Dict, Optional

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

# 获取配置
cfg = get_config()


def get_session_id(file_path: str) -> str:
    """从文件路径提取 Session ID"""
    # 文件名：xxx-xxx-xxx.jsonl → xxx-xxx-xxx
    filename = os.path.basename(file_path)
    session_id = filename.replace('.jsonl', '')
    return session_id


def count_messages(file_path: str) -> int:
    """统计 Session 消息数量"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return len(lines)
    except Exception as e:
        print(f"⚠️ 读取文件失败 {file_path}: {e}")
        return 0


def get_last_activity(file_path: str) -> datetime:
    """获取 Session 最后活跃时间（北京时间）"""
    mtime = os.path.getmtime(file_path)
    # 文件修改时间是 UTC，转换为北京时间
    last_activity_utc = datetime.fromtimestamp(mtime, tz=BEIJING_TZ)
    # 去掉时区信息，存储为北京时间
    return last_activity_utc.replace(tzinfo=None)


def scan_sessions() -> List[Dict]:
    """扫描所有 Agent 的 Sessions（从配置动态获取 Agent 列表）"""
    sessions = []
    
    # 从配置获取 Agent 列表
    agents = cfg.get_agent_list()
    
    if not agents:
        print("⚠️ 未找到任何 Agent，请检查配置")
        return sessions
    
    print(f"📋 检测到 {len(agents)} 个 Agent: {[a['id'] for a in agents]}")
    
    for agent in agents:
        agent_id = agent['id']
        workspace = agent.get('workspace', '')
        
        # 优先使用 workspace 配置，否则使用默认路径
        if workspace:
            session_dir = os.path.join(workspace, 'sessions')
        else:
            scan_base_dir = cfg.get('agents.scan_base_dir', '~/.openclaw/agents')
            scan_base_dir = os.path.expanduser(scan_base_dir)
            session_dir = os.path.join(scan_base_dir, agent_id, 'sessions')
        
        if not os.path.exists(session_dir):
            print(f"⚠️ Session 目录不存在：{session_dir}")
            continue
        
        # 扫描所有 .jsonl 文件
        session_files = glob.glob(os.path.join(session_dir, '*.jsonl'))
        
        for session_file in session_files:
            session_id = get_session_id(session_file)
            last_activity = get_last_activity(session_file)
            message_count = count_messages(session_file)
            
            sessions.append({
                'session_id': session_id,
                'agent_id': agent_id,
                'file_path': session_file,
                'last_activity': last_activity,
                'message_count': message_count
            })
    
    return sessions


def sync_sessions_to_database():
    """同步 Sessions 到数据库"""
    db = SessionLocal()
    
    try:
        # 1. 扫描 Sessions
        print("📝 扫描 Sessions...")
        sessions = scan_sessions()
        print(f"✅ 扫描到 {len(sessions)} 个 Sessions")
        
        # 2. 同步到数据库
        print("💾 同步到数据库...")
        for session_data in sessions:
            # 检查是否已存在
            existing = db.query(SessionTable).filter(
                SessionTable.session_id == session_data['session_id']
            ).first()
            
            if existing:
                # 更新现有记录
                existing.file_path = session_data['file_path']
                existing.last_activity = session_data['last_activity']
                existing.message_count = session_data['message_count']
                existing.updated_at = datetime.now()
            else:
                # 创建新记录
                session = SessionTable(
                    session_id=session_data['session_id'],
                    agent_id=session_data['agent_id'],
                    file_path=session_data['file_path'],
                    last_activity=session_data['last_activity'],
                    message_count=session_data['message_count'],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(session)
        
        db.commit()
        print(f"✅ 同步完成，共 {len(sessions)} 个 Sessions")
        
        # 3. 统计信息
        total = db.query(SessionTable).count()
        print(f"📊 数据库中共有 {total} 个 Sessions")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 同步失败：{e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    print("=" * 60)
    print("🦞 龙虾办公室 - Session 同步")
    print("=" * 60)
    print()
    
    sync_sessions_to_database()
    
    print()
    print("=" * 60)
    print("✅ Session 同步完成！")
    print("=" * 60)
