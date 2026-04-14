"""
龙虾办公室 - 调度器模块
包含：
1. 自动督促调度器（ReminderScheduler）
2. 数据采集调度器（DataSyncScheduler）
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import asyncio
from typing import Dict, List, Callable
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import AgentStatus, TaskRecord, ReminderLog, get_db, to_local_time, to_utc, UTC, get_current_utc
from config import config
from feishu_notify import send_reminder_notification
from websocket import broadcast_reminder
from request_sync import sync_request_logs
from openclaw_sync import sync_to_database as sync_agent_status
from cron_sync import sync_cron_to_database
from session_sync import sync_sessions_to_database
from task_sync import sync_session_tasks_to_database, merge_and_deduplicate_tasks


class ReminderScheduler:
    """自动督促调度器"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 300  # 每 5 分钟检查一次（300 秒）
        self.rules = {
            # 规则：任务超时督促
            "task_overtime": {
                "enabled": True,
                "threshold_minutes": 30,  # 超过预计时间 30 分钟
            },
            # 规则：长时间无更新督促
            "no_update": {
                "enabled": True,
                "threshold_minutes": 30,  # 30 分钟无状态更新
            },
            # 规则：Token 超预算督促
            "token_budget": {
                "enabled": True,
                "threshold_tokens": 100000,  # 单任务超 10 万 Token
            },
            # 规则：进度停滞督促
            "progress_stuck": {
                "enabled": True,
                "threshold_minutes": 30,  # 30 分钟进度无变化
            }
        }
    
    async def start(self, db_func):
        """启动调度器"""
        self.running = True
        print(f"⏰ 自动督促调度器已启动（每{self.check_interval/60:.0f}分钟检查一次）")
        
        while self.running:
            db = None
            try:
                db = next(db_func())
                await self.check_rules(db)
            except Exception as e:
                print(f"❌ 调度器检查失败：{e}")
            finally:
                if db is not None:
                    try:
                        db.close()
                    except:
                        pass
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """停止调度器"""
        self.running = False
        print("⏹️ 自动督促调度器已停止")
    
    async def check_rules(self, db: Session):
        """检查所有规则"""
        agents = db.query(AgentStatus).all()
        # 使用 UTC 时间进行计算
        now_utc = datetime.now(UTC)
        # 转换为本地时区用于展示
        now_local = now_utc
        
        for agent in agents:
            # 只检查工作中的 Agent
            if agent.status != "working":
                continue
            
            # 规则 1: 任务超时督促
            if self.rules["task_overtime"]["enabled"]:
                await self.check_task_overtime(db, agent, now_utc)
            
            # 规则 2: 长时间无更新督促
            if self.rules["no_update"]["enabled"]:
                await self.check_no_update(db, agent, now_utc)
            
            # 规则 3: Token 超预算督促
            if self.rules["token_budget"]["enabled"]:
                await self.check_token_budget(db, agent)
            
            # 规则 4: 进度停滞督促
            if self.rules["progress_stuck"]["enabled"]:
                await self.check_progress_stuck(db, agent, now_utc)
    
    async def check_task_overtime(self, db: Session, agent: AgentStatus, now: datetime):
        """检查任务超时"""
        if not agent.estimated_remaining:
            return
        
        # 计算预计总时间
        estimated_total = agent.elapsed_time + agent.estimated_remaining
        threshold = self.rules["task_overtime"]["threshold_minutes"] * 60
        
        # 如果已用时间超过预计总时间 + 阈值
        if agent.elapsed_time > (estimated_total + threshold):
            await self.send_auto_reminder(
                db, agent,
                reason=f"任务超时（已超{int((agent.elapsed_time - estimated_total) / 60)}分钟）"
            )
    
    async def check_no_update(self, db: Session, agent: AgentStatus, now: datetime):
        """检查长时间无更新"""
        if not agent.last_activity:
            return
        
        threshold = timedelta(minutes=self.rules["no_update"]["threshold_minutes"])
        
        # 确保 last_activity 是带时区的 UTC 时间
        if agent.last_activity.tzinfo is None:
            last_activity_utc = agent.last_activity.replace(tzinfo=UTC)
        else:
            last_activity_utc = agent.last_activity
        
        if now - last_activity_utc > threshold:
            # 计算分钟数
            minutes = int((now - last_activity_utc).total_seconds() / 60)
            await self.send_auto_reminder(
                db, agent,
                reason=f"长时间无状态更新（{minutes}分钟）"
            )
    
    async def check_token_budget(self, db: Session, agent: AgentStatus):
        """检查 Token 超预算"""
        threshold = self.rules["token_budget"]["threshold_tokens"]
        
        if agent.token_used > threshold:
            await self.send_auto_reminder(
                db, agent,
                reason=f"Token 超预算（已用{agent.token_used:,}，阈值{threshold:,}）"
            )
    
    async def check_progress_stuck(self, db: Session, agent: AgentStatus, now: datetime):
        """检查进度停滞"""
        # 查询最近一次督促记录
        last_reminder = db.query(ReminderLog).filter(
            ReminderLog.agent_id == agent.agent_id,
            ReminderLog.reminder_type == "auto"
        ).order_by(ReminderLog.created_at.desc()).first()
        
        # 如果最近有督促，且间隔不到阈值时间，跳过
        if last_reminder:
            threshold = timedelta(minutes=self.rules["progress_stuck"]["threshold_minutes"])
            # 确保 created_at 是带时区的 UTC 时间
            if last_reminder.created_at.tzinfo is None:
                created_at_utc = last_reminder.created_at.replace(tzinfo=UTC)
            else:
                created_at_utc = last_reminder.created_at
            if now - created_at_utc < threshold:
                return
        
        # TODO: 需要记录进度历史才能检测停滞
        # 暂时简化：如果进度<100% 且 elapsed_time>20 分钟，督促
        if agent.progress < 1.0 and agent.elapsed_time > (self.rules["progress_stuck"]["threshold_minutes"] * 60):
            await self.send_auto_reminder(
                db, agent,
                reason=f"任务进行中（{agent.progress*100:.0f}%, {int(agent.elapsed_time/60)}分钟）"
            )
    
    async def send_auto_reminder(self, db: Session, agent: AgentStatus, reason: str):
        """发送自动督促消息"""
        print(f"🔔 自动督促 {agent.agent_id}: {reason}")
        
        # 记录督促日志
        reminder = ReminderLog(
            agent_id=agent.agent_id,
            task_id=agent.task_id,
            reminder_type="auto",
            reminder_interval=0,
            response_status="sent",
            response_content=reason
        )
        db.add(reminder)
        db.commit()
        
        # 发送飞书通知
        feishu_result = send_reminder_notification(
            agent_id=agent.agent_id,
            agent_name=agent.agent_name or agent.agent_id,
            task_name=agent.task_name or "未知任务",
            progress=agent.progress,
            elapsed_time=agent.elapsed_time,
            reminder_type="auto"
        )
        
        # WebSocket 广播
        asyncio.create_task(broadcast_reminder({
            "agent_id": agent.agent_id,
            "reminder_type": "auto",
            "reason": reason,
            "feishu_result": feishu_result
        }))


