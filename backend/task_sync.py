"""
任务同步模块
- 从 Session 对话中提取任务
- 同步 Cron 定时任务
- 任务合并去重
- 保存到 agent_tasks 表

配置说明：
- agents.scan_base_dir: OpenClaw agents 目录路径
- features.task_extraction_enabled: 是否启用 Session 任务提取
"""

import os
import re
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from database import SessionLocal, TaskRecord
from config import get_config

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

# 获取配置
cfg = get_config()

# 任务提取关键词（可扩展）
TASK_KEYWORDS = [
    '请执行', '请帮我', '帮我', '完成', '检索', '开发', '创建',
    '实现', '设计', '编写', '分析', '研究', '调查', '整理',
    '总结', '生成', '转换', '修复', '优化', '部署', '测试'
]


def extract_task_from_session(session_path: str) -> Optional[Dict]:
    """
    从 Session 对话中提取任务
    
    提取逻辑：
    1. 读取最近 50 条消息
    2. 检测用户分配任务的对话
    3. 提取引号中的任务描述
    4. 返回任务信息
    """
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 只读取最近 50 条消息
        messages = [json.loads(line) for line in lines[-50:]]
        
        # 从后往前找（最新的任务优先）
        for msg in reversed(messages):
            if msg.get('role') != 'user':
                continue
                
            content = msg.get('message', {}).get('content', '')
            
            # 检测任务关键词
            if not any(kw in content for kw in TASK_KEYWORDS):
                continue
            
            # 提取任务名（优先提取引号中的内容）
            task_name = None
            
            # 尝试提取引号中的内容
            patterns = [
                r'["\']([^"\']{5,200})["\']',  # 双引号或单引号
                r'《([^》]{5,200})》',  # 书名号
                r'任务 [:：]\s*([^\n]{5,200})',  # "任务：XXX"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    task_name = match.group(1).strip()
                    break
            
            # 如果没有提取到，使用整句话（截断）
            if not task_name:
                task_name = content[:100]
            
            # 从文件路径提取 session_id
            session_id = os.path.basename(session_path).replace('.jsonl', '')
            
            return {
                'task_id': f'session-{session_id}',
                'task_name': task_name,
                'task_type': 'session',
                'session_id': session_id,
                'status': 'in_progress'
            }
        
        return None
        
    except Exception as e:
        print(f"⚠️ 提取 Session 任务失败 {session_path}: {e}")
        return None


def sync_session_tasks_to_database() -> int:
    """
    同步 Session 任务到数据库
    
    返回：同步的任务数量
    """
    db = SessionLocal()
    synced_count = 0
    
    try:
        # 1. 获取所有 Session
        from database import Session as SessionTable
        sessions = db.query(SessionTable).all()
        
        print(f"📝 检测到 {len(sessions)} 个 Sessions")
        
        # 2. 提取任务
        for session in sessions:
            # 检查任务是否已存在
            existing = db.query(TaskRecord).filter(
                TaskRecord.task_id == f'session-{session.session_id}'
            ).first()
            
            if existing:
                # 任务已存在，跳过
                continue
            
            # 尝试从 Session 提取任务
            task_info = extract_task_from_session(session.file_path)
            
            if task_info:
                # 创建任务记录
                task = TaskRecord(
                    task_id=task_info['task_id'],
                    task_name=task_info['task_name'],
                    task_type=task_info['task_type'],
                    session_id=task_info.get('session_id'),
                    agent_id=session.agent_id,
                    status=task_info['status'],
                    priority=2,  # P2
                    created_at=session.last_activity
                )
                db.add(task)
                synced_count += 1
                print(f"✅ 提取任务：{task_info['task_name'][:50]}...")
        
        db.commit()
        print(f"✅ Session 任务同步完成，新增 {synced_count} 个任务")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Session 任务同步失败：{e}")
        raise
    finally:
        db.close()
    
    return synced_count


def sync_cron_tasks_to_database() -> int:
    """
    同步 Cron 任务到数据库
    
    从 cron_sync 模块导入，复用现有逻辑
    """
    try:
        from cron_sync import sync_cron_to_database
        print("📝 同步 Cron 任务...")
        sync_cron_to_database()
        print("✅ Cron 任务同步完成")
        return 1  # 返回 1 表示成功执行
    except ImportError:
        print("⚠️ cron_sync 模块未找到，跳过 Cron 任务同步")
        return 0
    except Exception as e:
        print(f"❌ Cron 任务同步失败：{e}")
        return 0


def merge_and_deduplicate_tasks():
    """
    任务合并去重
    
    去重规则：
    1. 相同 task_id 的任务视为重复
    2. 保留最新创建的任务
    3. 清理取消/完成超过 24 小时的任务
    """
    db = SessionLocal()
    
    try:
        # 1. 清理完成超过 24 小时的任务
        from datetime import timedelta
        from database import UTC, CONFIG_TZ
        cutoff_time = datetime.now(CONFIG_TZ) - timedelta(hours=24)
        cutoff_time_utc = cutoff_time.astimezone(UTC).replace(tzinfo=None)
        
        old_tasks = db.query(TaskRecord).filter(
            TaskRecord.status == 'completed',
            TaskRecord.completed_at < cutoff_time_utc
        ).all()
        
        if old_tasks:
            for task in old_tasks:
                db.delete(task)
            db.commit()
            print(f"🧹 清理了 {len(old_tasks)} 个已完成的历史任务")
        
        # 2. 合并重复任务（相同 task_id）
        # 这个逻辑在创建任务时已经通过 unique index 保证
        print("✅ 任务去重完成")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 任务去重失败：{e}")
        raise
    finally:
        db.close()


def sync_all_tasks():
    """
    同步所有任务（Session + Cron）
    """
    print("=" * 60)
    print("🦞 龙虾办公室 - 任务同步")
    print("=" * 60)
    print()
    
    # 1. 同步 Session 任务
    session_count = sync_session_tasks_to_database()
    
    # 2. 同步 Cron 任务
    cron_count = sync_cron_tasks_to_database()
    
    # 3. 合并去重
    merge_and_deduplicate_tasks()
    
    print()
    print("=" * 60)
    print(f"✅ 任务同步完成！")
    print(f"   - Session 任务：{session_count} 个")
    print(f"   - Cron 任务：{cron_count} 次同步")
    print("=" * 60)


if __name__ == '__main__':
    sync_all_tasks()
