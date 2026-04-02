"""
龙虾办公室 - OpenClaw 数据同步模块
从 OpenClaw sessions 同步 Agent 状态
"""

import os
import json
from datetime import datetime, timedelta, timezone

# 北京时区（UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from database import AgentStatus
from config import get_config

# 常量
WORKING_MIN_TOOL_CALLS = 2
TOOL_CALL_WEIGHT = 2.0


def get_agent_list() -> List[Dict]:
    """从配置获取 Agent 列表"""
    config = get_config()
    return config.get_agent_list()


def analyze_session_messages(session_path: str, last_activity: datetime) -> Optional[Dict]:
    """
    分析 session 消息内容
    
    参数：
    - session_path: session 文件路径
    - last_activity: 最后活跃时间
    
    返回：
    {
        'assistant_count': int,
        'user_count': int,
        'tool_count': int,
        'has_task_context': bool,
        'task_name': str|None,
        'current_action': str|None,
        'subagent_actions': List[Dict],
        'token_used': int,
        'message_count': int,
        'is_recent': bool
    }
    """
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return None
        
        # 分析最后 100 条消息（覆盖更多对话历史）
        recent_lines = lines[-100:] if len(lines) >= 100 else lines
        all_lines = lines
        
        # 统计消息类型
        assistant_count = 0
        user_count = 0
        tool_count = 0
        token_used = 0
        
        # 任务上下文检测
        has_task_context = False
        task_name = None
        current_action = None
        subagent_actions = []
        
        # 对话时长计算：记录第一条用户消息时间和最后一条用户消息时间
        first_user_message_time = None
        last_user_message_time = None
        last_message_time = None
        
        for line in recent_lines:
            try:
                msg = json.loads(line)
                msg_type = msg.get("type", "")
                
                # 记录消息时间（转换为 UTC datetime）
                msg_timestamp = msg.get("timestamp", "")
                if msg_timestamp:
                    try:
                        msg_dt = datetime.fromisoformat(msg_timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
                        if last_message_time is None or msg_dt > last_message_time:
                            last_message_time = msg_dt
                    except:
                        pass
                
                if msg_type == "message":
                    role = msg.get("message", {}).get("role", "")
                    content_items = msg.get("message", {}).get("content", [])
                    
                    if role == "assistant":
                        assistant_count += 1
                        
                        # 检测任务关键词
                        for item in content_items:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                content = item.get('text', '')
                                if any(kw in content for kw in ['任务', '执行', '完成', '进度', '正在']):
                                    has_task_context = True
                                    
                    elif role == "user":
                        user_count += 1
                        
                        # 记录第一条用户消息时间
                        if first_user_message_time is None and msg_timestamp:
                            try:
                                first_user_message_time = datetime.fromisoformat(msg_timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
                            except:
                                pass
                        
                        # 记录最后一条用户消息时间（用于计算对话时长）
                        if msg_timestamp:
                            try:
                                last_user_message_time = datetime.fromisoformat(msg_timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
                            except:
                                pass
                        
                        # 检测用户分配任务
                        for item in content_items:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                content = item.get('text', '')
                                if any(kw in content for kw in ['请执行', '帮我', '完成', '开发', '创建']):
                                    has_task_context = True
                                    if not task_name:
                                        task_name = extract_task_name(content)
                
                elif msg_type == "toolCall":
                    tool_name = msg.get("toolName", "")
                    tool_args = msg.get("arguments", {})
                    
                    if tool_name:
                        tool_count += 1
                        
                        # 检测 sessions_spawn
                        if tool_name == "sessions_spawn":
                            subagent_id = tool_args.get('agentId', '')
                            task = tool_args.get('task', '')
                            if subagent_id:
                                subagent_actions.append({
                                    'subagent_id': subagent_id,
                                    'task': task
                                })
                                current_action = f"{subagent_id}执行中"
                        
                        # 推断当前动作
                        if not current_action and tool_name in ['web_search', 'exec', 'read', 'write']:
                            action_target = extract_tool_target(tool_name, tool_args)
                            if action_target:
                                current_action = f"正在{tool_name}: {action_target[:30]}"
                
                elif msg_type == "toolResult":
                    tool_count += 1
                
                # 统计 token
                if "message" in msg and "usage" in msg["message"]:
                    usage = msg["message"]["usage"]
                    token_used += usage.get("totalTokens", 0)
            
            except:
                pass
        
        # 检测所有消息中的任务上下文（只检查最近 30 分钟的消息）
        if not has_task_context:
            # 计算 30 分钟前的时间戳
            thirty_min_ago = last_activity.timestamp() - (30 * 60)
            
            for line in all_lines[-50:]:
                try:
                    msg = json.loads(line)
                    timestamp = msg.get("timestamp", 0)
                    
                    # 只检查 30 分钟内的消息
                    if timestamp < thirty_min_ago:
                        continue
                    
                    content = msg.get("message", {}).get("content", "")
                    if 'task_name' in content or '任务名称' in content:
                        has_task_context = True
                        break
                except:
                    pass
        
        # 判断是否是最近的活跃（1 小时内）
        # 数据库存储的 last_activity 是北京时间，不带时区标签
        # 需要将 datetime.now 也转换为不带时区的北京时间
        now_beijing = datetime.now(BEIJING_TZ).replace(tzinfo=None)
        time_since_activity = (now_beijing - last_activity).total_seconds() / 3600
        is_recent = time_since_activity < 1.0
        
        return {
            'assistant_count': assistant_count,
            'user_count': user_count,
            'tool_count': tool_count,
            'has_task_context': has_task_context,
            'task_name': task_name,
            'current_action': current_action,
            'subagent_actions': subagent_actions,
            'token_used': token_used,
            'message_count': len(lines),
            'is_recent': is_recent,
            'first_user_message_time': first_user_message_time,
            'last_user_message_time': last_user_message_time,
            'last_message_time': last_message_time
        }
    
    except Exception as e:
        print(f"⚠️ 分析 session 失败：{e}")
        return None


def extract_tool_target(tool_name: str, args: Dict) -> str:
    """从工具参数中提取动作对象"""
    if not args:
        return ""
    
    if tool_name in ['read', 'write', 'edit']:
        return args.get('path', '') or args.get('file_path', '')
    elif tool_name in ['web_search', 'web_fetch']:
        return args.get('query', '') or args.get('url', '')
    elif tool_name == 'exec':
        cmd = args.get('command', '')
        return cmd[:50] if cmd else ''
    elif tool_name in ['feishu_doc', 'feishu_drive']:
        return args.get('title', '') or args.get('name', '')
    
    return ""


def extract_task_name(content: str) -> Optional[str]:
    """从消息内容中提取任务名称"""
    import re
    
    # 排除常见的元数据字段
    exclude_patterns = [
        r'"message_id"',
        r'"session_id"',
        r'"conversation_id"',
        r'"chat_id"',
        r'"sender_id"',
        r'"agent_id"',
        r'"task_id"',
        r'"timestamp"',
    ]
    
    for pattern in exclude_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            # 如果内容主要是元数据，不提取任务名
            return None
    
    # 匹配引号中的任务描述（排除纯英文字段名）
    match = re.search(r'["\']([\u4e00-\u9fa5A-Za-z][^"\']{3,50})["\']', content)
    if match:
        extracted = match.group(1).strip()
        # 排除纯英文短词（可能是字段名）
        if re.match(r'^[a-z_]+$', extracted, re.IGNORECASE):
            return None
        return extracted
    return None


def determine_agent_status(
    session_analysis: Optional[Dict],
    active_cron_tasks: Dict,
    agent_id: str,
    active_minutes: int,
    last_activity: datetime
) -> Tuple[str, Optional[str]]:
    """
    多维度判断 Agent 状态（按优先级顺序）
    
    优先级规则（从上到下，满足即返回）:
    1. working（办公，执行任务中，最高优先级）
       满足任意一条 → working
       - subagent 正在执行
       - cron 任务正在执行
       - 正在调用工具（tool call）
       - 有未完成的任务上下文（task context）
    
    2. conversing（对话，对话交互中）
       满足全部两条 → conversing
       - 不在 working（上面的条件都不满足）
       - 最近 5 分钟内有对话/交互
    
    3. idle（空闲）
       以上都不满足 → idle
    
    返回：
    (status, task_name)
    - status: 'idle' | 'conversing' | 'working'
    - task_name: 任务名称或 None
    """
    
    # ==================== 1️⃣ conversing 判定（最高优先级）====================
    # 优先显示对话状态（正在服务用户）
    # 判定逻辑：有对话交互且最近 20 分钟内 → conversing
    # 数据库存储的 last_activity 是北京时间，不带时区标签
    now_beijing = datetime.now(BEIJING_TZ).replace(tzinfo=None)
    time_since_activity = (now_beijing - last_activity).total_seconds() / 60
    
    if session_analysis:
        user_count = session_analysis.get('user_count', 0)
        assistant_count = session_analysis.get('assistant_count', 0)
        
        # 有对话交互且最近 20 分钟内（放宽到 20 分钟）
        if user_count > 0 and assistant_count > 0 and time_since_activity < 20:
            print(f"✅ [{agent_id}] 判定为 conversing - 最近对话（{time_since_activity:.1f}分钟前）")
            return 'conversing', None
    
    # ==================== 2️⃣ working 判定 ====================
    # 满足任意一条 → working
    
    # 2.1 subagent 正在执行
    if session_analysis and session_analysis.get('subagent_actions'):
        subagent_str = ' + '.join([f"{s['subagent_id']}执行中" for s in session_analysis['subagent_actions']])
        print(f"✅ [{agent_id}] 判定为 working - subagent 执行中：{subagent_str}")
        return 'working', subagent_str
    
    # 2.2 cron 任务正在执行
    if agent_id in active_cron_tasks:
        cron_task = active_cron_tasks[agent_id]
        print(f"✅ [{agent_id}] 判定为 working - cron 任务执行中：{cron_task['task_name']}")
        return 'working', cron_task['task_name']
    
    # 2.3 正在调用工具（tool call）
    if session_analysis:
        tool_count = session_analysis.get('tool_count', 0)
        if tool_count > 0:
            current_action = session_analysis.get('current_action')
            action_str = current_action if current_action else f'工具调用（{tool_count}次）'
            print(f"✅ [{agent_id}] 判定为 working - 工具调用中：{action_str}")
            return 'working', action_str
    
    # 2.4 有未完成的任务上下文（task context）
    # 注意：需要是最近 30 分钟内的任务上下文才算 working
    if session_analysis and session_analysis.get('has_task_context') and time_since_activity < 30:
        task_name = session_analysis.get('task_name')
        current_action = session_analysis.get('current_action')
        
        # 优先显示任务名，如果没有则显示当前动作
        if task_name:
            full_task = task_name
        elif current_action:
            full_task = current_action
        else:
            full_task = '处理任务中'
        
        print(f"✅ [{agent_id}] 判定为 working - 任务上下文中（{time_since_activity:.1f}分钟前）：{full_task}")
        return 'working', full_task
    
    # 2.5 任务上下文超时（>=30 分钟无响应）
    # 自动结束任务，记录原因
    elif session_analysis and session_analysis.get('has_task_context') and time_since_activity >= 30:
        print(f"✅ [{agent_id}] 判定为 idle - 任务超时结束（{time_since_activity:.0f}分钟无响应，用户未补充材料）")
        return 'idle', '任务已结束（等待用户响应超时）'
    
    # ==================== 3️⃣ idle 判定（默认）====================
    # 需求文档：长时间无响应（>1 小时）才算 idle
    # 5-60 分钟无活动可能是任务间隙，不应算 idle
    
    if time_since_activity > 60:
        print(f"✅ [{agent_id}] 判定为 idle - 长时间无活动（{time_since_activity:.0f}分钟）")
        return 'idle', None
    else:
        # 5-60 分钟无活动，可能是任务间隙，保持 working 状态
        # 保留原任务名，不要覆盖为"任务间隙中"
        task_name = session_analysis.get('task_name') if session_analysis else None
        if task_name:
            print(f"⏭️ [{agent_id}] 判定为 working - 任务间隙（{time_since_activity:.0f}分钟无活动）：{task_name}")
            return 'working', task_name
        else:
            print(f"⏭️ [{agent_id}] 判定为 working - 任务间隙（{time_since_activity:.0f}分钟无活动）")
            return 'working', '任务间隙中'


def get_openclaw_agents() -> List[Dict]:
    """从 OpenClaw sessions 目录读取 Agent 状态"""
    config = get_config()
    agent_list = config.get_agent_list()
    
    if not agent_list:
        print("⚠️ 未找到 Agent 配置")
        return []
    
    agents = []
    
    for agent_config in agent_list:
        agent_id = agent_config.get('id', '')
        agent_name = agent_config.get('name', agent_id)
        workspace = agent_config.get('workspace', '')
        
        # 查找 session 目录
        sessions_dir = None
        if workspace:
            test_dir = os.path.join(workspace, 'sessions')
            if os.path.exists(test_dir):
                sessions_dir = test_dir
        
        if not sessions_dir:
            # 尝试默认路径
            default_dir = os.path.expanduser(f"~/.openclaw/agents/{agent_id}/sessions")
            if os.path.exists(default_dir):
                sessions_dir = default_dir
        
        if not sessions_dir:
            # 没有找到 session 目录，返回空闲状态
            agents.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "status": "idle",
                "task_id": None,
                "task_name": None,
                "progress": 0.0,
                "elapsed_time": 0,
                "estimated_remaining": 0,
                "token_used": 0,
                "last_activity": datetime.now(BEIJING_TZ)  # 返回 datetime 对象，不是字符串
            })
            continue
        
        # 查找最新的 session 文件
        session_files = [
            os.path.join(sessions_dir, f) 
            for f in os.listdir(sessions_dir) 
            if f.endswith('.jsonl')
        ]
        
        if not session_files:
            agents.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "status": "idle",
                "task_id": None,
                "task_name": None,
                "progress": 0.0,
                "elapsed_time": 0,
                "estimated_remaining": 0,
                "token_used": 0,
                "last_activity": datetime.now(BEIJING_TZ)  # 返回 datetime 对象，不是字符串
            })
            continue
        
        # 按修改时间排序
        session_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        latest_session = session_files[0]
        
        # 获取文件时间（从文件修改时间获取）
        mtime = os.path.getmtime(latest_session)
        # 文件修改时间是 UTC 时间戳，转换为北京时间
        last_activity = datetime.fromtimestamp(mtime).astimezone(BEIJING_TZ).replace(tzinfo=None)
        
        # 计算活跃分钟数
        now_beijing = datetime.now(BEIJING_TZ).replace(tzinfo=None)
        active_minutes = int((now_beijing - last_activity).total_seconds() / 60)
        
        # 分析 session
        session_analysis = analyze_session_messages(latest_session, last_activity)
        
        if session_analysis:
            # 多维度判定状态
            status, task_name = determine_agent_status(
                session_analysis=session_analysis,
                active_cron_tasks={},
                agent_id=agent_id,
                active_minutes=active_minutes,
                last_activity=last_activity
            )
            
            # 计算对话时长/未活动时间
            if status == 'conversing' and session_analysis.get('last_user_message_time'):
                # 对话区：计算最后一条用户消息到现在的时间
                conversation_duration = int((now_beijing - session_analysis['last_user_message_time']).total_seconds())
                elapsed_time = max(0, conversation_duration)
            else:
                # 其他状态：使用未活动时间，最大 24 小时
                elapsed_time = min(active_minutes * 60, 86400)
            
            agents.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "status": status,
                "task_id": f"task-{agent_id}" if task_name else None,
                "task_name": task_name,
                "progress": 0.5 if status == 'working' else (1.0 if status == 'idle' else 0.0),
                "elapsed_time": elapsed_time,
                "estimated_remaining": 0,
                "token_used": session_analysis.get('token_used', 0),
                "last_activity": last_activity.isoformat()
            })
        else:
            agents.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "status": "idle",
                "task_id": None,
                "task_name": None,
                "progress": 0.0,
                "elapsed_time": 0,
                "estimated_remaining": 0,
                "token_used": 0,
                "last_activity": last_activity.isoformat()
            })
    
    return agents


