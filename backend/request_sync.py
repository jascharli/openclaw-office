"""
龙虾办公室 - 请求日志同步模块
从 OpenClaw sessions 同步大模型请求记录
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from database import RequestLog, to_utc


# 模型到服务商的映射表
MODEL_PROVIDER_MAP = {
    # bailian 百炼
    'qwen3.5-plus': 'bailian',
    'qwen3.5-turbo': 'bailian',
    'qwen3.5-14b': 'bailian',
    'qwen3.5-32b': 'bailian',
    'qwen3.5-72b': 'bailian',
    'qwen3.5-110b': 'bailian',
    'qwen-max': 'bailian',
    'qwen-plus': 'bailian',
    'qwen-turbo': 'bailian',
    
    # volcengine 火山引擎
    'ark-code-latest': 'volcengine',
    'doubao-seed-2.0-code': 'volcengine',
    'doubao-seed-2.0-pro': 'volcengine',
    'doubao-seed-2.0-lite': 'volcengine',
    'doubao-seed-code': 'volcengine',
    
    # Moonshot
    'kimi-k2.5': 'moonshot',
    'kimi-k2': 'moonshot',
    'kimi-k1.5': 'moonshot',
    
    # Zhipu 智谱
    'glm-5': 'zhipu',
    'glm-4': 'zhipu',
    'glm-4v': 'zhipu',
    'glm-3-turbo': 'zhipu',
    
    # MiniMax
    'MiniMax-M2.5': 'minimax',
    'MiniMax-M2': 'minimax',
    'minimax-m2.5': 'minimax',
    
    # OpenAI
    'gpt-4': 'openai',
    'gpt-4o': 'openai',
    'gpt-4o-mini': 'openai',
    'gpt-3.5-turbo': 'openai',
    
    # Anthropic
    'claude-3-opus': 'anthropic',
    'claude-3-sonnet': 'anthropic',
    'claude-3-haiku': 'anthropic',
    'claude-3.5-sonnet': 'anthropic',
}


def infer_provider_from_model(model_name: str) -> str:
    """根据模型名称推断服务商"""
    if not model_name:
        return 'unknown'
    
    model_lower = model_name.lower()
    
    # 直接匹配
    if model_name in MODEL_PROVIDER_MAP:
        return MODEL_PROVIDER_MAP[model_name]
    
    # 模糊匹配
    for model, provider in MODEL_PROVIDER_MAP.items():
        if model.lower() in model_lower or model_lower in model.lower():
            return provider
    
    # 根据关键词推断
    if 'qwen' in model_lower or '通义' in model_lower:
        return 'bailian'
    elif 'doubao' in model_lower or 'seed' in model_lower or 'ark' in model_lower:
        return 'volcengine'
    elif 'kimi' in model_lower:
        return 'moonshot'
    elif 'glm' in model_lower:
        return 'zhipu'
    elif 'minimax' in model_lower:
        return 'minimax'
    elif 'gpt' in model_lower:
        return 'openai'
    elif 'claude' in model_lower:
        return 'anthropic'
    
    return 'unknown'


def identify_agent_from_session(session_path: str, agent_mapping: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """从 session 内容识别 Agent"""
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i > 20:
                    break
                msg = json.loads(line)
                if msg.get('type') == 'session':
                    session_id = msg.get('id', '')
                    for aid, aname in agent_mapping.items():
                        if aid in session_id.lower():
                            return aid, aname
                content_str = json.dumps(msg).lower()
                for aid, aname in agent_mapping.items():
                    if aid in content_str:
                        return aid, aname
    except:
        pass
    for aid, aname in agent_mapping.items():
        return aid, aname
    return None, None


def sync_request_logs(db: Session, lookback_hours: int = 24) -> int:
    """同步请求日志（扫描所有 Agent 的 session 目录）"""
    # 扫描所有 Agent 的 session 目录
    agents_base_dir = os.path.expanduser("~/.openclaw/agents")
    agent_dirs = ["dev-claw", "main", "work-claw", "daughter", "wife"]
    
    total_count = 0
    threshold = datetime.utcnow() - timedelta(hours=lookback_hours)
    agent_mapping = {"dev-claw": "dev-claw", "main": "大白 AI", "work-claw": "work-claw", "daughter": "daughter", "wife": "wife"}
    
    for agent_dir in agent_dirs:
        sessions_dir = os.path.join(agents_base_dir, agent_dir, "sessions")
        if not os.path.exists(sessions_dir):
            continue
        
        for filename in os.listdir(sessions_dir):
            if not filename.endswith('.jsonl'):
                continue
            session_path = os.path.join(sessions_dir, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(session_path))
            if mtime < threshold:
                continue
            
            # 优先使用目录名作为 agent_id（最准确）
            agent_id = agent_dir
            agent_name = agent_mapping.get(agent_dir, agent_dir)
            
            try:
                total_count += parse_session_file(db, session_path, agent_id, agent_name)
            except Exception as e:
                pass
    
    db.commit()
    return total_count


def parse_session_file(db: Session, session_path: str, agent_id: str, agent_name: str) -> int:
    """解析 session 文件"""
    count = 0
    session_provider = None  # 会话级别的 provider（从 model_change 事件获取）
    session_model = None      # 会话级别的 model（从 model_change 事件获取）
    
    with open(session_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        try:
            msg = json.loads(line)
            
            # 处理 model_change 事件，获取会话级别的 provider 和 model
            if msg.get('type') == 'model_change':
                session_provider = msg.get('provider', session_provider)
                session_model = msg.get('modelId', session_model)
                continue
            
            # 处理 custom 事件（model-snapshot），获取 provider
            if msg.get('type') == 'custom' and msg.get('customType') == 'model-snapshot':
                data = msg.get('data', {})
                session_provider = data.get('provider', session_provider)
                session_model = data.get('modelId', session_model)
                continue
            
            # 只处理 message 事件
            if msg.get('type') != 'message':
                continue
            
            if 'message' in msg:
                role = msg['message'].get('role', '')
                usage = msg['message'].get('usage', {})
                content = msg['message'].get('content', [])
            else:
                role = msg.get('role', '')
                usage = msg.get('usage', {})
                content = msg.get('content', [])
            
            if role != 'assistant':
                continue
            
            message_id = msg.get('id', '') or msg.get('message', {}).get('id', '')
            if not message_id:
                continue
            
            # 提取 model 和 provider 信息（优先级：message 事件 > 会话级别 > 推断）
            model_name = msg.get('model', '') or msg.get('message', {}).get('model', '') or session_model or ''
            provider = msg.get('provider', '') or msg.get('message', {}).get('provider', '') or session_provider or ''
            
            # 如果 provider 为空，设置为 'unknown'
            if not provider:
                provider = 'unknown'
            
            tokens_total = usage.get('totalTokens', 0)
            if tokens_total == 0:
                text = ''
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text += item.get('text', '')
                chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                tokens_total = max(10, chinese + (len(text) - chinese) // 4)
            
            # 检查是否已存在
            existing = db.query(RequestLog).filter(RequestLog.message_id == message_id).first()
            if existing:
                # 如果 model_name 为空，更新它
                if not existing.model_name and model_name:
                    existing.model_name = model_name
                if not existing.tokens_total and tokens_total:
                    existing.tokens_total = tokens_total
                if not existing.provider and provider:
                    existing.provider = provider
                continue
            
            # 如果 model_name 包含 provider 信息（如 bailian/qwen3.5-plus），提取 provider
            if model_name and '/' in model_name and not provider:
                parts = model_name.split('/')
                if len(parts) == 2:
                    provider = parts[0]
                    model_name = parts[1]
            
            # 不根据 model_name 推断 provider，只使用从 session 文件中明确获取的信息
            # 这样可以避免将开源大模型错误地归属到服务商
            
            try:
                ts = msg.get('timestamp', 0)
                # 支持两种格式：数字时间戳（UTC）或 ISO 字符串（UTC）
                if isinstance(ts, str):
                    if 'T' in ts:  # ISO 格式：2026-03-25T20:21:48.093Z
                        # 解析为 UTC 时间
                        ts = ts.replace('Z', '+00:00')
                        created_at = datetime.fromisoformat(ts)
                    else:  # 数字字符串
                        ts_float = float(ts) / 1000
                        # 从 UTC 时间戳创建 datetime
                        created_at = datetime.utcfromtimestamp(ts_float)
                else:  # 数字时间戳（UTC）
                    ts_float = ts / 1000
                    # 从 UTC 时间戳创建 datetime
                    created_at = datetime.utcfromtimestamp(ts_float)
            except Exception as e:
                print(f"⚠️ 时间解析失败：{ts} - {e}")
                created_at = datetime.utcnow()
            
            # 确保存储为 UTC 时间（不带时区）
            created_at_utc = to_utc(created_at)
            db.add(RequestLog(
                request_id=f"req-{uuid.uuid4().hex[:12]}",
                agent_id=agent_id,
                agent_name=agent_name,
                request_type='chat',
                provider=provider,
                model_name=model_name,
                tokens_total=tokens_total,
                status='success',
                message_id=message_id,
                created_at=created_at_utc
            ))
            count += 1
        except:
            pass
    return count


def get_hourly_stats(db: Session, agent_id: Optional[str], date: str) -> Dict:
    """
    获取每小时统计（数据库存储 UTC 时间）
    返回分服务商的数据，用于分组柱状图
    """
    from sqlalchemy import func, text
    # 数据库存储的是 UTC 时间，需要根据配置的时区进行查询
    start = datetime.strptime(date, '%Y-%m-%d')
    end = start + timedelta(days=1)
    
    # 查询：每个小时 × 每个服务商 的请求数
    query = text("""
        SELECT 
            strftime('%H', created_at) as hour,
            provider,
            COUNT(*) as count
        FROM request_logs
        WHERE created_at >= :start AND created_at < :end
        AND provider IS NOT NULL AND provider != ''
        GROUP BY hour, provider
        ORDER BY hour, provider
    """)
    
    params = {"start": start, "end": end}
    if agent_id:
        query = text("""
            SELECT 
                strftime('%H', created_at) as hour,
                provider,
                COUNT(*) as count
            FROM request_logs
            WHERE created_at >= :start AND created_at < :end
            AND agent_id = :agent_id
            AND provider IS NOT NULL AND provider != ''
            GROUP BY hour, provider
            ORDER BY hour, provider
        """)
        params["agent_id"] = agent_id
    
    results = db.execute(query, params).fetchall()
    
    # 整理数据：hourly[hour] = {by_provider: {provider: count}, total}
    hourly_data = {}
    total_count = 0
    
    # 初始化 24 小时
    for hour in range(24):
        hourly_data[str(hour).zfill(2)] = {
            'hour': hour,
            'by_provider': {},
            'total': 0
        }
    
    for row in results:
        hour = row.hour
        provider = row.provider
        count = row.count
        
        # 使用数据库中的 provider 字段
        if provider not in hourly_data[hour]['by_provider']:
            hourly_data[hour]['by_provider'][provider] = 0
        hourly_data[hour]['by_provider'][provider] += count
        hourly_data[hour]['total'] += count
        total_count += count
    
    # 转换为列表输出
    hourly_list = list(hourly_data.values())
    
    return {
        'period': 'daily',
        'date': date,
        'agent_id': agent_id,
        'hourly': hourly_list,  # 每个元素: {hour, by_provider: {provider: count}, total}
        'total': {
            'count': total_count
        }
    }


def get_daily_stats(db: Session, agent_id: Optional[str], start_date: str, end_date: str) -> Dict:
    """获取每日统计"""
    from sqlalchemy import func
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    query = db.query(
        func.date(RequestLog.created_at).label('date'),
        func.count(RequestLog.id).label('count'),
        func.sum(RequestLog.tokens_total).label('tokens')
    ).filter(RequestLog.created_at >= start, RequestLog.created_at < end)
    if agent_id:
        query = query.filter(RequestLog.agent_id == agent_id)
    query = query.group_by(func.date(RequestLog.created_at))
    results = query.all()
    
    daily = {}
    current = start
    while current < end:
        daily[current.strftime('%Y-%m-%d')] = {'day': current.strftime('%Y-%m-%d'), 'count': 0, 'tokens': 0}
        current += timedelta(days=1)
    for row in results:
        if row.date in daily:
            daily[row.date] = {'day': row.date, 'count': row.count, 'tokens': row.tokens or 0}
    
    return {'period': 'daily_range', 'start_date': start_date, 'end_date': end_date, 'agent_id': agent_id,
            'daily': list(daily.values()), 'total': {'count': sum(d['count'] for d in daily.values()), 'tokens': sum(d['tokens'] for d in daily.values())}}


def get_agent_comparison(db: Session, date: str) -> Dict:
    """获取 Agent 对比"""
    from sqlalchemy import func
    start = datetime.strptime(date, '%Y-%m-%d')
    end = start + timedelta(days=1)
    query = db.query(
        RequestLog.agent_id, RequestLog.agent_name,
        func.count(RequestLog.id).label('count'),
        func.sum(RequestLog.tokens_total).label('tokens')
    ).filter(RequestLog.created_at >= start, RequestLog.created_at < end
    ).group_by(RequestLog.agent_id, RequestLog.agent_name)
    results = query.all()
    
    agents = [{'agent_id': r.agent_id, 'agent_name': r.agent_name, 'count': r.count, 'tokens': r.tokens or 0} for r in results]
    return {'period': 'comparison', 'date': date, 'agents': agents,
            'total': {'count': sum(a['count'] for a in agents), 'tokens': sum(a['tokens'] for a in agents)}}
