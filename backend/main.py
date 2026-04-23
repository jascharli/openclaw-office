"""
OpenClaw 办公室 - FastAPI 主应用
提供 Agent 状态查询、任务管理、Token 统计等 API
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import json

from database import init_db, get_db, AgentStatus, TaskRecord, TokenLog, ReminderLog, TaskHandover, CollaborationGroup, RequestLog, to_local_time, to_utc, UTC, get_current_utc, CONFIG_TZ
from config import config, CONFIG_FILE
from handover_sync import create_handover_context, get_agent_sessions
from request_sync import sync_request_logs, get_hourly_stats, get_daily_stats, get_agent_comparison, identify_agent_from_session
from websocket import websocket_endpoint, manager, broadcast_agent_update, broadcast_reminder
from feishu_notify import send_reminder_notification, send_alert_notification
from scheduler import start_reminder_scheduler, stop_reminder_scheduler, start_data_sync_scheduler, stop_data_sync_scheduler, stop_scheduler, start_health_check_scheduler
from openclaw_sync import get_openclaw_agents
import asyncio

app = FastAPI(
    title="OpenClaw 办公室 API",
    description="AI 团队工作空间 - 上帝视角的实时监控和干预能力",
    version="1.0.0"
)

# CORS 配置（必须在路由定义之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境，生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 健康检查 ====================

@app.get("/")
def root():
    """根路径 - 健康检查"""
    return {
        "service": "OpenClaw 办公室 API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": to_local_time(datetime.now(UTC)).isoformat()
    }


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": to_local_time(datetime.now(UTC)).isoformat()}


@app.get("/api/v1/health/logs")
def get_health_logs(hours: int = 48, service: str = None):
    """获取健康检测日志"""
    from health_check import get_health_logs as fetch_health_logs
    logs = fetch_health_logs(hours=hours, service=service)
    return {"logs": logs, "total": len(logs)}


@app.post("/api/v1/health/check")
def trigger_health_check():
    """手动触发健康检测"""
    from health_check import perform_health_check
    try:
        result = perform_health_check()
        return {"success": True, "results": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.websocket("/ws")
async def websocket_router(websocket: WebSocket, client_id: str = "default"):
    """WebSocket 连接端点"""
    await websocket_endpoint(websocket, client_id)


@app.websocket("/ws/{client_id}")
async def websocket_router_with_id(websocket: WebSocket, client_id: str):
    """WebSocket 连接端点（带客户端 ID）"""
    await websocket_endpoint(websocket, client_id)


# ==================== Agent 状态查询 ====================

@app.get("/api/v1/agents/status")
def get_agents_status(db: Session = Depends(get_db)):
    """
    获取所有 Agent 的实时状态（直接调用 openclaw_sync 获取最新数据）
    返回三区域分类：idle(休闲区), conversing(对话区), working(办公区)
    """
    agents = get_openclaw_agents()

    result = {
        "agents": [],
        "summary": {
            "total": len(agents),
            "idle": 0,
            "conversing": 0,
            "working": 0
        }
    }

    for agent in agents:
        agent_data = {
            "agent_id": agent["agent_id"],
            "agent_name": agent["agent_name"],
            "status": agent["status"],
            "task_id": agent.get("task_id"),
            "task_name": agent.get("task_name"),
            "progress": agent.get("progress", 0.0),
            "elapsed_time": agent.get("elapsed_time", 0),
            "estimated_remaining": agent.get("estimated_remaining", 0),
            "token_used": agent.get("token_used", 0),
            "last_activity": agent.get("last_activity").isoformat() + "+08:00" if isinstance(agent.get("last_activity"), datetime) else (agent.get("last_activity") if agent.get("last_activity") else None)
        }
        result["agents"].append(agent_data)

        if agent["status"] == "idle":
            result["summary"]["idle"] += 1
        elif agent["status"] == "conversing":
            result["summary"]["conversing"] += 1
        elif agent["status"] == "working":
            result["summary"]["working"] += 1

    return result


# ==================== 任务管理 ====================

def parse_owner_from_task_name(task_name: str) -> str:
    """从任务名称解析归属 agent"""
    import re
    # 匹配 "work-claw 心跳"、"dev-claw 心跳"、"daughter 心跳" 等
    match = re.match(r'^(dev-claw|work-claw|daughter|main)\b', task_name, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def classify_task_type(task: TaskRecord) -> str:
    """
    分类任务类型
    
    规则:
    - 普通任务：手动创建的任务（task_id 不包含"cron-"）
    - Cron 任务：定时任务（task_id 包含"cron-"）
    - 一次性任务：项目/自动化任务（特殊标记或无周期性）
    
    返回:
    - "普通任务" | "Cron 任务" | "一次性任务"
    """
    task_id = task.task_id or ""
    task_name = task.task_name.lower()
    
    # Cron 任务：task_id 包含 "cron-"
    if task_id.startswith('cron-'):
        return 'Cron 任务'
    
    # 一次性任务：包含特定关键词或无周期性
    one_time_keywords = ['项目', '自动化', '临时', '特别', '紧急']
    if any(kw in task_name for kw in one_time_keywords):
        return '一次性任务'
    
    # 默认为普通任务
    return '普通任务'


@app.post("/api/v1/cron/sync")
def sync_cron_tasks():
    """手动触发 cron 任务同步"""
    from cron_sync import sync_cron_to_database
    try:
        sync_cron_to_database()
        return {"success": True, "message": "Cron tasks synced successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents/tasks")
def get_agent_tasks(db: Session = Depends(get_db)):
    """
    获取每个 Agent 的今日任务清单及完成情况
    返回格式：{ agent_id: { agent_name, tasks: [...], completed_count, total_count, task_type } }
    
    任务分类:
    - 普通任务：手动创建的任务，显示今日创建的
    - Cron 任务：定时任务，显示今日应执行的
    - 一次性任务：项目/自动化任务，显示今日创建或正在执行的
    
    过滤规则:
    1. ❌ 不显示每周 X 的任务（除非今日是周 X）
    2. ❌ 不显示每月 X 日的任务（除非今日是 X 日）
    """
    from datetime import datetime, timedelta
    
    # 获取当前北京时间
    now_local = datetime.now(CONFIG_TZ)
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # 转换为 UTC 时间（不带时区）
    today_start_utc = today_start.astimezone(UTC).replace(tzinfo=None)
    today_end_utc = today_end.astimezone(UTC).replace(tzinfo=None)
    
    # 从数据库读取今日任务（简化查询，获取所有任务）
    # 先获取所有任务，然后在Python中过滤
    all_tasks = db.query(TaskRecord).all()
    
    # 过滤出今日任务
    from datetime import date, datetime
    today = date.today()
    today_tasks = []
    
    for task in all_tasks:
        if task.created_at:
            task_date = task.created_at.date()
            if task_date == today:
                today_tasks.append(task)
    
    print(f"DEBUG: Today: {today}")
    print(f"DEBUG: Found {len(today_tasks)} tasks")
    for task in today_tasks:
        print(f"DEBUG: Task: {task.task_name}, Agent: {task.agent_id}, Date: {task.created_at.date()}")
    
    # 初始化 agent 结构
    agent_tasks = {
        "dev-claw": {
            "agent_id": "dev-claw",
            "agent_name": "dev-claw",
            "tasks": [],
            "completed_count": 0,
            "total_count": 0,
            "task_types": {
                "普通任务": 0,
                "Cron 任务": 0,
                "一次性任务": 0
            }
        },
        "work-claw": {
            "agent_id": "work-claw",
            "agent_name": "work-claw",
            "tasks": [],
            "completed_count": 0,
            "total_count": 0,
            "task_types": {
                "普通任务": 0,
                "Cron 任务": 0,
                "一次性任务": 0
            }
        },
        "main": {
            "agent_id": "main",
            "agent_name": "main",
            "tasks": [],
            "completed_count": 0,
            "total_count": 0,
            "task_types": {
                "普通任务": 0,
                "Cron 任务": 0,
                "一次性任务": 0
            }
        }
    }
    
    # 处理任务数据
    for task in today_tasks:
        # 过滤掉暂停的任务
        if task.status == "paused":
            continue
            
        agent_id = task.agent_id
        if agent_id not in agent_tasks:
            # 添加新的 agent
            agent_tasks[agent_id] = {
                "agent_id": agent_id,
                "agent_name": agent_id,
                "tasks": [],
                "completed_count": 0,
                "total_count": 0,
                "task_types": {
                    "普通任务": 0,
                    "Cron 任务": 0,
                    "一次性任务": 0
                }
            }
        
        # 分类任务类型
        task_type = classify_task_type(task)
        
        # 构建任务数据
        task_data = {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "status": task.status,
            "priority": task.priority,
            "created_at": to_local_time(task.created_at).isoformat() if task.created_at else None,
            "started_at": to_local_time(task.started_at).isoformat() if task.started_at else None,
            "completed_at": to_local_time(task.completed_at).isoformat() if task.completed_at else None,
            "token_used": task.token_used or 0
        }
        
        # 添加到 agent 的任务列表
        agent_tasks[agent_id]["tasks"].append(task_data)
        agent_tasks[agent_id]["total_count"] += 1
        agent_tasks[agent_id]["task_types"][task_type] += 1
        
        # 统计完成的任务
        if task.status == "completed":
            agent_tasks[agent_id]["completed_count"] += 1
    
    return agent_tasks


@app.get("/api/v1/agents/{agent_id}")
def get_agent_status(agent_id: str, db: Session = Depends(get_db)):
    """获取单个 Agent 的状态"""
    agent = db.query(AgentStatus).filter(AgentStatus.agent_id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "status": agent.status,
        "task_id": agent.task_id,
        "task_name": agent.task_name,
        "progress": agent.progress,
        "elapsed_time": agent.elapsed_time,
        "estimated_remaining": agent.estimated_remaining,
        "token_used": agent.token_used,
        # 转换为北京时间
        "last_activity": to_local_time(agent.last_activity).isoformat() if agent.last_activity else None
    }

@app.get("/api/v1/tasks")
def get_tasks(db: Session = Depends(get_db)):
    """
    获取任务队列 - 从数据库读取真实任务
    """
    result = {
        "in_progress": [],
        "pending": [],
        "blocked": [],
        "completed_today": []
    }
    
    # 从数据库读取任务
    tasks = db.query(TaskRecord).order_by(TaskRecord.created_at.desc()).all()
    
    for task in tasks:
        task_data = {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "agent_id": task.agent_id,
            "agent_name": task.agent_id,
            "status": task.status,
            "priority": task.priority,
            "progress": 1.0 if task.status == "completed" else 0.5
        }
        
        if task.status == "in_progress":
            result["in_progress"].append(task_data)
        elif task.status == "pending":
            result["pending"].append(task_data)
        elif task.status == "blocked":
            result["blocked"].append(task_data)
        elif task.status == "completed":
            result["completed_today"].append(task_data)
    
    return result


@app.post("/api/v1/tasks")
def create_task(task_data: dict, db: Session = Depends(get_db)):
    """创建新任务"""
    task = TaskRecord(**task_data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"success": True, "task_id": task.task_id}


# ==================== Token 统计 ====================

@app.get("/api/v1/tokens/stats")
def get_token_stats(
    period: str = "today",
    db: Session = Depends(get_db)
):
    """
    获取 Token 使用统计
    period: today, week, month, all
    """
    # 优先从 request_logs 聚合 token 数据（更准确）
    from sqlalchemy import func
    from datetime import timedelta
    
    # 获取当前北京时间
    now_local = datetime.now(CONFIG_TZ)
    
    # 根据周期计算时间范围（北京时间）
    if period == "today":
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = start_local + timedelta(days=1)
    elif period == "week":
        start_local = now_local - timedelta(days=now_local.weekday())
        start_local = start_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = start_local + timedelta(days=7)
    elif period == "month":
        start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_local.month == 12:
            end_local = start_local.replace(year=start_local.year+1, month=1, day=1)
        else:
            end_local = start_local.replace(month=start_local.month+1, day=1)
    else:  # all
        start_local = None
        end_local = None
    
    # 转换为 UTC 时间（不带时区）
    if start_local and end_local:
        start_utc = start_local.astimezone(UTC).replace(tzinfo=None)
        end_utc = end_local.astimezone(UTC).replace(tzinfo=None)
        
        query = db.query(
            RequestLog.agent_id,
            func.sum(RequestLog.tokens_total).label('total_tokens')
        ).filter(
            RequestLog.created_at >= start_utc,
            RequestLog.created_at < end_utc
        )
    else:
        query = db.query(
            RequestLog.agent_id,
            func.sum(RequestLog.tokens_total).label('total_tokens')
        )
    
    query = query.group_by(RequestLog.agent_id)
    results = query.all()
    
    # 统计
    total_used = sum(r.total_tokens or 0 for r in results)
    by_agent = {r.agent_id: (r.total_tokens or 0) for r in results}
    
    # 计算本月总消耗（用于返回）
    month_start = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_utc = month_start.astimezone(UTC).replace(tzinfo=None)
    if month_start.month == 12:
        month_end_utc = month_start.replace(year=month_start.year+1, month=1, day=1).astimezone(UTC).replace(tzinfo=None)
    else:
        month_end_utc = month_start.replace(month=month_start.month+1, day=1).astimezone(UTC).replace(tzinfo=None)
    
    monthly_query = db.query(
        func.sum(RequestLog.tokens_total).label('total_tokens')
    ).filter(
        RequestLog.created_at >= month_start_utc,
        RequestLog.created_at < month_end_utc
    )
    monthly_total = (monthly_query.scalar() or 0)
    
    # 预算（从配置读取）
    daily_budget = config.config.get('token_budget', {}).get('daily', 500000)
    monthly_budget = config.config.get('token_budget', {}).get('monthly', 10000000)
    
    budget = {
        "daily": daily_budget,
        "monthly": monthly_budget,
        "remaining_daily": max(0, daily_budget - total_used),
        "remaining_monthly": max(0, monthly_budget - monthly_total)
    }
    
    return {
        "period": period,
        "total_used": total_used,
        "monthly_total": monthly_total,
        "by_agent": [{"agent_id": k, "used": v} for k, v in by_agent.items()],
        "budget": budget
    }


@app.get("/api/v1/tokens/monthly-trend")
def get_monthly_token_trend(
    month: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取本月每日 Token 使用趋势
    - 按 provider 分组汇总
    - 按日期分组展示每日用量
    month: 月份（格式 YYYY-MM，默认当前月）
    """
    from sqlalchemy import func
    from datetime import timedelta
    from collections import defaultdict
    
    # 获取当前北京时间
    now_local = datetime.now(CONFIG_TZ)
    
    # 解析月份，计算起止时间
    if month:
        # 解析传入的月份
        try:
            start_local = datetime.strptime(month + '-01', '%Y-%m-%d').replace(tzinfo=CONFIG_TZ)
            # 计算下个月第一天
            if start_local.month == 12:
                end_local = start_local.replace(year=start_local.year+1, month=1, day=1)
            else:
                end_local = start_local.replace(month=start_local.month+1, day=1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    else:
        # 使用当前月份
        start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_local.month == 12:
            end_local = start_local.replace(year=start_local.year+1, month=1, day=1)
        else:
            end_local = start_local.replace(month=start_local.month+1, day=1)
    
    # 转换为 UTC 时间（不带时区）
    start_utc = start_local.astimezone(UTC).replace(tzinfo=None)
    end_utc = end_local.astimezone(UTC).replace(tzinfo=None)
    
    # 查询每日按服务商分组的 Token 数据
    query = db.query(
        RequestLog.created_at,
        RequestLog.provider,
        func.sum(RequestLog.tokens_total).label('total_tokens')
    ).filter(
        RequestLog.created_at >= start_utc,
        RequestLog.created_at < end_utc,
        RequestLog.provider.isnot(None),
        RequestLog.provider != ''
    ).group_by(
        RequestLog.created_at,
        RequestLog.provider
    ).order_by(
        RequestLog.created_at,
        RequestLog.provider
    ).all()
    
    # 按日期和服务商聚合数据
    daily_data = defaultdict(lambda: defaultdict(int))
    provider_totals = defaultdict(int)
    
    for row in query:
        # 将 UTC 时间转换为北京时间日期
        date_str = row.created_at.replace(tzinfo=UTC).astimezone(CONFIG_TZ).strftime('%Y-%m-%d')
        provider = row.provider or 'unknown'
        tokens = row.total_tokens or 0
        
        daily_data[date_str][provider] += tokens
        provider_totals[provider] += tokens
    
    # 构建每日数组（包含所有日期，即使某日无数据）
    daily = []
    current_date = start_local
    while current_date < end_local:
        date_str = current_date.strftime('%Y-%m-%d')
        day_providers = daily_data.get(date_str, {})
        day_total = sum(day_providers.values())
        
        daily.append({
            'date': date_str,
            'tokens': day_total,
            'by_provider': dict(day_providers) if day_providers else {}
        })
        
        current_date += timedelta(days=1)
    
    # 构建服务商汇总
    by_provider = [
        {'provider': provider, 'tokens': tokens}
        for provider, tokens in sorted(provider_totals.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # 计算总计
    total_tokens = sum(provider_totals.values())
    
    return {
        'month': start_local.strftime('%Y-%m'),
        'total_tokens': total_tokens,
        'by_provider': by_provider,
        'daily': daily
    }


@app.put("/api/v1/tokens/budget")
def update_token_budget(
    daily: Optional[int] = Body(None, description="日预算"),
    monthly: Optional[int] = Body(None, description="月预算"),
    db: Session = Depends(get_db)
):
    """
    更新 Token 预算配置
    - daily: 日预算数量（可选）
    - monthly: 月预算数量（可选）
    """
    import json
    
    # 读取当前配置
    current_config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
    
    # 更新预算配置
    if 'token_budget' not in current_config:
        current_config['token_budget'] = {}
    
    if daily is not None:
        current_config['token_budget']['daily'] = daily
        print(f"✅ 更新日预算 Token: {daily}")
    
    if monthly is not None:
        current_config['token_budget']['monthly'] = monthly
        print(f"✅ 更新月预算 Token: {monthly}")
    
    # 保存配置
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_config, f, indent=2, ensure_ascii=False)
    
    # 直接更新内存中的配置（不重新加载整个配置）
    if daily is not None:
        config.config['token_budget']['daily'] = daily
    if monthly is not None:
        config.config['token_budget']['monthly'] = monthly
    
    print(f"✅ 配置已更新（内存 + 文件）")
    
    # 返回新的预算配置
    return {
        "success": True,
        "budget": config.get_token_budget()
    }


# ==================== 督促功能 ====================

@app.post("/api/v1/reminders/send")
def send_reminder(
    agent_id: str,
    interval: int = 10,
    message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    发送督促消息
    agent_id: 目标 Agent
    interval: 督促间隔（分钟）
    message: 督促消息内容
    """
    # 获取 Agent 信息
    agent = db.query(AgentStatus).filter(AgentStatus.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # 记录督促日志
    reminder = ReminderLog(
        agent_id=agent_id,
        reminder_type="manual",
        reminder_interval=interval,
        response_status="pending",
        response_content=message
    )
    db.add(reminder)
    db.commit()
    
    # 发送飞书通知
    feishu_result = send_reminder_notification(
        agent_id=agent_id,
        agent_name=agent.agent_name or agent_id,
        task_name=agent.task_name or "未知任务",
        progress=agent.progress,
        elapsed_time=agent.elapsed_time,
        reminder_type="manual"
    )
    
    # 更新督促日志状态
    reminder.response_status = "sent" if feishu_result.get("success") else "failed"
    db.commit()
    
    # WebSocket 广播（简化处理，暂不广播）
    # TODO: 在异步上下文中广播
    
    return {
        "success": True,
        "reminder_id": reminder.id,
        "sent_at": to_local_time(datetime.now(UTC)).isoformat(),
        "feishu_result": feishu_result
    }


@app.get("/api/v1/reminders/history")
def get_reminder_history(
    agent_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取督促历史记录"""
    query = db.query(ReminderLog)
    if agent_id:
        query = query.filter(ReminderLog.agent_id == agent_id)
    
    reminders = query.order_by(ReminderLog.created_at.desc()).limit(limit).all()
    
    return {
        "reminders": [
            {
                "id": r.id,
                "agent_id": r.agent_id,
                "reminder_type": r.reminder_type,
                "reminder_interval": r.reminder_interval,
                "response_status": r.response_status,
                "created_at": to_local_time(r.created_at).isoformat()
            }
            for r in reminders
        ]
    }


# ==================== 任务交接管理 ====================

@app.post("/api/v1/handovers")
def create_handover(
    handover_data: dict,
    auto_extract: bool = True,  # 是否自动提取上下文
    db: Session = Depends(get_db)
):
    """创建任务交接"""
    import uuid
    
    # 自动提取上下文（如果请求）
    context_data = handover_data.get("context_data", {})
    if auto_extract and not context_data:
        handover_context = create_handover_context(
            handover_data["from_agent_id"],
            handover_data["to_agent_id"]
        )
        if not handover_context['error']:
            context_data = handover_context['context']
    
    handover = TaskHandover(
        handover_id=f"handover-{uuid.uuid4().hex[:8]}",
        task_id=handover_data["task_id"],
        task_name=handover_data["task_name"],
        from_agent_id=handover_data["from_agent_id"],
        from_agent_name=handover_data.get("from_agent_name", ""),
        to_agent_id=handover_data["to_agent_id"],
        to_agent_name=handover_data.get("to_agent_name", ""),
        handover_type=handover_data.get("handover_type", "full"),
        progress_at_handover=handover_data.get("progress_at_handover", 0.0),
        context_data=json.dumps(context_data),
        notes=handover_data.get("notes", ""),
        status="pending"
    )
    
    db.add(handover)
    
    # 更新任务表中的 agent_id 和任务名称
    task = db.query(TaskRecord).filter(TaskRecord.task_id == handover_data["task_id"]).first()
    if task:
        old_agent = handover_data["from_agent_id"]
        new_agent = handover_data["to_agent_id"]
        
        # 更新执行者
        task.agent_id = new_agent
        
        # 更新任务名称中的 agent 前缀（如果任务名以旧 agent 开头）
        import re
        old_prefix_pattern = rf'^{re.escape(old_agent)}[\s-]+'
        if re.match(old_prefix_pattern, task.task_name, re.IGNORECASE):
            # 替换前缀为新 agent
            task.task_name = re.sub(old_prefix_pattern, f'{new_agent} ', task.task_name, flags=re.IGNORECASE)
            print(f"📝 任务名称更新：{task.task_name}")
        
        task.status = "pending"  # 重置为待执行，等待新 Agent 接收
        print(f"✅ 任务 {task.task_name} 已从 {old_agent} 移交给 {new_agent}")
    else:
        print(f"⚠️ 未找到任务 {handover_data['task_id']}")
    
    db.commit()
    db.refresh(handover)
    
    # 发送 WebSocket 通知
    broadcast_agent_update({
        "type": "handover_completed",
        "data": {
            "handover_id": handover.handover_id,
            "from_agent_id": handover.from_agent_id,
            "to_agent_id": handover.to_agent_id,
            "task_name": handover.task_name,
            "task_updated": task is not None
        }
    })
    
    return {
        "success": True,
        "handover_id": handover.handover_id,
        "task_updated": task is not None,
        "handover": {
            "id": handover.id,
            "handover_id": handover.handover_id,
            "task_id": handover.task_id,
            "from_agent_id": handover.from_agent_id,
            "to_agent_id": handover.to_agent_id,
            "status": handover.status,
            "created_at": to_local_time(handover.created_at).isoformat()
        }
    }


@app.get("/api/v1/handovers")
def get_handovers(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取交接列表"""
    query = db.query(TaskHandover)
    
    if status:
        query = query.filter(TaskHandover.status == status)
    if agent_id:
        query = query.filter(
            (TaskHandover.from_agent_id == agent_id) | 
            (TaskHandover.to_agent_id == agent_id)
        )
    if task_id:
        query = query.filter(TaskHandover.task_id == task_id)
    
    handovers = query.order_by(TaskHandover.created_at.desc()).all()
    
    return {
        "handovers": [
            {
                "id": h.id,
                "handover_id": h.handover_id,
                "task_id": h.task_id,
                "task_name": h.task_name,
                "from_agent_id": h.from_agent_id,
                "from_agent_name": h.from_agent_name,
                "to_agent_id": h.to_agent_id,
                "to_agent_name": h.to_agent_name,
                "handover_type": h.handover_type,
                "progress_at_handover": h.progress_at_handover,
                "context_data": json.loads(h.context_data) if h.context_data else {},
                "notes": h.notes,
                "status": h.status,
                "accepted_at": to_local_time(h.accepted_at).isoformat() if h.accepted_at else None,
                "completed_at": to_local_time(h.completed_at).isoformat() if h.completed_at else None,
                "created_at": to_local_time(h.created_at).isoformat(),
                "updated_at": to_local_time(h.updated_at).isoformat()
            }
            for h in handovers
        ],
        "total": len(handovers)
    }


@app.get("/api/v1/handovers/{handover_id}")
def get_handover(handover_id: str, db: Session = Depends(get_db)):
    """获取交接详情"""
    handover = db.query(TaskHandover).filter(
        TaskHandover.handover_id == handover_id
    ).first()
    
    if not handover:
        raise HTTPException(status_code=404, detail="交接记录不存在")
    
    return {
        "handover": {
            "id": handover.id,
            "handover_id": handover.handover_id,
            "task_id": handover.task_id,
            "task_name": handover.task_name,
            "from_agent_id": handover.from_agent_id,
            "from_agent_name": handover.from_agent_name,
            "to_agent_id": handover.to_agent_id,
            "to_agent_name": handover.to_agent_name,
            "handover_type": handover.handover_type,
            "progress_at_handover": handover.progress_at_handover,
            "context_data": json.loads(handover.context_data) if handover.context_data else {},
            "notes": handover.notes,
            "status": handover.status,
            "accepted_at": to_local_time(handover.accepted_at).isoformat() if handover.accepted_at else None,
            "completed_at": to_local_time(handover.completed_at).isoformat() if handover.completed_at else None,
            "created_at": to_local_time(handover.created_at).isoformat() if handover.created_at else None,
            "updated_at": to_local_time(handover.updated_at).isoformat() if handover.updated_at else None
        }
    }


@app.post("/api/v1/handovers/{handover_id}/accept")
def accept_handover(
    handover_id: str,
    accept_data: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """接受交接"""
    handover = db.query(TaskHandover).filter(
        TaskHandover.handover_id == handover_id
    ).first()
    
    if not handover:
        raise HTTPException(status_code=404, detail="交接记录不存在")
    
    handover.status = "accepted"
    handover.accepted_at = get_current_utc()
    handover.updated_at = get_current_utc()
    
    db.commit()
    
    # 发送 WebSocket 通知
    broadcast_agent_update({
        "type": "handover_accepted",
        "data": {
            "handover_id": handover_id,
            "accepted_by": handover.to_agent_id,
            "message": accept_data.get("message", "") if accept_data else ""
        }
    })
    
    return {
        "success": True,
        "handover": {
            "id": handover.id,
            "handover_id": handover.handover_id,
            "status": handover.status,
            "accepted_at": handover.accepted_at.isoformat()
        }
    }


@app.post("/api/v1/handovers/{handover_id}/reject")
def reject_handover(
    handover_id: str,
    reject_data: dict,
    db: Session = Depends(get_db)
):
    """拒绝交接"""
    handover = db.query(TaskHandover).filter(
        TaskHandover.handover_id == handover_id
    ).first()
    
    if not handover:
        raise HTTPException(status_code=404, detail="交接记录不存在")
    
    handover.status = "rejected"
    handover.updated_at = get_current_utc()
    
    db.commit()
    
    return {
        "success": True,
        "handover": {
            "id": handover.id,
            "handover_id": handover.handover_id,
            "status": handover.status,
            "reason": reject_data.get("reason", "")
        }
    }


@app.post("/api/v1/handovers/{handover_id}/complete")
def complete_handover(
    handover_id: str,
    complete_data: dict,
    db: Session = Depends(get_db)
):
    """完成交接"""
    handover = db.query(TaskHandover).filter(
        TaskHandover.handover_id == handover_id
    ).first()
    
    if not handover:
        raise HTTPException(status_code=404, detail="交接记录不存在")
    
    handover.status = "completed"
    handover.completed_at = get_current_utc()
    handover.updated_at = get_current_utc()
    
    db.commit()
    
    return {
        "success": True,
        "handover": {
            "id": handover.id,
            "handover_id": handover.handover_id,
            "status": handover.status,
            "completed_at": handover.completed_at.isoformat(),
            "summary": complete_data.get("summary", "")
        }
    }


# ==================== 初始化 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    print("🦞 OpenClaw 办公室 API 启动中...")
    init_db()
    print("✅ 数据库初始化完成（真实数据模式）")
    print("🚀 OpenClaw 办公室 API 已就绪")
    print("🔗 对接 OpenClaw 真实数据")
    
    # 启动自动督促调度器（后台任务）
    asyncio.create_task(start_reminder_scheduler(get_db))
    print("⏰ 自动督促调度器已启动")
    
    # 启动数据采集调度器（定时任务）
    start_data_sync_scheduler(get_db)
    print("⏰ 数据采集调度器已启动")
    
    # 启动健康检测调度器（定时任务）
    start_health_check_scheduler()
    
    # 立即执行一次数据采集（冷启动）
    print("🔄 执行首次数据采集...")
    try:
        from request_sync import sync_request_logs
        db = next(get_db())
        count = sync_request_logs(db, lookback_hours=24)
        db.commit()
        print(f"✅ 首次采集完成：{count} 条记录")
    except Exception as e:
        print(f"⚠️ 首次采集：{e}")
    finally:
        try:
            db.close()
        except:
            pass


# ==================== 请求统计管理 ====================

@app.post("/api/v1/requests/sync")
def sync_requests(
    lookback_hours: int = 24,
    db: Session = Depends(get_db)
):
    """同步请求日志"""
    count = sync_request_logs(db, lookback_hours)
    return {
        "success": True,
        "synced_count": count,
        "lookback_hours": lookback_hours
    }


@app.post("/api/v1/config/sync")
def sync_config(
    agent_sync_interval_minutes: int = Body(..., description="Agent 状态同步频率（分钟）"),
    task_sync_interval_minutes: int = Body(..., description="任务数据同步频率（分钟）"),
    request_sync_interval_minutes: int = Body(..., description="请求日志同步频率（分钟）"),
    cron_sync_interval_minutes: int = Body(..., description="Cron 任务同步频率（分钟）")
):
    """
    同步配置到后端
    更新同步频率设置并重启调度器
    """
    import json
    
    # 验证输入
    if not (1 <= agent_sync_interval_minutes <= 120):
        raise HTTPException(status_code=400, detail="Agent 状态同步频率必须在1-120分钟之间")
    if not (1 <= task_sync_interval_minutes <= 120):
        raise HTTPException(status_code=400, detail="任务数据同步频率必须在1-120分钟之间")
    if not (1 <= request_sync_interval_minutes <= 120):
        raise HTTPException(status_code=400, detail="请求日志同步频率必须在1-120分钟之间")
    if not (1 <= cron_sync_interval_minutes <= 120):
        raise HTTPException(status_code=400, detail="Cron 任务同步频率必须在1-120分钟之间")
    
    # 读取当前配置
    current_config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
    
    # 更新同步频率配置
    if 'sync_intervals' not in current_config:
        current_config['sync_intervals'] = {}
    
    current_config['sync_intervals']['agent_sync_interval_minutes'] = agent_sync_interval_minutes
    current_config['sync_intervals']['task_sync_interval_minutes'] = task_sync_interval_minutes
    current_config['sync_intervals']['request_sync_interval_minutes'] = request_sync_interval_minutes
    current_config['sync_intervals']['cron_sync_interval_minutes'] = cron_sync_interval_minutes
    
    # 保存配置
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_config, f, indent=2, ensure_ascii=False)
    
    # 直接更新内存中的配置
    config.config['sync_intervals'] = current_config['sync_intervals']
    
    # 重启数据同步调度器
    try:
        from scheduler import stop_data_sync_scheduler, start_data_sync_scheduler, data_sync_scheduler
        # 先停止调度器
        stop_data_sync_scheduler()
        # 重新加载配置
        data_sync_scheduler.reload_config()
        # 重新启动调度器
        start_data_sync_scheduler(get_db)
        print("✅ 数据同步调度器已重启，新配置生效")
    except Exception as e:
        print(f"⚠️ 重启调度器失败：{e}")
    
    return {
        "success": True,
        "message": "配置已保存并生效",
        "config": {
            "agent_sync_interval_minutes": agent_sync_interval_minutes,
            "task_sync_interval_minutes": task_sync_interval_minutes,
            "request_sync_interval_minutes": request_sync_interval_minutes,
            "cron_sync_interval_minutes": cron_sync_interval_minutes
        }
    }


@app.get("/api/v1/requests/stats")
def get_request_stats(
    period: str = "daily",  # daily, weekly, monthly
    agent_id: Optional[str] = None,
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取请求统计"""
    from datetime import datetime, timedelta
    
    # 获取当前北京时间（UTC+8）
    def get_local_now():
        return datetime.now(CONFIG_TZ)
    
    if period == "daily":
        if not date:
            date = get_local_now().strftime('%Y-%m-%d')
        return get_hourly_stats(db, agent_id, date)
    
    elif period == "weekly":
        if not date:
            date = get_local_now().strftime('%Y-%m-%d')
        # 计算本周起止
        current = datetime.strptime(date, '%Y-%m-%d')
        start = current - timedelta(days=current.weekday())
        end = start + timedelta(days=6)
        return get_daily_stats(db, agent_id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    
    elif period == "monthly":
        if not date:
            date = get_local_now().strftime('%Y-%m-%d')
        # 计算本月起止
        current = datetime.strptime(date, '%Y-%m-%d')
        start = current.replace(day=1)
        if current.month == 12:
            end = current.replace(year=current.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end = current.replace(month=current.month+1, day=1) - timedelta(days=1)
        return get_daily_stats(db, agent_id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    
    elif period == "comparison":
        if not date:
            date = get_local_now().strftime('%Y-%m-%d')
        return get_agent_comparison(db, date)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported period: {period}")


@app.get("/api/v1/requests/providers")
def get_provider_stats(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取请求统计
    返回今日请求数、今日Token、高峰时段、高峰请求数
    """
    from sqlalchemy import func, text
    
    # 解析传入的日期（北京时间），如果没有传入则使用当前日期
    if not date:
        # 获取当前北京时间
        now_local = datetime.now(CONFIG_TZ)
        date = now_local.strftime('%Y-%m-%d')
    
    # 1. 解析传入的日期（北京时间）
    start_local = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=CONFIG_TZ)
    end_local = start_local + timedelta(days=1)
    
    # 2. 转换为 UTC 时间（不带时区）
    start_utc = start_local.astimezone(UTC).replace(tzinfo=None)
    end_utc = end_local.astimezone(UTC).replace(tzinfo=None)
    
    # 获取按provider分组的统计数据
    query = text("""
        SELECT 
            provider,
            COUNT(*) as count,
            SUM(tokens_total) as tokens
        FROM request_logs
        WHERE created_at >= :start AND created_at < :end
        AND provider IS NOT NULL AND provider != ''
        GROUP BY provider
    """)
    
    results = db.execute(query, {"start": start_utc, "end": end_utc}).fetchall()
    
    # 调试：打印查询结果
    print(f"查询结果: {results}")
    
    providers = []
    for row in results:
        provider = row[0] if row[0] else 'unknown'
        count = row[1]
        tokens = row[2] or 0
        
        # 找出该provider的高峰时段
        peak_query = text("""
            SELECT 
                strftime('%H', created_at) as hour,
                COUNT(*) as count
            FROM request_logs
            WHERE created_at >= :start AND created_at < :end
            AND provider = :provider
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 1
        """)
        peak = db.execute(peak_query, {"start": start_utc, "end": end_utc, "provider": provider}).fetchone()
        
        if peak:
            # 数据库中存的是 UTC 时间的小时，需要转换为本地时区
            utc_hour = int(peak[0])
            utc_datetime = datetime.combine(start_utc.date(), datetime.min.time()) + timedelta(hours=utc_hour)
            utc_datetime = utc_datetime.replace(tzinfo=UTC)
            local_datetime = utc_datetime.astimezone(CONFIG_TZ)
            peak_hour = local_datetime.hour
            peak_count = peak[1]
        else:
            peak_hour = 0
            peak_count = count
        
        providers.append({
            'provider': provider,
            'request_count': count,
            'tokens_total': tokens,
            'peak_hour': peak_hour,
            'peak_count': peak_count
        })
    
    return {
        'date': date,
        'providers': providers,
        'debug': str(results),
        'start': start_utc.isoformat(),
        'end': end_utc.isoformat()
    }


@app.get("/api/v1/requests/models")
def get_model_stats(
    date: Optional[str] = None,
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取分模型的请求统计"""
    from sqlalchemy import func
    
    if not date:
        # 获取当前北京时间
        now_local = datetime.now(CONFIG_TZ)
        date = now_local.strftime('%Y-%m-%d')
    
    # 1. 解析传入的日期（北京时间）
    start_local = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=CONFIG_TZ)
    end_local = start_local + timedelta(days=1)
    
    # 2. 转换为 UTC 时间（不带时区）
    start_utc = start_local.astimezone(UTC).replace(tzinfo=None)
    end_utc = end_local.astimezone(UTC).replace(tzinfo=None)
    
    query = db.query(
        RequestLog.model_name.label('model'),
        RequestLog.provider.label('provider'),
        func.count(RequestLog.id).label('count'),
        func.sum(RequestLog.tokens_total).label('tokens')
    ).filter(
        RequestLog.created_at >= start_utc,
        RequestLog.created_at < end_utc,
        RequestLog.model_name != '',
        RequestLog.model_name != None
    )
    
    if provider:
        query = query.filter(RequestLog.provider == provider)
    
    models = query.group_by(RequestLog.model_name, RequestLog.provider).all()
    
    return {
        'date': date,
        'provider': provider,
        'models': [
            {'model': m.model, 'provider': m.provider or 'unknown', 'count': m.count, 'tokens': m.tokens or 0}
            for m in models
        ]
    }


@app.get("/api/v1/requests/agents")
def get_agent_list(db: Session = Depends(get_db)):
    """获取 Agent 列表及其请求统计"""
    from sqlalchemy import func, distinct
    
    agents = db.query(
        RequestLog.agent_id,
        RequestLog.agent_name,
        func.count(RequestLog.id).label('total_count'),
        func.sum(RequestLog.tokens_total).label('total_tokens')
    ).group_by(
        RequestLog.agent_id,
        RequestLog.agent_name
    ).all()
    
    return {
        "agents": [
            {
                "agent_id": a.agent_id,
                "agent_name": a.agent_name,
                "total_count": a.total_count,
                "total_tokens": a.total_tokens or 0
            }
            for a in agents
        ]
    }


@app.on_event("shutdown")
def shutdown_event():
    """应用关闭时清理资源"""
    print("🛑 OpenClaw 办公室 API 关闭中...")
    stop_scheduler()
    print("✅ 已停止所有调度器")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
