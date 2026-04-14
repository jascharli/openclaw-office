import os
import sys
import subprocess
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal, HealthLog, to_local_time, get_current_utc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

CONFIG = {
    "enabled": True,
    "interval_hours": 3,
    "failure_threshold": 2,
    "restart_timeout": 60,
    "auto_restart": True,
    "log_retention_hours": 48
}

failure_counts = {
    "backend": 0,
    "frontend": 0,
    "openclaw": 0
}


def check_backend_health() -> Dict:
    """检测后端服务健康状态"""
    try:
        response = requests.get(f"http://localhost:{BACKEND_PORT}/health", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "message": "Backend service is running"}
        else:
            return {"status": "unhealthy", "message": f"Backend returned status {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "unhealthy", "message": "Connection refused - backend service not running"}
    except requests.exceptions.Timeout:
        return {"status": "unhealthy", "message": "Connection timeout"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


def check_frontend_health() -> Dict:
    """检测前端服务健康状态"""
    try:
        response = requests.get(f"http://localhost:{FRONTEND_PORT}/", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "message": "Frontend service is running"}
        else:
            return {"status": "unhealthy", "message": f"Frontend returned status {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "unhealthy", "message": "Connection refused - frontend service not running"}
    except requests.exceptions.Timeout:
        return {"status": "unhealthy", "message": "Connection timeout"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


def check_openclaw_gateway() -> Dict:
    """检测OpenClaw Gateway健康状态"""
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {"status": "healthy", "message": "OpenClaw Gateway is running"}
        else:
            return {"status": "unhealthy", "message": f"Gateway error: {result.stderr}"}
    except subprocess.TimeoutExpired:
        return {"status": "unhealthy", "message": "Gateway health check timeout"}
    except FileNotFoundError:
        return {"status": "unhealthy", "message": "openclaw command not found"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}


def check_openclaw_cron() -> Dict:
    """检测OpenClaw Cron对接状态"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "ID" in result.stdout:
            return {"status": "healthy", "message": "OpenClaw Cron is accessible", "tasks_count": result.stdout.count("\n")}
        else:
            return {"status": "warning", "message": f"Cron list error: {result.stderr}"}
    except subprocess.TimeoutExpired:
        return {"status": "warning", "message": "Cron list timeout"}
    except Exception as e:
        return {"status": "warning", "message": str(e)}


def restart_backend() -> bool:
    """重启后端服务"""
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "start.sh")
        if os.path.exists(script_path):
            subprocess.Popen(
                ["bash", script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to restart backend: {e}")
        return False


def restart_frontend() -> bool:
    """重启前端服务"""
    try:
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
        subprocess.Popen(
            ["python3", "-m", "http.server", str(FRONTEND_PORT)],
            cwd=frontend_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        logger.error(f"Failed to restart frontend: {e}")
        return False


def restart_openclaw_gateway() -> bool:
    """重启OpenClaw Gateway"""
    try:
        subprocess.run(
            ["openclaw", "gateway", "restart"],
            capture_output=True,
            timeout=30
        )
        return True
    except Exception as e:
        logger.error(f"Failed to restart OpenClaw Gateway: {e}")
        return False


def log_health_status(db: Session, service_name: str, status: str, message: str, action: str = "none"):
    """记录健康检测日志到数据库"""
    try:
        log = HealthLog(
            service_name=service_name,
            status=status,
            message=message,
            action=action,
            created_at=get_current_utc()
        )
        db.add(log)
        db.commit()
        logger.info(f"Health log recorded: {service_name} - {status}")
    except Exception as e:
        logger.error(f"Failed to log health status: {e}")
        db.rollback()


def perform_health_check():
    """执行健康检测并根据配置自动恢复"""
    global failure_counts
    
    logger.info("=" * 50)
    logger.info("开始执行健康检测")
    logger.info("=" * 50)
    
    results = {}
    db = SessionLocal()
    
    try:
        backend_result = check_backend_health()
        results["backend"] = backend_result["status"]
        
        if backend_result["status"] == "healthy":
            failure_counts["backend"] = 0
            log_health_status(db, "backend", "healthy", backend_result["message"])
        else:
            failure_counts["backend"] += 1
            if failure_counts["backend"] >= CONFIG["failure_threshold"] and CONFIG["auto_restart"]:
                logger.warning(f"Backend连续{failure_counts['backend']}次检测失败，尝试重启...")
                if restart_backend():
                    log_health_status(db, "backend", "restarted", "Service restarted", "restart")
                    failure_counts["backend"] = 0
                else:
                    log_health_status(db, "backend", "error", "Failed to restart service", "restart")
            else:
                log_health_status(db, "backend", "unhealthy", backend_result["message"])
        
        frontend_result = check_frontend_health()
        results["frontend"] = frontend_result["status"]
        
        if frontend_result["status"] == "healthy":
            failure_counts["frontend"] = 0
            log_health_status(db, "frontend", "healthy", frontend_result["message"])
        else:
            failure_counts["frontend"] += 1
            if failure_counts["frontend"] >= CONFIG["failure_threshold"] and CONFIG["auto_restart"]:
                logger.warning(f"Frontend连续{failure_counts['frontend']}次检测失败，尝试重启...")
                if restart_frontend():
                    log_health_status(db, "frontend", "restarted", "Service restarted", "restart")
                    failure_counts["frontend"] = 0
                else:
                    log_health_status(db, "frontend", "error", "Failed to restart service", "restart")
            else:
                log_health_status(db, "frontend", "unhealthy", frontend_result["message"])
        
        openclaw_result = check_openclaw_gateway()
        results["openclaw"] = openclaw_result["status"]
        
        if openclaw_result["status"] == "healthy":
            failure_counts["openclaw"] = 0
            log_health_status(db, "openclaw", "healthy", openclaw_result["message"])
            
            cron_result = check_openclaw_cron()
            if cron_result["status"] == "healthy":
                log_health_status(db, "openclaw_cron", "healthy", cron_result["message"])
            else:
                log_health_status(db, "openclaw_cron", "warning", cron_result["message"])
        else:
            failure_counts["openclaw"] += 1
            if failure_counts["openclaw"] >= CONFIG["failure_threshold"] and CONFIG["auto_restart"]:
                logger.warning(f"OpenClaw Gateway连续{failure_counts['openclaw']}次检测失败，尝试重启...")
                if restart_openclaw_gateway():
                    log_health_status(db, "openclaw", "restarted", "Gateway restarted", "restart")
                    failure_counts["openclaw"] = 0
                else:
                    log_health_status(db, "openclaw", "error", "Failed to restart gateway", "restart")
            else:
                log_health_status(db, "openclaw", "unhealthy", openclaw_result["message"])
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
    finally:
        db.close()
    
    logger.info(f"健康检测完成，结果: {results}")
    return results


def get_health_logs(hours: int = 48, service: str = None) -> List[Dict]:
    """获取健康检测日志"""
    db = SessionLocal()
    try:
        cutoff_time = get_current_utc() - timedelta(hours=hours)
        query = db.query(HealthLog).filter(HealthLog.created_at >= cutoff_time)
        
        if service and service != "all":
            query = query.filter(HealthLog.service_name == service)
        
        logs = query.order_by(HealthLog.created_at.desc()).all()
        
        return [{
            "id": log.id,
            "service_name": log.service_name,
            "status": log.status,
            "message": log.message,
            "action": log.action,
            "created_at": to_local_time(log.created_at).strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None
        } for log in logs]
    finally:
        db.close()


def cleanup_old_logs(retention_hours: int = 48):
    """清理过期的健康检测日志"""
    db = SessionLocal()
    try:
        cutoff_time = get_current_utc() - timedelta(hours=retention_hours)
        deleted = db.query(HealthLog).filter(HealthLog.created_at < cutoff_time).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} old health logs")
        return deleted
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    print("执行健康检测...")
    result = perform_health_check()
    print(f"\n检测结果: {result}")
    
    print("\n获取最近健康日志:")
    logs = get_health_logs(hours=48)
    print(f"共 {len(logs)} 条日志")
    for log in logs[:5]:
        print(f"  - {log['created_at']} | {log['service_name']} | {log['status']}")
