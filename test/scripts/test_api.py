#!/usr/bin/env python3
"""
龙虾办公室 - API测试脚本

测试所有RESTful API接口的功能和性能
"""

import pytest
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 10


class TestAgentAPI:
    """Agent状态API测试"""
    
    def test_get_agents_status(self):
        """测试获取所有Agent状态"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert "summary" in data
        assert isinstance(data["agents"], list)
        
        summary = data["summary"]
        assert "total" in summary
        assert "idle" in summary
        assert "conversing" in summary
        assert "working" in summary
    
    def test_get_agent_by_id(self):
        """测试获取单个Agent状态"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        agents = response.json()["agents"]
        
        if len(agents) > 0:
            agent_id = agents[0]["agent_id"]
            url = f"{BASE_URL}/api/v1/agents/{agent_id}"
            response = requests.get(url, timeout=TIMEOUT)
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_id"] == agent_id


class TestTaskAPI:
    """任务管理API测试"""
    
    def test_get_agent_tasks(self):
        """测试获取Agent任务清单"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
    
    def test_create_handover(self):
        """测试创建任务移交"""
        url = f"{BASE_URL}/api/v1/handovers"
        handover_data = {
            "task_id": "test-task-001",
            "task_name": "测试任务",
            "from_agent_id": "dev-claw",
            "to_agent_id": "work-claw",
            "handover_type": "full",
            "progress_at_handover": 0.5,
            "context_data": {},
            "notes": "测试移交"
        }
        
        response = requests.post(
            url, 
            json=handover_data, 
            timeout=TIMEOUT
        )
        
        assert response.status_code in [200, 201, 400]


class TestStatsAPI:
    """数据统计API测试"""
    
    def test_get_requests_stats(self):
        """测试获取请求统计"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "hourly" in data or "total" in data
    
    def test_get_token_stats(self):
        """测试获取Token统计"""
        url = f"{BASE_URL}/api/v1/tokens/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_used" in data or "budget" in data
    
    def test_get_providers_stats(self):
        """测试获取提供商统计"""
        url = f"{BASE_URL}/api/v1/requests/providers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
    
    def test_get_model_stats(self):
        """测试获取分模型统计"""
        url = f"{BASE_URL}/api/v1/requests/models"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
    
    def test_get_agents_stats(self):
        """测试获取Agent统计"""
        url = f"{BASE_URL}/api/v1/requests/agents"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data


class TestReminderAPI:
    """督促功能API测试"""
    
    def test_send_reminder(self):
        """测试发送督促消息"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": "测试督促消息",
            "reminder_type": "manual"
        }
        
        response = requests.post(
            url, 
            json=reminder_data, 
            timeout=TIMEOUT
        )
        
        assert response.status_code in [200, 201, 400, 422]
    
    def test_get_reminder_history(self):
        """测试获取督促历史"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200


class TestHealthCheck:
    """健康检查测试"""
    
    def test_api_health(self):
        """测试API健康检查"""
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    def test_api_root(self):
        """测试API根路径"""
        url = f"{BASE_URL}/"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