# ==================== 数据采集调度器 ====================

class DataSyncScheduler:
    """数据采集调度器 - 定时同步 OpenClaw 数据"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db_func = None
        self.running = False
        
        # 从配置文件读取同步频率设置
        sync_intervals = config.config.get('sync_intervals', {})
        
        # 默认配置（可从 config.json 读取）
        self.config = {
            "request_sync_interval_minutes": sync_intervals.get('request_sync_interval_minutes', 15),   # 请求日志同步频率（15 分钟）
            "agent_sync_interval_minutes": sync_intervals.get('agent_sync_interval_minutes', 5),      # Agent 状态同步频率（5 分钟）
            "session_sync_interval_minutes": sync_intervals.get('session_sync_interval_minutes', 30),   # Session 同步频率（30 分钟）
            "task_sync_interval_minutes": sync_intervals.get('task_sync_interval_minutes', 10),      # 任务同步频率（10 分钟）
            "cron_sync_interval_minutes": sync_intervals.get('cron_sync_interval_minutes', 90),      # Cron 任务同步频率（90 分钟）
            "request_lookback_hours": 6,         # 请求日志回溯时间
            "agent_lookback_hours": 1,           # Agent 状态回溯时间
            "session_lookback_hours": 24,        # Session 回溯时间
        }
        
        print(f"📝 数据采集调度器配置：{self.config}")
    
    def start(self, db_func):
        """启动调度器"""
        self.db_func = db_func
        self.running = True
        
        # 添加定时任务
        self._add_jobs()
        
        # 启动调度器
        self.scheduler.start()
        print("⏰ 数据采集调度器已启动")
        print(f"   - Agent 状态同步：每{self.config['agent_sync_interval_minutes']}分钟（回溯{self.config['agent_lookback_hours']}小时）")
        print(f"   - 任务同步：每{self.config['task_sync_interval_minutes']}分钟")
        print(f"   - 请求日志同步：每{self.config['request_sync_interval_minutes']}分钟（回溯{self.config['request_lookback_hours']}小时）")
        print(f"   - Session 同步：每{self.config['session_sync_interval_minutes']}分钟（回溯{self.config['session_lookback_hours']}小时）")
        print(f"   - Cron 任务同步：每{self.config['cron_sync_interval_minutes']}分钟")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        self.scheduler.shutdown(wait=False)
        print("⏹️ 数据采集调度器已停止")
    
    def _add_jobs(self):
        """添加定时任务"""
        # 任务 1: 同步请求日志
        self.scheduler.add_job(
            func=self._sync_request_logs_job,
            trigger=IntervalTrigger(minutes=self.config['request_sync_interval_minutes']),
            id='sync_request_logs',
            name='同步请求日志',
            replace_existing=True
        )
        
        # 任务 2: 同步 Agent 状态
        self.scheduler.add_job(
            func=self._sync_agent_status_job,
            trigger=IntervalTrigger(minutes=self.config['agent_sync_interval_minutes']),
            id='sync_agent_status',
            name='同步 Agent 状态',
            replace_existing=True
        )
        
        # 任务 3: 同步 Cron 任务
        self.scheduler.add_job(
            func=self._sync_cron_tasks_job,
            trigger=IntervalTrigger(minutes=self.config['cron_sync_interval_minutes']),
            id='sync_cron_tasks',
            name='同步 Cron 任务',
            replace_existing=True
        )
        
        # 任务 4: 同步 Sessions（每 5 分钟同步）
        self.scheduler.add_job(
            func=self._sync_sessions_job,
            trigger=IntervalTrigger(minutes=self.config['session_sync_interval_minutes']),
            id='sync_sessions',
            name='同步 Sessions',
            replace_existing=True
        )
        
        # 任务 5: 同步任务（每 10 分钟同步）
        self.scheduler.add_job(
            func=self._sync_tasks_job,
            trigger=IntervalTrigger(minutes=self.config['task_sync_interval_minutes']),
            id='sync_tasks',
            name='同步任务',
            replace_existing=True
        )
    
    def _sync_request_logs_job(self):
        """同步请求日志任务"""
        db = None
        try:
            db = next(self.db_func())
            lookback_hours = self.config['request_lookback_hours']
            
            print(f"🔄 开始同步请求日志（最近{lookback_hours}小时）...")
            count = sync_request_logs(db, lookback_hours=lookback_hours)
            db.commit()
            print(f"✅ 同步完成：{count} 条记录")
        except Exception as e:
            print(f"❌ 请求日志同步失败：{e}")
        finally:
            if db is not None:
                try:
                    db.close()
                except:
                    pass
    
    def _sync_agent_status_job(self):
        """同步 Agent 状态任务"""
        db = None
        try:
            db = next(self.db_func())
            
            print(f"🔄 开始同步 Agent 状态...")
            count = sync_agent_status(db)
            db.commit()
            print(f"✅ 同步完成：{count} 个 Agent")
        except Exception as e:
            print(f"❌ Agent 状态同步失败：{e}")
        finally:
            if db is not None:
                try:
                    db.close()
                except:
                    pass
    
    def _sync_cron_tasks_job(self):
        """同步 Cron 任务"""
        try:
            print(f"🔄 开始同步 Cron 任务...")
            sync_cron_to_database()
            print(f"✅ Cron 任务同步完成")
        except Exception as e:
            print(f"❌ Cron 任务同步失败：{e}")
    
    def _sync_sessions_job(self):
        """同步 Sessions 任务"""
        try:
            print(f"🔄 开始同步 Sessions...")
            sync_sessions_to_database()
        except Exception as e:
            print(f"❌ Session 同步失败：{e}")
    
    def _sync_tasks_job(self):
        """同步任务（Session + Cron）"""
        db = None
        try:
            db = next(self.db_func())
            
            print(f"🔄 开始同步 Session 任务...")
            count = sync_session_tasks_to_database()
            db.commit()
            print(f"✅ Session 任务同步完成：{count} 个")
            
            print(f"🔄 开始任务去重...")
            merge_and_deduplicate_tasks()
        except Exception as e:
            print(f"❌ 任务同步失败：{e}")
        finally:
            if db is not None:
                try:
                    db.close()
                except:
                    pass
    
    def load_config(self, config: Dict):
        """加载配置"""
        if 'data_sync' in config:
            self.config.update(config['data_sync'])
            print(f"📝 数据采集配置已更新：{self.config}")
    
    def reload_config(self):
        """重新加载配置并更新定时任务"""
        # 从配置文件读取同步频率设置
        sync_intervals = config.config.get('sync_intervals', {})
        
        # 更新配置
        self.config = {
            "request_sync_interval_minutes": sync_intervals.get('request_sync_interval_minutes', 15),   # 请求日志同步频率（15 分钟）
            "agent_sync_interval_minutes": sync_intervals.get('agent_sync_interval_minutes', 5),      # Agent 状态同步频率（5 分钟）
            "session_sync_interval_minutes": sync_intervals.get('session_sync_interval_minutes', 30),   # Session 同步频率（30 分钟）
            "task_sync_interval_minutes": sync_intervals.get('task_sync_interval_minutes', 10),      # 任务同步频率（10 分钟）
            "cron_sync_interval_minutes": sync_intervals.get('cron_sync_interval_minutes', 90),      # Cron 任务同步频率（90 分钟）
            "request_lookback_hours": 6,         # 请求日志回溯时间
            "agent_lookback_hours": 1,           # Agent 状态回溯时间
            "session_lookback_hours": 24,        # Session 回溯时间
        }
        
        print(f"📝 数据采集调度器配置已重新加载：{self.config}")
        
        # 如果调度器正在运行，重新添加定时任务
        if self.running and self.scheduler.running:
            print("🔄 重新更新定时任务...")
            self._add_jobs()
            print("✅ 定时任务已更新")


# ==================== 全局调度器 ====================

# 督促调度器
reminder_scheduler = ReminderScheduler()

# 数据采集调度器
data_sync_scheduler = DataSyncScheduler()


async def start_reminder_scheduler(db_func):
    """启动督促调度器"""
    await reminder_scheduler.start(db_func)


def stop_reminder_scheduler():
    """停止督促调度器"""
    reminder_scheduler.stop()


def start_data_sync_scheduler(db_func):
    """启动数据采集调度器"""
    data_sync_scheduler.start(db_func)


def stop_data_sync_scheduler():
    """停止数据采集调度器"""
    data_sync_scheduler.stop()


# ==================== 健康检测调度器 ====================

class HealthCheckScheduler:
    """健康检测调度器 - 定时检测服务健康状态"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False
        self.config = {
            "enabled": True,
            "interval_hours": 3,
            "failure_threshold": 2,
            "auto_restart": True,
            "log_retention_hours": 48
        }
    
    def start(self):
        """启动健康检测调度器"""
        if not self.config["enabled"]:
            print("⚠️ 健康检测功能已禁用")
            return
        
        self.running = True
        
        self.scheduler.add_job(
            func=self._health_check_job,
            trigger=IntervalTrigger(hours=self.config["interval_hours"]),
            id='health_check',
            name='服务健康检测',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            func=self._cleanup_logs_job,
            trigger=IntervalTrigger(hours=24),
            id='cleanup_health_logs',
            name='清理过期健康日志',
            replace_existing=True
        )
        
        self.scheduler.start()
        print(f"⏰ 健康检测调度器已启动（每{self.config['interval_hours']}小时检测一次）")
    
    def stop(self):
        """停止健康检测调度器"""
        self.running = False
        self.scheduler.shutdown(wait=False)
        print("⏹️ 健康检测调度器已停止")
    
    def _health_check_job(self):
        """执行健康检测"""
        from health_check import perform_health_check
        try:
            result = perform_health_check()
            print(f"✅ 健康检测完成: {result}")
        except Exception as e:
            print(f"❌ 健康检测失败: {e}")
    
    def _cleanup_logs_job(self):
        """清理过期日志"""
        from health_check import cleanup_old_logs
        try:
            deleted = cleanup_old_logs(self.config["log_retention_hours"])
            print(f"🧹 清理了 {deleted} 条过期健康日志")
        except Exception as e:
            print(f"❌ 清理日志失败: {e}")


health_check_scheduler = HealthCheckScheduler()


def start_health_check_scheduler():
    """启动健康检测调度器"""
    health_check_scheduler.start()


def stop_health_check_scheduler():
    """停止健康检测调度器"""
    health_check_scheduler.stop()


def stop_scheduler():
    """停止所有调度器"""
    stop_reminder_scheduler()
    stop_data_sync_scheduler()
    stop_health_check_scheduler()
