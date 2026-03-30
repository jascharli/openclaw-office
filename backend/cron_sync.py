"""
Cron 任务同步模块
从 OpenClaw cron 系统同步任务状态到龙虾办公室数据库
"""

import subprocess
import json
import re
from datetime import datetime, timezone, timedelta
from database import SessionLocal, TaskRecord, AgentStatus

# 北京时区（UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))


def parse_owner_from_task_name(task_name: str) -> str:
    """从任务名称解析归属 agent"""
    # 优先匹配明确的 Agent 前缀
    match = re.match(r'^(dev-claw|work-claw|daughter|main|wife)\b', task_name, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    
    # 检查是否包含 Wife-Agent（任务名称中常见）
    if 'wife-agent' in task_name.lower():
        return 'wife'
    
    return None


def parse_last_run_time(last_run_str: str) -> bool:
    """
    解析 last_run 字符串，判断是否是今日执行
    返回 True 如果是今日执行，False 否则
    """
    if not last_run_str or last_run_str == '-':
        return False
    
    # 解析各种时间格式
    # "20h ago" - 20小时前
    # "4h ago" - 4小时前
    # "11m ago" - 11分钟前
    # "7d ago" - 7天前
    # "-" - 从未执行
    
    hours_match = re.match(r'(\d+)h ago', last_run_str)
    if hours_match:
        hours = int(hours_match.group(1))
        # 如果小于 24 小时，可能是今日执行
        if hours < 24:
            return True
    
    minutes_match = re.match(r'(\d+)m ago', last_run_str)
    if minutes_match:
        # 几分钟前肯定是今日
        return True
    
    return False


def get_cron_tasks():
    """获取 OpenClaw cron 任务列表"""
    try:
        result = subprocess.run(
            ['openclaw', 'cron', 'list'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Error running openclaw cron list: {result.stderr}")
            return []
        
        # 解析输出（表格格式）
        tasks = []
        lines = result.stdout.strip().split('\n')
        
        # 跳过表头
        for line in lines[1:]:
            # 找到第一个空格的位置，提取 ID
            first_space = line.find(' ')
            if first_space == -1:
                continue
            
            task_id = line[:first_space]
            remaining = line[first_space:].strip()
            
            # 找到 Schedule 列的开始位置（以 'cron' 或 'every' 开头）
            schedule_start = remaining.find(' cron ')
            if schedule_start == -1:
                schedule_start = remaining.find(' every ')
                if schedule_start == -1:
                    continue
            
            # 提取任务名称
            task_name = remaining[:schedule_start].strip()
            remaining_after_name = remaining[schedule_start:].strip()
            
            # 提取剩余列：Schedule | Next | Last | Status | Target | Agent ID | Model
            # 从后往前解析，因为后面的列格式更固定
            parts = remaining_after_name.split()
            
            # 解析状态、Agent ID 等
            status = 'unknown'
            agent_id = 'main'
            last_run = '-'
            
            # 从后往前找状态列
            for j in range(len(parts) - 1, -1, -1):
                if parts[j] in ['ok', 'error', 'idle', 'pending']:
                    status = parts[j]
                    # 找到状态后，确定其他列
                    if j - 1 >= 0:
                        # 处理 last_run 格式，如 "2h ago"
                        if j - 2 >= 0 and parts[j - 2].endswith('h') and parts[j - 1] == 'ago':
                            last_run = f"{parts[j - 2]} ago"
                        elif j - 2 >= 0 and parts[j - 2].endswith('m') and parts[j - 1] == 'ago':
                            last_run = f"{parts[j - 2]} ago"
                        elif j - 2 >= 0 and parts[j - 2].endswith('d') and parts[j - 1] == 'ago':
                            last_run = f"{parts[j - 2]} ago"
                        else:
                            last_run = parts[j - 1]
                    if j - 3 >= 0:
                        # Agent ID 通常在状态列前三位
                        potential_agent = parts[j - 3]
                        # 检查是否是有效的 Agent ID
                        if potential_agent in ['dev-claw', 'work-claw', 'daughter', 'main', 'wife']:
                            agent_id = potential_agent
                    break
            
            # 优先从任务名称解析归属 Agent
            owner_from_name = parse_owner_from_task_name(task_name)
            if owner_from_name:
                owner = owner_from_name
            else:
                # 如果任务名称没有解析出归属，使用 Agent ID 列
                owner = agent_id
                # 如果 Agent ID 为空或无效，根据关键词推断
                if owner == 'main' or owner == '-':
                    if any(kw in task_name.lower() for kw in ['日报', '天气', '新闻', '战况', '需求']):
                        owner = 'work-claw'
                    elif any(kw in task_name.lower() for kw in ['提醒', '日志', '心跳']):
                        if 'dev-claw' in task_name:
                            owner = 'dev-claw'
                        elif 'daughter' in task_name:
                            owner = 'daughter'
                        elif 'work-claw' in task_name:
                            owner = 'work-claw'
                        else:
                            owner = 'main'
                    else:
                        owner = 'main'
            
            # 确保任务名称包含归属 Agent 前缀
            if not parse_owner_from_task_name(task_name):
                task_name = f"{owner} {task_name}"
            
            tasks.append({
                'cron_id': task_id,
                'task_name': task_name,
                'owner_agent': owner,
                'status': status,
                'last_run': last_run,
            })
        
        return tasks
    
    except Exception as e:
        print(f"Error getting cron tasks: {e}")
        return []


def sync_cron_to_database():
    """同步 cron 任务到数据库"""
    db = SessionLocal()
    
    try:
        cron_tasks = get_cron_tasks()
        print(f"Found {len(cron_tasks)} cron tasks")
        
        # 今日开始时间（北京时间，不带时区）
        today_start = datetime.now(BEIJING_TZ).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
        
        for cron_task in cron_tasks:
            task_id = f"cron-{cron_task['cron_id']}"
            owner = cron_task['owner_agent'] or 'main'
            
            # 检查是否已存在（任何时间的）
            existing = db.query(TaskRecord).filter(
                TaskRecord.task_id == task_id
            ).first()
            
            # 判断是否是今日执行的任务
            last_run = cron_task['last_run']
            is_today_executed = False
            
            if last_run and last_run != '-':
                # 解析 last_run 时间
                hours_match = re.match(r'(\d+)h ago', last_run)
                if hours_match:
                    hours = int(hours_match.group(1))
                    # 如果小于 24 小时，说明是今日执行
                    if hours < 24:
                        is_today_executed = True
                
                minutes_match = re.match(r'(\d+)m ago', last_run)
                if minutes_match:
                    is_today_executed = True
            
            if existing:
                # 更新任务名称（确保使用带 agent 前缀的名称）
                existing.task_name = cron_task['task_name']
                
                # 判断是否应该更新为今日任务
                # 只有今日创建且今日执行的任务才标记为 completed
                is_today_task = existing.created_at >= today_start
                
                if is_today_task:
                    # 今日创建的任务，根据实际执行状态更新
                    if is_today_executed:
                        # 今日执行的任务
                        if cron_task['status'] == 'ok':
                            existing.status = 'completed'  # 今日已执行
                        elif cron_task['status'] == 'error':
                            existing.status = 'blocked'  # 执行失败
                        else:
                            existing.status = 'pending'  # 待执行
                    else:
                        # 今日创建但未执行（或昨日执行）的任务
                        # 检查任务是否应该今日执行
                        if cron_task['status'] == 'ok' and not is_today_executed:
                            # 状态是 ok 但不是今日执行的，说明是昨日执行
                            # 对于周期性任务，应该根据当前时间判断
                            existing.status = 'pending'  # 等待今日执行
                        elif cron_task['status'] == 'error':
                            existing.status = 'blocked'
                        else:
                            existing.status = 'pending'
                    
                    existing.updated_at = datetime.now(BEIJING_TZ).replace(tzinfo=None)
                    existing.agent_id = owner
                    print(f"  ✅ 更新今日 cron 任务：{cron_task['task_name']} ({existing.status}, agent={owner}, last={last_run})")
                else:
                    # 历史任务，不更新
                    print(f"  ⏭️  跳过历史 cron 任务：{cron_task['task_name']} (agent={owner}, last={last_run})")
            else:
                # 新增任务
                if cron_task['status'] == 'ok':
                    status = 'completed'
                elif cron_task['status'] == 'error':
                    status = 'blocked'
                else:
                    status = 'pending'
                
                new_task = TaskRecord(
                    task_id=task_id,
                    task_name=cron_task['task_name'],
                    agent_id=owner,
                    task_type='cron',
                    status=status,
                    created_at=datetime.now(BEIJING_TZ).replace(tzinfo=None),
                )
                db.add(new_task)
                print(f"  ✨ 新增 cron 任务：{cron_task['task_name']} ({status}, agent={owner})")
        
        db.commit()
        print(f"✅ Synced {len(cron_tasks)} cron tasks to database")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error syncing cron tasks: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    sync_cron_to_database()
