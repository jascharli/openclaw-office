#!/usr/bin/env python3
"""
龙虾办公室 - 冒烟测试脚本

覆盖8个冒烟测试用例，用于快速验证系统核心功能
"""

import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000"
TIMEOUT = 10


class TestSmokeSuite:
    """冒烟测试套件 - 8个核心测试用例"""
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_001_system_health_check(self):
        """ST-001: 系统健康检查"""
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_002_get_agents_status_list(self):
        """ST-002: 获取Agent状态列表"""
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
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_003_get_agent_tasks_list(self):
        """ST-003: 获取Agent任务清单"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_004_get_requests_stats(self):
        """ST-004: 获取请求统计数据"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_005_get_token_stats(self):
        """ST-005: 获取Token统计数据"""
        url = f"{BASE_URL}/api/v1/tokens/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_006_api_response_time_validation(self):
        """ST-006: API响应时间验证"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        start_time = time.time()
        response = requests.get(url, timeout=TIMEOUT)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 1000
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_007_concurrent_requests_handling(self):
        """ST-007: 并发请求处理"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        def make_request():
            response = requests.get(url, timeout=TIMEOUT)
            return response.status_code == 200
        
        success_count = 0
        total_count = 10
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(total_count)]
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
        
        assert success_count == total_count
    
    @pytest.mark.smoke
    @pytest.mark.p0
    def test_ST_008_frontend_page_load(self):
        """ST-008: 前端页面加载"""
        try:
            import os
            frontend_path = "/Users/alisa/.openclaw/workspace/projects/lobster-office/frontend/index.html"
            assert os.path.exists(frontend_path)
            
            with open(frontend_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "龙虾办公室" in content
                assert "<!DOCTYPE html>" in content
                
        except ImportError:
            pytest.skip("Frontend page test skipped")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
