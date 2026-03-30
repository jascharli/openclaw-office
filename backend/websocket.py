"""
龙虾办公室 - WebSocket 实时推送模块
实现 Agent 状态变化的实时推送
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import asyncio
import json
from datetime import datetime


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 活跃连接：{client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 订阅的 Agent：{client_id: set(agent_ids)}
        self.subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """接受 WebSocket 连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()  # 默认订阅所有
        print(f"🔌 客户端 {client_id} 已连接")
    
    def disconnect(self, client_id: str):
        """断开 WebSocket 连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.subscriptions[client_id]
            print(f"🔌 客户端 {client_id} 已断开")
    
    def subscribe(self, client_id: str, agent_ids: List[str]):
        """订阅特定 Agent 的状态更新"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id] = set(agent_ids)
            print(f"📡 客户端 {client_id} 订阅：{agent_ids}")
    
    async def broadcast(self, message: dict, agent_id: str = None):
        """
        广播消息
        agent_id: 如果指定，只发送给订阅了该 Agent 的客户端
        """
        disconnected = []
        
        for client_id, websocket in self.active_connections.items():
            # 检查订阅过滤
            if agent_id:
                subscribed = self.subscriptions.get(client_id, set())
                if subscribed and agent_id not in subscribed:
                    continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"❌ 发送消息给 {client_id} 失败：{e}")
                disconnected.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def send_personal(self, message: dict, client_id: str):
        """发送个人消息"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                print(f"❌ 发送个人消息给 {client_id} 失败：{e}")
                self.disconnect(client_id)


# 全局管理器实例
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str = "default"):
    """WebSocket 端点"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收客户端消息（添加超时：300 秒无活动自动断开）
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=300.0
                )
            except asyncio.TimeoutError:
                print(f"⏰ 客户端 {client_id} 超时，断开连接")
                break
            
            message = json.loads(data)
            
            # 处理订阅请求
            if message.get("type") == "subscribe":
                agent_ids = message.get("agents", [])
                manager.subscribe(client_id, agent_ids)
                await manager.send_personal({
                    "type": "subscribed",
                    "agents": agent_ids,
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
            
            # 处理心跳
            elif message.get("type") == "ping":
                await manager.send_personal({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"❌ WebSocket 错误：{e}")
        manager.disconnect(client_id)


async def broadcast_agent_update(agent_data: dict):
    """广播 Agent 状态更新"""
    await manager.broadcast({
        "type": "agent_update",
        "data": agent_data,
        "timestamp": datetime.utcnow().isoformat()
    }, agent_data.get("agent_id"))


async def broadcast_task_update(task_data: dict):
    """广播任务更新"""
    await manager.broadcast({
        "type": "task_update",
        "data": task_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_reminder(reminder_data: dict):
    """广播督促消息"""
    await manager.broadcast({
        "type": "reminder",
        "data": reminder_data,
        "timestamp": datetime.utcnow().isoformat()
    }, reminder_data.get("agent_id"))
