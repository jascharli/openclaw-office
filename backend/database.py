"""
OpenClaw 办公室 - 数据库模块
SQLite 数据库 Schema 和 ORM 模型
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os

# 从配置导入时区设置
try:
    from config import config
    # 使用 Config 对象的 get 方法获取配置
    tz_name = config.get("database.timezone", "Asia/Shanghai")
    CONFIG_TZ = ZoneInfo(tz_name)
except ImportError:
    # 如果配置未加载，默认使用北京时间
    CONFIG_TZ = ZoneInfo("Asia/Shanghai")

# UTC 时区
UTC = timezone.utc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'openclaw_office.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AgentStatus(Base):
    """Agent 状态表"""
    __tablename__ = "agent_status"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), nullable=False, unique=True, index=True)
    agent_name = Column(String(200))
    status = Column(String(50), nullable=False)  # idle, conversing, working
    task_id = Column(String(100))
    task_name = Column(String(500))
    progress = Column(Float, default=0.0)
    elapsed_time = Column(Integer, default=0)  # seconds
    estimated_remaining = Column(Integer, default=0)  # seconds
    token_used = Column(Integer, default=0)
    last_activity = Column(DateTime, nullable=False)  # 北京时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_last_activity', 'last_activity'),
    )


class TaskRecord(Base):
    """任务记录表"""
    __tablename__ = "task_records"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), nullable=False, unique=True, index=True)
    task_name = Column(String(500), nullable=False)
    agent_id = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, default='cron')  # session/cron
    session_id = Column(String(100), nullable=True)  # 关联 Session ID
    status = Column(String(50), nullable=False)  # in_progress/completed/cancelled
    priority = Column(Integer, default=2)  # 0:P0, 1:P1, 2:P2, 3:P3
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    token_used = Column(Integer, default=0)
    progress_log = Column(Text)  # JSON 格式的进度日志
    created_at = Column(DateTime, nullable=False, index=True)  # 北京时间
    
    __table_args__ = (
        Index('idx_agent_status', 'agent_id', 'status'),
        Index('idx_created_at', 'created_at'),
    )


class TokenLog(Base):
    """Token 日志表"""
    __tablename__ = "token_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    task_id = Column(String(100))
    token_count = Column(Integer, nullable=False)
    token_type = Column(String(50))  # input, output, total
    action = Column(String(100))  # chat, task, search, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Session(Base):
    """Sessions 表"""
    __tablename__ = "sessions"

    session_id = Column(String(100), primary_key=True, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    last_activity = Column(DateTime, nullable=False, index=True)  # 北京时间
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_agent_activity', 'agent_id', 'last_activity'),
    )


class ReminderLog(Base):
    """督促记录表"""
    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    task_id = Column(String(100))
    reminder_type = Column(String(50))  # auto, manual
    reminder_interval = Column(Integer)  # minutes
    response_status = Column(String(50))  # responded, ignored, blocked
    response_content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TaskHandover(Base):
    """任务交接记录表"""
    __tablename__ = "task_handovers"

    id = Column(Integer, primary_key=True, index=True)
    handover_id = Column(String(100), nullable=False, unique=True, index=True)  # 交接 ID
    task_id = Column(String(100), nullable=False, index=True)  # 任务 ID
    task_name = Column(String(500), nullable=False)  # 任务名称
    
    # 交接双方
    from_agent_id = Column(String(100), nullable=False, index=True)  # 交出方
    from_agent_name = Column(String(200))  # 交出方名称
    to_agent_id = Column(String(100), nullable=False, index=True)  # 接收方
    to_agent_name = Column(String(200))  # 接收方名称
    
    # 交接内容
    handover_type = Column(String(50), nullable=False)  # full: 完整交接，partial: 部分交接，collaboration: 协作
    progress_at_handover = Column(Float, default=0.0)  # 交接时进度
    context_data = Column(Text)  # JSON 格式的上下文数据
    notes = Column(Text)  # 交接说明/备注
    
    # 交接状态
    status = Column(String(50), nullable=False, default='pending')  # pending, accepted, rejected, completed
    accepted_at = Column(DateTime)  # 接收时间
    completed_at = Column(DateTime)  # 完成时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CollaborationGroup(Base):
    """协作组表"""
    __tablename__ = "collaboration_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(100), nullable=False, unique=True, index=True)  # 协作组 ID
    group_name = Column(String(200), nullable=False)  # 协作组名称
    
    # 组成员（JSON 数组）
    # 格式：[{"agent_id": "dev-claw", "role": "lead"}, {"agent_id": "work-claw", "role": "member"}]
    members = Column(Text, nullable=False)
    
    # 当前任务
    active_task_id = Column(String(100))  # 当前任务 ID
    active_task_name = Column(String(500))  # 当前任务名称
    
    # 状态
    status = Column(String(50), default='active')  # active, archived
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RequestLog(Base):
    """大模型请求日志表"""
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), nullable=False, unique=True, index=True)  # 请求 ID
    
    # Agent 信息
    agent_id = Column(String(100), nullable=False, index=True)  # Agent ID
    agent_name = Column(String(200))  # Agent 名称
    
    # 请求信息
    request_type = Column(String(50))  # chat, tool, search, etc.
    provider = Column(String(100))  # 服务商（bailian, openai, anthropic, etc.）
    model_name = Column(String(100))  # 模型名称
    action = Column(String(200))  # 具体动作描述
    
    # Token 统计
    tokens_input = Column(Integer, default=0)  # 输入 Token
    tokens_output = Column(Integer, default=0)  # 输出 Token
    tokens_total = Column(Integer, default=0)  # 总 Token
    tokens_cache_read = Column(Integer, default=0)  # 缓存读取
    tokens_cache_write = Column(Integer, default=0)  # 缓存写入
    
    # 成本统计（如果适用）
    cost_input = Column(Float, default=0.0)  # 输入成本
    cost_output = Column(Float, default=0.0)  # 输出成本
    cost_total = Column(Float, default=0.0)  # 总成本
    
    # 响应信息
    status = Column(String(50), default='success')  # success, error
    error_message = Column(Text)  # 错误信息
    response_time_ms = Column(Integer)  # 响应时间（毫秒）
    
    # 上下文信息
    session_id = Column(String(100), index=True)  # Session ID
    task_id = Column(String(100))  # 任务 ID
    message_id = Column(String(100))  # 消息 ID
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class HealthLog(Base):
    """服务健康检测日志表"""
    __tablename__ = "health_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(50), nullable=False, index=True)  # 服务名称：backend/frontend/openclaw
    status = Column(String(20), nullable=False)  # 状态：healthy/unhealthy/restarted/error
    message = Column(Text)  # 详细信息/错误原因
    action = Column(String(50))  # 执行的操作：none/restart/notify
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_utc(dt):
    """将带时区的 datetime 转换为 UTC 时间（不带时区）"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # 假设是本地时间，转换为 UTC
        return dt.replace(tzinfo=CONFIG_TZ).astimezone(UTC).replace(tzinfo=None)
    # 已经带时区，直接转换为 UTC
    return dt.astimezone(UTC).replace(tzinfo=None)


