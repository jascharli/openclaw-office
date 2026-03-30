#!/usr/bin/env python3
"""
创建示例数据库
用于发布时提供干净的示例数据
"""

import sqlite3
import os
from datetime import datetime, timedelta

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'lobster_office.db')

def create_example_database():
    """创建示例数据库"""
    print(f"创建示例数据库: {DB_PATH}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建表
    create_tables(cursor)
    
    # 插入示例数据
    insert_example_data(cursor)
    
    # 提交并关闭
    conn.commit()
    conn.close()
    
    print("示例数据库创建完成！")

def create_tables(cursor):
    """创建表结构"""
    # agent_status 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT UNIQUE,
        agent_name TEXT,
        status TEXT,
        current_task_id TEXT,
        status_message TEXT,
        progress REAL,
        task_count INTEGER,
        request_count INTEGER,
        error_count INTEGER,
        created_at TEXT,
        last_activity TEXT,
        updated_at TEXT
    )
    ''')
    
    # task_records 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE,
        agent_id TEXT,
        task_name TEXT,
        status TEXT,
        progress REAL,
        started_at TEXT,
        updated_at TEXT,
        completed_at TEXT,
        result TEXT,
        error_message TEXT
    )
    ''')
    
    # token_logs 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS token_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT,
        agent_id TEXT,
        model TEXT,
        prompt_tokens INTEGER,
        completion_tokens INTEGER,
        total_tokens INTEGER,
        timestamp TEXT
    )
    ''')
    
    # request_logs 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS request_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT UNIQUE,
        agent_id TEXT,
        agent_name TEXT,
        request_type TEXT,
        model TEXT,
        prompt TEXT,
        prompt_tokens INTEGER,
        completion_tokens INTEGER,
        total_tokens INTEGER,
        latency REAL,
        cost REAL,
        budget_usage REAL,
        success_rate REAL,
        status TEXT,
        error_message TEXT,
        start_time TEXT,
        end_time TEXT,
        duration REAL,
        trace_id TEXT,
        timestamp TEXT,
        provider TEXT
    )
    ''')
    
    # reminder_logs 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reminder_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        reminder_type TEXT,
        message TEXT,
        timestamp TEXT,
        status TEXT
    )
    ''')
    
    # task_handovers 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_handovers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        from_agent TEXT,
        to_agent TEXT,
        reason TEXT,
        timestamp TEXT,
        status TEXT
    )
    ''')
    
    # collaboration_groups 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS collaboration_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT UNIQUE,
        group_name TEXT,
        members TEXT,
        created_at TEXT
    )
    ''')
    
    # sessions 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE,
        agent_id TEXT,
        user_id TEXT,
        start_time TEXT,
        end_time TEXT,
        duration INTEGER,
        status TEXT
    )
    ''')

def insert_example_data(cursor):
    """插入示例数据"""
    now = datetime.now()
    
    # 示例 Agent
    agents = [
        ('agent-001', '开发助手', 'idle', '', '系统就绪', 0.0, 0, 0, 0, now, now, now),
        ('agent-002', '测试助手', 'idle', '', '系统就绪', 0.0, 0, 0, 0, now, now, now),
        ('agent-003', '数据分析', 'idle', '', '系统就绪', 0.0, 0, 0, 0, now, now, now),
        ('agent-004', '客服助手', 'idle', '', '系统就绪', 0.0, 0, 0, 0, now, now, now),
    ]
    
    for agent in agents:
        cursor.execute('''
        INSERT OR REPLACE INTO agent_status 
        (agent_id, agent_name, status, current_task_id, status_message, 
         progress, task_count, request_count, error_count, 
         created_at, last_activity, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', agent)
    
    # 示例任务
    tasks = [
        ('task-001', 'agent-001', '项目初始化', 'completed', 100.0, 
         now - timedelta(hours=2), now - timedelta(hours=1), now - timedelta(hours=1), 
         '项目初始化完成', ''),
    ]
    
    for task in tasks:
        cursor.execute('''
        INSERT OR REPLACE INTO task_records 
        (task_id, agent_id, task_name, status, progress, 
         started_at, updated_at, completed_at, result, error_message) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', task)
    
    # 示例请求日志
    requests = [
        ('req-001', 'agent-001', '开发助手', 'chat', 'gpt-4', '', 10, 20, 30, 
         1.2, 0.01, 0.001, 1.0, 'success', '', now - timedelta(hours=1), 
         now - timedelta(hours=1), 1.2, 'trace-001', now - timedelta(hours=1), 'openai'),
    ]
    
    for req in requests:
        cursor.execute('''
        INSERT OR REPLACE INTO request_logs 
        (request_id, agent_id, agent_name, request_type, model, prompt, 
         prompt_tokens, completion_tokens, total_tokens, latency, cost, 
         budget_usage, success_rate, status, error_message, start_time, 
         end_time, duration, trace_id, timestamp, provider) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', req)
    
    # 示例 Token 日志
    tokens = [
        ('req-001', 'agent-001', 'gpt-4', 10, 20, 30, now - timedelta(hours=1)),
    ]
    
    for token in tokens:
        cursor.execute('''
        INSERT OR REPLACE INTO token_logs 
        (request_id, agent_id, model, prompt_tokens, completion_tokens, total_tokens, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', token)
    
    # 示例提醒日志
    reminders = [
        ('agent-001', 'system', '系统启动完成', now, 'success'),
    ]
    
    for reminder in reminders:
        cursor.execute('''
        INSERT OR REPLACE INTO reminder_logs 
        (agent_id, reminder_type, message, timestamp, status) 
        VALUES (?, ?, ?, ?, ?)
        ''', reminder)
    
    # 示例协作组
    groups = [
        ('group-001', '开发团队', 'agent-001,agent-002', now),
    ]
    
    for group in groups:
        cursor.execute('''
        INSERT OR REPLACE INTO collaboration_groups 
        (group_id, group_name, members, created_at) 
        VALUES (?, ?, ?, ?)
        ''', group)
    
    # 示例会话
    sessions = [
        ('session-001', 'agent-001', 'user-001', now - timedelta(hours=2), 
         now - timedelta(hours=1), 3600, 'completed'),
    ]
    
    for session in sessions:
        cursor.execute('''
        INSERT OR REPLACE INTO sessions 
        (session_id, agent_id, user_id, start_time, end_time, duration, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', session)

if __name__ == '__main__':
    create_example_database()