def sync_to_database(db: Session):
    """同步 OpenClaw 数据到数据库"""
    agents = get_openclaw_agents()
    
    for agent_data in agents:
        agent = db.query(AgentStatus).filter(
            AgentStatus.agent_id == agent_data["agent_id"]
        ).first()
        
        # 处理 last_activity（可能是 datetime 或字符串）
        last_activity = agent_data.get("last_activity")
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        elif last_activity is None:
            last_activity = datetime.now(BEIJING_TZ)
        
        if agent:
            agent.status = agent_data["status"]
            agent.task_name = agent_data.get("task_name")
            agent.token_used = agent_data.get("token_used", 0)
            agent.last_activity = last_activity
            agent.updated_at = datetime.now(BEIJING_TZ)
        else:
            agent = AgentStatus(
                agent_id=agent_data["agent_id"],
                agent_name=agent_data["agent_name"],
                status=agent_data["status"],
                task_id=agent_data.get("task_id"),
                task_name=agent_data.get("task_name"),
                progress=agent_data.get("progress", 0.0),
                elapsed_time=agent_data.get("elapsed_time", 0),
                estimated_remaining=agent_data.get("estimated_remaining", 0),
                token_used=agent_data.get("token_used", 0),
                last_activity=last_activity
            )
            db.add(agent)
    
    db.commit()
    print(f"✅ 同步 {len(agents)} 个 Agent 状态到数据库")
    return len(agents)


if __name__ == '__main__':
    # 测试
    agents = get_openclaw_agents()
    for agent in agents:
        print(f"{agent['agent_id']}: {agent['status']} - {agent.get('task_name', '无任务')}")
