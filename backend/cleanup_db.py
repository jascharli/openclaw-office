#!/usr/bin/env python3
"""
清理并创建示例数据库
用于发布时提供干净的示例数据
"""

import sqlite3
import os
from datetime import datetime, timedelta

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'lobster_office.db')

def cleanup_and_create_example():
    """清理并创建示例数据库"""
    print(f"清理并创建示例数据库: {DB_PATH}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清理现有数据
    cleanup_tables(cursor)
    
    # 插入示例数据
    insert_example_data(cursor)
    
    # 提交并关闭
    conn.commit()
    conn.close()
    
    print("示例数据库创建完成！")
    print("数据库已清理，包含干净的示例数据。")

def cleanup_tables(cursor):
    """清理所有表的数据"""
    tables = [
        'agent_status',
        'task_records',
        'token_logs',
        'request_logs',
        'reminder_logs',
        'task_handovers',
        'collaboration_groups',
        'sessions'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"清理表: {table}")
        except Exception as e:
            print(f"清理表 {table} 时出错: {e}")

def insert_example_data(cursor):
    """插入示例数据"""
    now = datetime.now()
    
    # 示例 Agent（使用干净的名称）
    agents = [
        ('agent-001', '开发助手', 'idle', None, None, 0.0, 0, 0, 0, now, now, now),
        ('agent-002', '测试助手', 'idle', None, None, 0.0, 0, 0, 0, now, now, now),
        ('agent-003', '数据分析', 'idle', None, None, 0.0, 0, 0, 0, now, now, now),
        ('agent-004', '客服助手', 'idle', None, None, 0.0, 0, 0, 0, now, now, now),
        ('agent-005', '设计助手', 'idle', None, None, 0.0, 0, 0, 0, now, now, now),
    ]
    
    for agent in agents:
        try:
            cursor.execute('''
            INSERT INTO agent_status 
            (agent_id, agent_name, status, task_id, task_name, 
             progress, elapsed_time, estimated_remaining, token_used, 
             last_activity, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', agent)
        except Exception as e:
            print(f"插入 Agent 数据时出错: {e}")
    
    # 示例任务
    tasks = [
        ('task-001', 'agent-001', '项目初始化', 'completed', 100.0, 
         now - timedelta(hours=2), now - timedelta(hours=1), now - timedelta(hours=1), 
         '项目初始化完成', ''),
        ('task-002', 'agent-002', '系统测试', 'completed', 100.0, 
         now - timedelta(hours=1.5), now - timedelta(hours=0.5), now - timedelta(hours=0.5), 
         '测试通过', ''),
    ]
    
    for task in tasks:
        try:
            cursor.execute('''
            INSERT INTO task_records 
            (task_id, agent_id, task_name, status, progress, 
             started_at, updated_at, completed_at, result, error_message) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', task)
        except Exception as e:
            print(f"插入任务数据时出错: {e}")
    
    # 示例请求日志
    requests = [
        ('req-001', 'agent-001', '开发助手', 'chat', 'gpt-4', '', 10, 20, 30, 
         1.2, 0.01, 0.001, 1.0, 'success', '', now - timedelta(hours=1), 
         now - timedelta(hours=1), 1.2, 'trace-001', now - timedelta(hours=1), 'openai'),
        ('req-002', 'agent-002', '测试助手', 'chat', 'gpt-3.5', '', 8, 15, 23, 
         0.8, 0.002, 0.0002, 1.0, 'success', '', now - timedelta(hours=0.5), 
         now - timedelta(hours=0.5), 0.8, 'trace-002', now - timedelta(hours=0.5), 'openai'),
    ]
    
    for req in requests:
        try:
            cursor.execute('''
            INSERT INTO request_logs 
            (request_id, agent_id, agent_name, request_type, model, prompt, 
             prompt_tokens, completion_tokens, total_tokens, latency, cost, 
             budget_usage, success_rate, status, error_message, start_time, 
             end_time, duration, trace_id, timestamp, provider) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', req)
        except Exception as e:
            print(f"插入请求日志时出错: {e}")
    
    # 示例 Token 日志
    tokens = [
        ('req-001', 'agent-001', 'gpt-4', 10, 20, 30, now - timedelta(hours=1)),
        ('req-002', 'agent-002', 'gpt-3.5', 8, 15, 23, now - timedelta(hours=0.5)),
    ]
    
    for token in tokens:
        try:
            cursor.execute('''
            INSERT INTO token_logs 
            (request_id, agent_id, model, prompt_tokens, completion_tokens, total_tokens, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', token)
        except Exception as e:
            print(f"插入 Token 日志时出错: {e}")

if __name__ == '__main__':
    cleanup_and_create_example()
