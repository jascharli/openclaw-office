"""
Cron 任务同步模块
从 OpenClaw cron 系统同步任务状态到龙虾办公室数据库

Cron 任务状态判断逻辑：
    第一步：判断是否是今天的任务
        - Next 有值且是今天 -> 今天的任务
        - Next 无值，Last 有值且 < 24h -> 今天的任务
        - Next/Last 都无值 -> 根据 Status 判断（idle=paused, error=blocked, 其他=pending）

    第二步：判断是否已过执行时间
        - Next 已过 且 Status=ok -> completed
        - Next 已过 且 Status=error -> blocked
        - Next 未过 -> pending
        - 无 Next，用 Last 判断：今天内执行过 -> completed/error
        - 无 Next，用 Last 判断：超过24h未执行 -> pending

    第三步：周期性任务拆分
        - 每日 X:00 -> 不拆分
        - 每小时/每 X 小时 -> 拆分为多个任务实例（今日剩余次数）
"""

import os
import subprocess
import json
import re
from datetime import datetime, timezone, timedelta
from database import SessionLocal, TaskRecord, AgentStatus, to_utc, CONFIG_TZ, UTC


def parse_owner_from_task_name(task_name: str) -> str:
    """从任务名称解析归属 agent"""
    match = re.match(r'^(dev-claw|work-claw|daughter|main|wife)\b', task_name, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    
    if 'wife-agent' in task_name.lower():
        return 'wife'
    
    return None


def parse_schedule_info(schedule: str) -> dict:
    """
    解析 Schedule 字段，获取调度类型和执行时间信息
    
    返回：
        {
            'type': 'daily' | 'hourly' | 'interval' | 'unknown',
            'hour': int or None,  # 每日 X 点
            'interval_hours': int or None,  # 每 X 小时
            'is_daily_specific_time': bool  # 是否是每日特定时间
        }
    """
    result = {
        'type': 'unknown',
        'hour': None,
        'interval_hours': None,
        'is_daily_specific_time': False
    }
    
    if not schedule or schedule == '-':
        return result
    
    # 匹配每日 X 点：cron 0 23 * * *
    daily_match = re.match(r'cron\s+0\s+(\d+)\s+', schedule)
    if daily_match:
        result['type'] = 'daily'
        result['hour'] = int(daily_match.group(1))
        result['is_daily_specific_time'] = True
        return result
    
    # 匹配每 X 小时：every Xh 或 every X hour
    interval_match = re.match(r'every\s+(\d+)h', schedule, re.IGNORECASE)
    if interval_match:
        result['type'] = 'interval'
        result['interval_hours'] = int(interval_match.group(1))
        return result
    
    # 匹配每小时：every 1h 或 every hour
    hourly_match = re.match(r'every\s+1h?', schedule, re.IGNORECASE)
    if hourly_match:
        result['type'] = 'hourly'
        result['interval_hours'] = 1
        return result
    
    return result


def parse_next_time(next_str: str) -> dict:
    """
    解析 Next 字段，获取下次执行时间信息
    
    返回：
        {
            'is_today': bool,  # 是否是今天
            'is_past': bool,   # 是否已过执行时间
            'datetime': datetime or None,  # 解析后的 datetime
            'raw': str  # 原始字符串
        }
    """
    now = datetime.now(CONFIG_TZ)
    result = {
        'is_today': False,
        'is_past': False,
        'datetime': None,
        'raw': next_str
    }
    
    if not next_str or next_str == '-':
        return result
    
    # 匹配 "today 23:00" 格式
    today_match = re.match(r'today\s+(\d+):(\d+)', next_str)
    if today_match:
        hour = int(today_match.group(1))
        minute = int(today_match.group(2))
        target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        result['is_today'] = True
        result['is_past'] = target_dt < now
        result['datetime'] = target_dt
        return result
    
    # 匹配 "in 2h" 格式（未来 X 小时）
    in_hours_match = re.match(r'in\s+(\d+)h', next_str)
    if in_hours_match:
        hours = int(in_hours_match.group(1))
        result['is_today'] = True  # 即将执行，视为今天
        result['is_past'] = False
        result['datetime'] = now + timedelta(hours=hours)
        return result
    
    # 匹配 "in 30m" 格式（未来 X 分钟）
    in_minutes_match = re.match(r'in\s+(\d+)m', next_str)
    if in_minutes_match:
        minutes = int(in_minutes_match.group(1))
        result['is_today'] = True
        result['is_past'] = False
        result['datetime'] = now + timedelta(minutes=minutes)
        return result
    
    # 匹配 "tomorrow 23:00" 格式
    tomorrow_match = re.match(r'tomorrow\s+(\d+):(\d+)', next_str)
    if tomorrow_match:
        hour = int(tomorrow_match.group(1))
        minute = int(tomorrow_match.group(2))
        tomorrow_date = now.date() + timedelta(days=1)
        target_dt = datetime.combine(tomorrow_date, datetime.min.time()).replace(
            hour=hour, minute=minute
        )
        target_dt = CONFIG_TZ.localize(target_dt)
        result['is_today'] = False
        result['is_past'] = False
        result['datetime'] = target_dt
        return result
    
    return result


def parse_last_run_time(last_run_str: str) -> dict:
    """
    解析 Last 字段，判断上次执行时间和是否今日执行
    
    返回：
        {
            'is_today': bool,  # 是否今日执行（< 24h）
            'hours_ago': int or None,  # 多少小时前
            'minutes_ago': int or None,  # 多少分钟前
            'raw': str  # 原始字符串
        }
    """
    result = {
        'is_today': False,
        'hours_ago': None,
        'minutes_ago': None,
        'raw': last_run_str
    }
    
    if not last_run_str or last_run_str == '-':
        return result
    
    # 匹配 "20h ago" 格式
    hours_match = re.match(r'(\d+)h ago', last_run_str)
    if hours_match:
        hours = int(hours_match.group(1))
        result['hours_ago'] = hours
        if hours < 24:
            result['is_today'] = True
        return result
    
    # 匹配 "11m ago" 格式
    minutes_match = re.match(r'(\d+)m ago', last_run_str)
    if minutes_match:
        minutes = int(minutes_match.group(1))
        result['minutes_ago'] = minutes
        result['is_today'] = True  # 几分钟前肯定是今日
        return result
    
    # 匹配 "7d ago" 格式
    days_match = re.match(r'(\d+)d ago', last_run_str)
    if days_match:
        days = int(days_match.group(1))
        result['hours_ago'] = days * 24
        result['is_today'] = False
        return result
    
    return result


def determine_task_status(next_info: dict, last_info: dict, cron_status: str) -> str:
    """
    根据 Next、Last、Status 判断任务状态
    
    状态映射：
        - completed: 已完成
        - pending: 待执行
        - blocked: 执行失败
        - paused: 暂停
    
    判断逻辑：
        1. 如果 Next 有值：
            - 已过执行时间 -> 根据 cron_status 判断 completed/blocked
            - 未过执行时间 -> pending
        
        2. 如果 Next 无值，用 Last 判断：
            - 今日执行过 -> 根据 cron_status 判断
            - 未在今日执行 -> pending
        
        3. 如果 Next/Last 都无值：
            - idle -> paused
            - error -> blocked
            - 其他 -> pending
    """
    # 情况1：Next 有值
    if next_info['datetime'] is not None:
        if next_info['is_past']:
            # Next 已过，执行完成
            if cron_status == 'ok':
                return 'completed'
            elif cron_status == 'error':
                return 'blocked'
            else:
                return 'pending'
        else:
            # Next 未过，等待执行
            return 'pending'
    
    # 情况2：Next 无值，用 Last 判断
    if last_info['is_today']:
        # 今日执行过
        if cron_status == 'ok':
            return 'completed'
        elif cron_status == 'error':
            return 'blocked'
        else:
            return 'pending'
    elif last_info['hours_ago'] is not None:
        # 超过24小时未执行
        return 'pending'
    
    # 情况3：Next/Last 都无值
    if cron_status == 'idle':
        return 'paused'
    elif cron_status == 'error':
        return 'blocked'
    else:
        return 'pending'


def should_split_task(schedule_info: dict) -> bool:
    """
    判断任务是否需要拆分
    
    需要拆分的任务类型：
        - hourly: 每小时执行 -> 拆分为多个任务实例
        - interval: 每 X 小时执行 -> 拆分为多个任务实例
    
    不需要拆分：
        - daily: 每日特定时间 -> 单个任务
    """
    return schedule_info['type'] in ['hourly', 'interval']


def generate_split_tasks(cron_task: dict, schedule_info: dict) -> list:
    """
    拆分周期性任务为多个任务实例
    
    例如：每 2 小时执行，当前 18:00
    -> 生成 3 个任务实例：18:00(已完成), 20:00(待执行), 22:00(待执行)
    """
    now = datetime.now(CONFIG_TZ)
    interval_hours = schedule_info['interval_hours']
    
    tasks = []
    
    # 计算今日剩余的执行次数
    # 从 00:00 到 23:59，共 24 小时
    
    # 获取当前时间所在的小时区间
    current_hour = now.hour
    
    # 生成今日剩余的任务实例（只生成当前时间之后的小时）
    for hour in range(0, 24, interval_hours):
        # 跳过已过的小时（但保留当前小时，用于显示"即将执行"的任务）
        if hour < current_hour:
            continue

        target_dt = now.replace(hour=hour, minute=0, second=0, microsecond=0)

        task_instance = {
            'cron_id': f"{cron_task['cron_id']}-{hour}",
            'task_name': f"{cron_task['task_name']} ({hour}:00)",
            'owner_agent': cron_task['owner_agent'],
            'schedule': cron_task.get('schedule', '-'),
            'next_time': target_dt,
            'last_run': cron_task.get('last_run', '-'),
            'status': cron_task.get('status', 'unknown'),
            'target_datetime': target_dt,
            'is_past': target_dt < now,
        }
        tasks.append(task_instance)
    
    return tasks


def get_cron_tasks():
    """
    获取 OpenClaw cron 任务列表
    
    返回字段：
        - cron_id: 任务 ID
        - task_name: 任务名称
        - owner_agent: 归属 Agent
        - schedule: 调度规则
        - next: 下次执行时间（原始字符串）
        - last_run: 上次执行时间（原始字符串）
        - status: 执行状态（ok/error/idle）
    """
    try:
        # 打印环境变量信息
        print(f"DEBUG: os.environ['HOME'] = {os.environ.get('HOME')}")
        print(f"DEBUG: os.environ['USER'] = {os.environ.get('USER')}")
        print(f"DEBUG: os.environ['PATH'] = {os.environ.get('PATH', '')[:200]}")
        
        # 获取当前用户的主目录
        import pwd
        try:
            current_user = pwd.getpwuid(os.getuid()).pw_name
            print(f"DEBUG: 当前系统用户 = {current_user}")
        except:
            print(f"DEBUG: 无法获取系统用户")
        
        result = subprocess.run(
            ['openclaw', 'cron', 'list'],
            capture_output=True,
            text=True,
            timeout=60,  # 增加超时时间到 60 秒
            env=os.environ  # 显式传递当前环境变量
        )
        print(f"DEBUG: returncode = {result.returncode}")
        print(f"DEBUG: stdout 前 500 字符 = {result.stdout[:500] if result.stdout else 'None'}")
        if result.stderr:
            print(f"DEBUG: stderr = {result.stderr[:500]}")
        
        if result.returncode != 0:
            print(f"⚠️  Error running openclaw cron list: {result.stderr}")
            print(f"⚠️  将使用备用任务数据")
            return get_fallback_cron_tasks()
        
        tasks = []
        lines = result.stdout.strip().split('\n')
        
        # 跳过表头
        for line in lines[1:]:
            first_space = line.find(' ')
            if first_space == -1:
                continue
            
            task_id = line[:first_space]
            remaining = line[first_space:].strip()
            
            # 找到 Schedule 列的开始位置
            schedule_start = remaining.find(' cron ')
            if schedule_start == -1:
                schedule_start = remaining.find(' every ')
                if schedule_start == -1:
                    continue
            
            # 提取任务名称
            task_name = remaining[:schedule_start].strip()
            remaining_after_name = remaining[schedule_start:].strip()
            
            # 分割各列：Schedule | Next | Last | Status | Target | Agent ID | Model
            parts = remaining_after_name.split()
            
            # 解析各字段
            schedule = '-'
            next_time = '-'
            last_run = '-'
            status = 'unknown'
            agent_id = 'main'
            
            # 找到 Status 列的位置（从后往前）
            status_idx = -1
            for j in range(len(parts) - 1, -1, -1):
                if parts[j] in ['ok', 'error', 'idle', 'pending']:
                    status = parts[j]
                    status_idx = j
                    break
            
            # 根据 Status 位置推断其他列
            # 格式：Schedule | Next | Last | Status | Target | Agent ID | Model
            # 至少需要：Schedule, Next, Last
            
            # Schedule 通常在前3个部分
            if status_idx >= 3:
                schedule = ' '.join(parts[:status_idx-2])
                # Next 是 Schedule 后的下一个
                next_time = parts[status_idx-2] if status_idx-2 >= 0 else '-'
                # Last 是 Next 后的下一个
                last_run = parts[status_idx-1] if status_idx-1 >= 0 else '-'
            
            # 尝试解析 Agent ID
            if status_idx >= 0 and status_idx + 2 < len(parts):
                potential_agent = parts[status_idx + 2]
                if potential_agent in ['dev-claw', 'work-claw', 'daughter', 'main', 'wife']:
                    agent_id = potential_agent
            
            # 解析归属 Agent
            owner_from_name = parse_owner_from_task_name(task_name)
            if owner_from_name:
                owner = owner_from_name
            else:
                owner = agent_id
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
            
            # 解析 Schedule 信息
            schedule_info = parse_schedule_info(schedule)
            
            tasks.append({
                'cron_id': task_id,
                'task_name': task_name,
                'owner_agent': owner,
                'schedule': schedule,
                'schedule_info': schedule_info,
                'next': next_time,
                'last_run': last_run,
                'status': status,
            })
        
        # 如果没有任务，返回备用数据
        if not tasks:
            return get_fallback_cron_tasks()
        
        return tasks
    
    except Exception as e:
        print(f"Error getting cron tasks: {e}")
        return get_fallback_cron_tasks()


def get_fallback_cron_tasks():
    """
    当 OpenClaw Gateway 不可用时，返回空列表（不使用备用数据）
    """
    print("⚠️  OpenClaw Gateway 不可用，返回空任务列表")
    return []


def sync_cron_to_database():
    """
    同步 cron 任务到数据库
    
    处理逻辑：
        1. 获取所有 cron 任务
        2. 对于周期性任务（每小时/每X小时），拆分为多个任务实例
        3. 根据 Next/Last/Status 判断任务状态
        4. 同步到数据库
    """
    db = SessionLocal()
    
    try:
        cron_tasks = get_cron_tasks()
        print(f"Found {len(cron_tasks)} cron tasks from openclaw")
        if cron_tasks:
            print(f"First task: {cron_tasks[0]}")
        
        # 解析所有任务（包括拆分的任务实例）
        all_tasks_to_sync = []
        
        for cron_task in cron_tasks:
            # 检查是否需要拆分任务
            if should_split_task(cron_task['schedule_info']):
                # 拆分任务
                split_tasks = generate_split_tasks(cron_task, cron_task['schedule_info'])
                all_tasks_to_sync.extend(split_tasks)
                print(f"  📦 拆分任务 {cron_task['task_name']} 为 {len(split_tasks)} 个实例")
            else:
                # 不拆分，直接添加
                all_tasks_to_sync.append(cron_task)
        
        print(f"Total tasks to sync: {len(all_tasks_to_sync)}")
        
        for task in all_tasks_to_sync:
            task_id = f"cron-{task['cron_id']}"
            owner = task['owner_agent'] or 'main'
            
            # 解析 Next 和 Last 时间信息
            next_info = parse_next_time(task.get('next', '-'))
            last_info = parse_last_run_time(task.get('last_run', '-'))
            
            # 判断是否是今天的任务
            is_today_task = next_info['is_today'] or last_info['is_today']
            
            # 如果 Next/Last 都无值，根据 Status 判断
            if not is_today_task:
                if task.get('status') == 'idle':
                    is_today_task = True  # 暂停的任务也显示
                elif task.get('status') == 'error':
                    is_today_task = True  # 失败的任务也显示
                elif next_info['datetime'] is None and last_info['hours_ago'] is None:
                    # 没有任何时间信息，视为新任务
                    is_today_task = True
            
            # 判断任务状态
            cron_status = task.get('status', 'unknown')
            task_status = determine_task_status(next_info, last_info, cron_status)
            
            # 对于拆分后的任务，根据执行时间判断状态
            if 'target_datetime' in task:
                if task['is_past']:
                    if cron_status == 'ok':
                        task_status = 'completed'
                    elif cron_status == 'error':
                        task_status = 'blocked'
                    else:
                        task_status = 'completed'  # 已过时间且状态正常视为完成
                else:
                    task_status = 'pending'
            
            # 计算任务的计划执行时间（用于 created_at）
            # 优先使用任务的计划执行时间，而不是当前同步时间
            if 'target_datetime' in task:
                # 拆分后的任务（如每2小时），使用目标时间
                task_created_at = task['target_datetime'].astimezone(UTC).replace(tzinfo=None)
            elif next_info['datetime'] is not None and next_info['is_today']:
                # 有计划执行时间且是今天
                task_created_at = next_info['datetime'].astimezone(UTC).replace(tzinfo=None)
            else:
                # 没有计划时间，使用当前 UTC 时间
                task_created_at = datetime.utcnow()
            
            # 检查是否已存在
            existing = db.query(TaskRecord).filter(
                TaskRecord.task_id == task_id
            ).first()
            
            if existing:
                # 更新任务（使用计划执行时间作为 created_at）
                existing.task_name = task['task_name']
                existing.status = task_status
                existing.updated_at = datetime.utcnow()
                existing.created_at = task_created_at  # 使用计划执行时间
                existing.agent_id = owner
                print(f"  ✅ 更新任务：{task['task_name']} ({task_status}, next={task.get('next', '-')}, last={task.get('last_run', '-')})")
            else:
                # 新增任务（使用计划执行时间作为 created_at）
                new_task = TaskRecord(
                    task_id=task_id,
                    task_name=task['task_name'],
                    agent_id=owner,
                    task_type='cron',
                    status=task_status,
                    created_at=task_created_at,  # 使用计划执行时间
                )
                db.add(new_task)
                print(f"  ✨ 新增任务：{task['task_name']} ({task_status})")
        
        db.commit()
        print(f"✅ Synced {len(all_tasks_to_sync)} cron tasks to database")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error syncing cron tasks: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    sync_cron_to_database()
