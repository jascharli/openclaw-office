"""
龙虾办公室 - 飞书通知模块
集成飞书机器人发送督促消息
"""

import requests
import json
from datetime import datetime
from typing import Optional
import os

# 飞书 Webhook URL（从环境变量读取）
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")


def send_feishu_notification(
    title: str,
    content: str,
    mention_all: bool = False,
    webhook_url: Optional[str] = None
) -> dict:
    """
    发送飞书消息（使用 text 类型，兼容性更好）
    
    Args:
        title: 消息标题
        content: 消息内容
        mention_all: 是否@所有人
        webhook_url: 飞书 Webhook URL（可选，默认使用环境变量）
    
    Returns:
        dict: 发送结果
    """
    url = webhook_url or FEISHU_WEBHOOK_URL
    
    if not url:
        print("⚠️ 飞书 Webhook URL 未配置，跳过通知发送")
        return {"success": False, "error": "Webhook URL not configured"}
    
    # 构建消息内容（使用 text 类型，兼容性更好）
    full_content = f"{title}\n\n{content}\n\n发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    message = {
        "msg_type": "text",
        "content": {
            "text": full_content
        }
    }
    
    # 如果需要@所有人（text 类型使用@all）
    if mention_all:
        message["content"]["text"] += "\n@所有人"
    
    try:
        response = requests.post(
            url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        result = response.json()
        
        if result.get("StatusCode") == 0 or result.get("code") == 0:
            print(f"✅ 飞书通知发送成功：{title}")
            return {"success": True, "response": result}
        else:
            print(f"❌ 飞书通知发送失败：{result}")
            return {"success": False, "error": result}
    
    except Exception as e:
        print(f"❌ 发送飞书通知异常：{e}")
        return {"success": False, "error": str(e)}


def send_reminder_notification(
    agent_id: str,
    agent_name: str,
    task_name: str,
    progress: float,
    elapsed_time: int,
    reminder_type: str = "auto"
) -> dict:
    """
    发送督促通知
    
    Args:
        agent_id: Agent ID
        agent_name: Agent 名称
        task_name: 任务名称
        progress: 进度（0-1）
        elapsed_time: 已用时间（秒）
        reminder_type: 督促类型（auto/manual）
    
    Returns:
        dict: 发送结果
    """
    # 格式化时间
    hours = elapsed_time // 3600
    minutes = (elapsed_time % 3600) // 60
    time_str = f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟"
    
    # 构建消息内容
    title = "🦞 龙虾办公室 - 任务督促"
    
    content = f"""【任务督促】{agent_name}

📋 任务：{task_name}
📊 进度：{progress*100:.0f}%
⏱️  已用：{time_str}
🔔 类型：{'自动督促' if reminder_type == 'auto' else '手动督促'}

请汇报当前进度和是否有阻塞问题。

回复格式：
- 进度：XX%
- 状态：正常/阻塞/需要帮助
- 下一步：...
"""
    
    return send_feishu_notification(title, content, mention_all=False)


def send_alert_notification(
    alert_type: str,
    title: str,
    content: str,
    level: str = "warning"
) -> dict:
    """
    发送告警通知
    
    Args:
        alert_type: 告警类型
        title: 告警标题
        content: 告警内容
        level: 告警级别（warning/error/info）
    
    Returns:
        dict: 发送结果
    """
    emoji = {"warning": "⚠️", "error": "❌", "info": "ℹ️"}.get(level, "📢")
    
    full_title = f"{emoji} 龙虾办公室 - {alert_type}"
    full_content = f"""【{alert_type}】

{content}

级别：{level}
时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return send_feishu_notification(full_title, full_content, mention_all=(level == "error"))


if __name__ == "__main__":
    # 测试
    print("🧪 测试飞书通知...")
    
    # 测试督促通知
    result = send_reminder_notification(
        agent_id="dev-claw",
        agent_name="dev-claw",
        task_name="龙虾办公室开发",
        progress=0.45,
        elapsed_time=7200,
        reminder_type="manual"
    )
    
    print(f"测试结果：{result}")
