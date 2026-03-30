# 统计函数（追加到 request_sync.py 末尾）

def get_hourly_stats(db: Session, agent_id: Optional[str], date: str) -> Dict:
    """获取每小时统计数据"""
    from sqlalchemy import func
    
    start = datetime.strptime(date, '%Y-%m-%d')
    end = start + timedelta(days=1)
    
    # 1. 获取按小时分组的总请求数
    query = db.query(
        func.strftime('%H', RequestLog.created_at).label('hour'),
        func.count(RequestLog.id).label('count'),
        func.sum(RequestLog.tokens_total).label('tokens')
    ).filter(
        RequestLog.created_at >= start,
        RequestLog.created_at < end
    )
    
    if agent_id:
        query = query.filter(RequestLog.agent_id == agent_id)
    
    query = query.group_by(func.strftime('%H', RequestLog.created_at))
    results = query.all()
    
    # 2. 获取按小时和服务商分组的请求数
    provider_query = db.query(
        func.strftime('%H', RequestLog.created_at).label('hour'),
        RequestLog.provider,
        func.count(RequestLog.id).label('count')
    ).filter(
        RequestLog.created_at >= start,
        RequestLog.created_at < end
    )
    
    if agent_id:
        provider_query = provider_query.filter(RequestLog.agent_id == agent_id)
    
    provider_query = provider_query.group_by(func.strftime('%H', RequestLog.created_at), RequestLog.provider)
    provider_results = provider_query.all()
    
    # 3. 构建按服务商分组的数据
    hourly = {str(i).zfill(2): {'hour': i, 'count': 0, 'tokens': 0, 'by_provider': {}} for i in range(24)}
    
    # 填充总请求数
    for row in results:
        hourly[row.hour] = {'hour': int(row.hour), 'count': row.count, 'tokens': row.tokens or 0, 'by_provider': {}}
    
    # 填充按服务商分组的请求数
    for row in provider_results:
        hour_str = row.hour
        provider = row.provider or 'unknown'
        count = row.count
        if hour_str in hourly:
            hourly[hour_str]['by_provider'][provider] = count
    
    return {
        'period': 'daily',
        'date': date,
        'agent_id': agent_id,
        'hourly': list(hourly.values()),
        'total': {
            'count': sum(h['count'] for h in hourly.values()),
            'tokens': sum(h['tokens'] for h in hourly.values())
        }
    }


def get_daily_stats(db: Session, agent_id: Optional[str], start_date: str, end_date: str) -> Dict:
    """获取每日统计数据"""
    from sqlalchemy import func
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    query = db.query(
        func.date(RequestLog.created_at).label('date'),
        func.count(RequestLog.id).label('count'),
        func.sum(RequestLog.tokens_total).label('tokens')
    ).filter(
        RequestLog.created_at >= start,
        RequestLog.created_at < end
    )
    
    if agent_id:
        query = query.filter(RequestLog.agent_id == agent_id)
    
    query = query.group_by(func.date(RequestLog.created_at))
    results = query.all()
    
    daily = {}
    current = start
    while current < end:
        date_str = current.strftime('%Y-%m-%d')
        daily[date_str] = {'day': date_str, 'count': 0, 'tokens': 0}
        current += timedelta(days=1)
    
    for row in results:
        if row.date in daily:
            daily[row.date] = {'day': row.date, 'count': row.count, 'tokens': row.tokens or 0}
    
    return {
        'period': 'daily_range',
        'start_date': start_date,
        'end_date': end_date,
        'agent_id': agent_id,
        'daily': list(daily.values()),
        'total': {
            'count': sum(d['count'] for d in daily.values()),
            'tokens': sum(d['tokens'] for d in daily.values())
        }
    }


def get_agent_comparison(db: Session, date: str) -> Dict:
    """获取 Agent 对比统计"""
    from sqlalchemy import func
    
    start = datetime.strptime(date, '%Y-%m-%d')
    end = start + timedelta(days=1)
    
    query = db.query(
        RequestLog.agent_id,
        RequestLog.agent_name,
        func.count(RequestLog.id).label('count'),
        func.sum(RequestLog.tokens_total).label('tokens')
    ).filter(
        RequestLog.created_at >= start,
        RequestLog.created_at < end
    ).group_by(RequestLog.agent_id, RequestLog.agent_name)
    
    results = query.all()
    
    agents = []
    for row in results:
        agents.append({
            'agent_id': row.agent_id,
            'agent_name': row.agent_name,
            'count': row.count,
            'tokens': row.tokens or 0
        })
    
    return {
        'period': 'comparison',
        'date': date,
        'agents': agents,
        'total': {
            'count': sum(a['count'] for a in agents),
            'tokens': sum(a['tokens'] for a in agents)
        }
    }
