"""
龙虾办公室 - 任务交接同步模块
从 OpenClaw sessions 提取交接上下文
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional


def extract_session_context(session_path: str, limit: int = 50) -> Dict:
    """
    从 session 文件提取上下文
    
    Args:
        session_path: session 文件路径
        limit: 提取最近多少条消息
    
    Returns:
        上下文数据字典
    """
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 提取最近的消息
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        # 分类消息
        user_messages = []
        assistant_messages = []
        tool_calls = []
        
        for line in recent_lines:
            try:
                msg = json.loads(line)
                role = msg.get('message', {}).get('role', '')
                content = msg.get('message', {}).get('content', [])
                
                if role == 'user':
                    user_messages.append(extract_content(content))
                elif role == 'assistant':
                    assistant_messages.append(extract_content(content))
                elif role == 'toolResult':
                    tool_calls.append({
                        'tool': msg.get('toolName', ''),
                        'result': extract_content(content)
                    })
            except:
                pass
        
        # 提取任务相关信息
        task_info = analyze_task_info(user_messages, assistant_messages)
        
        return {
            'message_count': len(lines),
            'recent_messages': {
                'user': user_messages[-10:],  # 最近 10 条用户消息
                'assistant': assistant_messages[-10:],
                'tool_calls': tool_calls[-10:]
            },
            'task_info': task_info,
            'extracted_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"⚠️ 提取上下文失败：{e}")
        return {}


def extract_content(content_list: List) -> str:
    """从 content 列表提取文本"""
    if not content_list:
        return ""
    
    texts = []
    for item in content_list:
        if isinstance(item, dict):
            if item.get('type') == 'text':
                texts.append(item.get('text', ''))
            elif item.get('type') == 'thinking':
                texts.append(f"[思考] {item.get('thinking', '')}")
        elif isinstance(item, str):
            texts.append(item)
    
    return '\n'.join(texts)


def analyze_task_info(user_messages: List[str], assistant_messages: List[str]) -> Dict:
    """分析任务信息"""
    # 合并消息
    all_text = '\n'.join(user_messages + assistant_messages)
    
    # 提取关键词
    keywords = []
    if '开发' in all_text:
        keywords.append('开发')
    if '部署' in all_text:
        keywords.append('部署')
    if 'API' in all_text:
        keywords.append('API')
    if '前端' in all_text:
        keywords.append('前端')
    if '后端' in all_text:
        keywords.append('后端')
    
    # 估算进度（简单规则）
    progress = estimate_progress(all_text)
    
    # 提取依赖
    dependencies = extract_dependencies(all_text)
    
    return {
        'keywords': keywords,
        'estimated_progress': progress,
        'dependencies': dependencies,
        'summary': generate_summary(user_messages, assistant_messages)
    }


def estimate_progress(text: str) -> float:
    """估算任务进度"""
    # 简单规则
    progress_keywords = {
        '完成': 1.0,
        '已完成': 1.0,
        '做好': 1.0,
        '进行中': 0.5,
        '正在': 0.5,
        '开始': 0.2,
        '准备': 0.1,
        '计划': 0.1
    }
    
    for keyword, progress in progress_keywords.items():
        if keyword in text:
            return progress
    
    return 0.0  # 默认未知


def extract_dependencies(text: str) -> List[str]:
    """提取依赖信息"""
    dependencies = []
    
    # 常见依赖模式
    patterns = [
        '需要',
        '依赖',
        '要求',
        '必须'
    ]
    
    lines = text.split('\n')
    for line in lines:
        for pattern in patterns:
            if pattern in line:
                dependencies.append(line.strip())
                break
    
    return dependencies[:5]  # 最多 5 个依赖


def generate_summary(user_messages: List[str], assistant_messages: List[str]) -> str:
    """生成任务摘要"""
    # 简单摘要：最近的用户消息 + 助手回复
    recent_user = user_messages[-1] if user_messages else ""
    recent_assistant = assistant_messages[-1] if assistant_messages else ""
    
    summary = []
    if recent_user:
        summary.append(f"用户需求：{recent_user[:200]}")
    if recent_assistant:
        summary.append(f"助手回复：{recent_assistant[:200]}")
    
    return '\n'.join(summary)


def get_agent_sessions(agent_id: str) -> List[str]:
    """获取指定 Agent 的 session 文件列表"""
    sessions_dir = os.path.expanduser("~/.openclaw/agents/dev-claw/sessions")
    
    if not os.path.exists(sessions_dir):
        return []
    
    # 查找匹配的 session 文件
    matched = []
    for filename in os.listdir(sessions_dir):
        if not filename.endswith('.jsonl'):
            continue
        
        # 简单匹配：文件名包含 agent_id
        if agent_id.lower() in filename.lower():
            matched.append(os.path.join(sessions_dir, filename))
    
    # 按修改时间排序（最新的在前）
    matched.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return matched


def create_handover_context(from_agent_id: str, to_agent_id: str) -> Dict:
    """
    创建交接上下文
    
    Args:
        from_agent_id: 交出方 Agent ID
        to_agent_id: 接收方 Agent ID
    
    Returns:
        交接上下文数据
    """
    # 获取交出方的 session
    from_sessions = get_agent_sessions(from_agent_id)
    
    if not from_sessions:
        return {
            'error': f'未找到 Agent {from_agent_id} 的 session 记录',
            'context': {}
        }
    
    # 提取最新 session 的上下文
    latest_session = from_sessions[0]
    context = extract_session_context(latest_session)
    
    # 添加交接元数据
    context['handover_meta'] = {
        'from_agent_id': from_agent_id,
        'to_agent_id': to_agent_id,
        'session_file': os.path.basename(latest_session),
        'created_at': datetime.utcnow().isoformat()
    }
    
    return {
        'error': None,
        'context': context
    }