def to_local_time(utc_dt):
    """将 UTC 时间（不带时区）转换为本地时区"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        # 假设是 UTC 时间，转换为本地时区
        return utc_dt.replace(tzinfo=UTC).astimezone(CONFIG_TZ)
    # 已经带时区，直接转换
    return utc_dt.astimezone(CONFIG_TZ)


def get_current_utc():
    """获取当前 UTC 时间（不带时区）"""
    return datetime.now(UTC).replace(tzinfo=None)


# 测试用示例数据
def seed_sample_data():
    """插入示例数据用于测试"""
    db = SessionLocal()
    try:
        # 清空现有数据
        db.query(AgentStatus).delete()
        db.query(TaskRecord).delete()
        
        # 示例 Agent 状态
        agents = [
            AgentStatus(
                agent_id="main",
                agent_name="大白 AI",
                status="conversing",
                task_id=None,
                task_name=None,
                progress=0,
                elapsed_time=1800,
                token_used=5420
            ),
            AgentStatus(
                agent_id="dev-claw",
                agent_name="dev-claw",
                status="working",
                task_id="task-001",
                task_name="OpenClaw 办公室开发",
                progress=0.45,
                elapsed_time=8130,
                estimated_remaining=5400,
                token_used=15420
            ),
            AgentStatus(
                agent_id="work-claw",
                agent_name="work-claw",
                status="idle",
                task_id=None,
                task_name=None,
                progress=0,
                elapsed_time=0,
                token_used=0
            ),
        ]
        
        for agent in agents:
            db.add(agent)
        
        # 示例任务
        tasks = [
            TaskRecord(
                task_id="task-001",
                task_name="OpenClaw 办公室开发",
                agent_id="dev-claw",
                status="in_progress",
                priority=0,
                token_used=15420
            ),
            TaskRecord(
                task_id="task-002",
                task_name="企业微信对接",
                agent_id="dev-claw",
                status="pending",
                priority=0,
            ),
            TaskRecord(
                task_id="task-003",
                task_name="文档整理",
                agent_id="work-claw",
                status="pending",
                priority=2,
            ),
        ]
        
        for task in tasks:
            db.add(task)
        
        db.commit()
        print("✅ 示例数据已插入")
    except Exception as e:
        db.rollback()
        print(f"❌ 插入示例数据失败：{e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🦞 初始化 OpenClaw 办公室数据库...")
    init_db()
    seed_sample_data()
    print("✅ 数据库初始化完成")
