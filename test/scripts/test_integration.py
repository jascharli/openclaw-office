#!/usr/bin/env python3
"""
龙虾办公室 - 集成测试脚本

测试系统各模块的集成和端到端功能
"""

import pytest
import requests
import json
import time
import concurrent.futures

BASE_URL = "http://localhost:8000"
TIMEOUT = 10


class TestDataSync:
    """数据同步集成测试"""
    
    def test_agent_status_sync(self):
        """测试Agent状态同步"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        assert response.status_code == 200
        
        initial_data = response.json()
        initial_count = initial_data["summary"]["total"]
        
        time.sleep(2)
        
        response = requests.get(url, timeout=TIMEOUT)
        assert response.status_code == 200
        
        updated_data = response.json()
        updated_count = updated_data["summary"]["total"]
        
        assert isinstance(updated_count, int)
    
    def test_task_sync(self):
        """测试任务同步"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        assert response.status_code == 200
        
        initial_tasks = response.json()
        
        time.sleep(2)
        
        response = requests.get(url, timeout=TIMEOUT)
        assert response.status_code == 200
        
        updated_tasks = response.json()
        
        assert isinstance(updated_tasks, dict)


class TestEndToEnd:
    """端到端测试"""
    
    def test_user_scenario_view_agents(self):
        """测试用户场景：查看Agent状态"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert "summary" in data
    
    def test_user_scenario_view_tasks(self):
        """测试用户场景：查看任务清单"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
    
    def test_user_scenario_view_stats(self):
        """测试用户场景：查看统计数据"""
        urls = [
            f"{BASE_URL}/api/v1/requests/stats",
            f"{BASE_URL}/api/v1/tokens/stats",
            f"{BASE_URL}/api/v1/requests/providers"
        ]
        
        for url in urls:
            response = requests.get(url, timeout=TIMEOUT)
            assert response.status_code == 200
    
    def test_user_scenario_view_handovers(self):
        """测试用户场景：查看任务移交"""
        url = f"{BASE_URL}/api/v1/handovers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200


class TestPerformance:
    """性能集成测试"""
    
    def test_api_response_time(self):
        """测试API响应时间"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        start_time = time.time()
        response = requests.get(url, timeout=TIMEOUT)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response_time < 1.0
        assert response.status_code == 200
    
    def test_concurrent_requests(self):
        """测试并发请求"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        def make_request():
            response = requests.get(url, timeout=TIMEOUT)
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(status == 200 for status in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
