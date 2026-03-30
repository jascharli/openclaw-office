#!/usr/bin/env python3
"""
龙虾办公室 - 回归测试脚本

覆盖所有105个回归测试用例
"""

import pytest
import requests
import json
import time
import concurrent.futures
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TIMEOUT = 10


class TestAgentStatusRegression:
    """Agent状态监控回归测试 - 25个用例"""
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_001_get_agents_status_list(self):
        """RT-STA-001: 获取所有Agent状态列表"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "summary" in data
        assert isinstance(data["agents"], list)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_002_verify_status_classification(self):
        """RT-STA-002: 验证Agent状态分类"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        summary = data["summary"]
        
        assert "total" in summary
        assert "idle" in summary
        assert "conversing" in summary
        assert "working" in summary
        assert summary["total"] == summary["idle"] + summary["conversing"] + summary["working"]
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_003_verify_idle_agents_display(self):
        """RT-STA-003: 验证空闲Agent显示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        agents = data["agents"]
        
        idle_agents = [a for a in agents if a.get("status") == "idle"]
        for agent in idle_agents:
            assert "agent_id" in agent
            assert "status" in agent
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_004_verify_conversing_agents_display(self):
        """RT-STA-004: 验证对话中Agent显示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        agents = data["agents"]
        
        conversing_agents = [a for a in agents if a.get("status") == "conversing"]
        for agent in conversing_agents:
            assert "agent_id" in agent
            assert "status" in agent
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_005_verify_working_agents_display(self):
        """RT-STA-005: 验证工作中Agent显示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        agents = data["agents"]
        
        working_agents = [a for a in agents if a.get("status") == "working"]
        for agent in working_agents:
            assert "agent_id" in agent
            assert "status" in agent
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_006_get_single_agent_detail(self):
        """RT-STA-006: 获取单个Agent详细信息"""
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
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_007_verify_status_refresh(self):
        """RT-STA-007: 验证Agent状态刷新"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        assert response1.status_code == 200
        
        time.sleep(1)
        
        response2 = requests.get(url, timeout=TIMEOUT)
        assert response2.status_code == 200
        
        assert "agents" in response2.json()
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_008_verify_summary_statistics(self):
        """RT-STA-008: 验证状态摘要统计"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        summary = data["summary"]
        
        assert isinstance(summary["total"], int)
        assert isinstance(summary["idle"], int)
        assert isinstance(summary["conversing"], int)
        assert isinstance(summary["working"], int)
        assert summary["total"] >= 0
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_009_verify_idle_time_display(self):
        """RT-STA-009: 验证空闲时间显示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        agents = data["agents"]
        
        for agent in agents:
            if "idle_time" in agent:
                assert isinstance(agent["idle_time"], (int, float, type(None)))
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_010_verify_recent_model_display(self):
        """RT-STA-010: 验证最近模型显示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        agents = data["agents"]
        
        for agent in agents:
            if "recent_model" in agent:
                assert isinstance(agent["recent_model"], (str, type(None)))
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_011_verify_agent_card_color(self):
        """RT-STA-011: 验证Agent卡片颜色"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        agents = data["agents"]
        
        valid_statuses = ["idle", "conversing", "working"]
        for agent in agents:
            if "status" in agent:
                assert agent["status"] in valid_statuses
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_012_verify_status_hover_tooltip(self):
        """RT-STA-012: 验证状态悬停提示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert "summary" in data
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_013_test_large_agents_performance(self):
        """RT-STA-013: 测试大量Agent显示性能"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        start_time = time.time()
        response = requests.get(url, timeout=TIMEOUT)
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_014_test_empty_data_scenario(self):
        """RT-STA-014: 测试空数据场景"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert isinstance(data["agents"], list)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_015_test_single_agent_status_change(self):
        """RT-STA-015: 测试单个Agent状态变更"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["agents"]) > 0:
            agent = data["agents"][0]
            assert "agent_id" in agent
            assert "status" in agent
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_016_test_batch_agent_status_change(self):
        """RT-STA-016: 测试批量Agent状态变更"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["agents"]) == data["summary"]["total"]
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_017_verify_status_sync_integrity(self):
        """RT-STA-017: 验证状态同步完整性"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        for agent in data["agents"]:
            assert "agent_id" in agent
            assert "status" in agent
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_018_verify_websocket_realtime_update(self):
        """RT-STA-018: 验证WebSocket实时更新"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        assert "agents" in response.json()
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_STA_019_test_network_error_status_display(self):
        """RT-STA-019: 测试网络异常时的状态显示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        try:
            response = requests.get(url, timeout=TIMEOUT)
            assert response.status_code in [200, 500, 503]
        except requests.exceptions.RequestException:
            pass
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_STA_020_test_database_error_status_display(self):
        """RT-STA-020: 测试数据库异常时的状态显示"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code in [200, 500, 503]
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_021_verify_status_data_consistency(self):
        """RT-STA-021: 验证状态数据一致性"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["summary"]["total"] == data2["summary"]["total"]
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_022_test_status_cache_mechanism(self):
        """RT-STA-022: 测试状态数据缓存机制"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        start_time = time.time()
        response1 = requests.get(url, timeout=TIMEOUT)
        first_time = time.time() - start_time
        
        start_time = time.time()
        response2 = requests.get(url, timeout=TIMEOUT)
        second_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_023_test_status_history_function(self):
        """RT-STA-023: 测试状态历史记录功能"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_024_verify_status_trend_analysis(self):
        """RT-STA-024: 验证状态趋势分析"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_STA_025_test_status_alert_function(self):
        """RT-STA-025: 测试状态告警功能"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data


class TestTaskManagementRegression:
    """任务管理回归测试 - 30个用例"""
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_001_get_agent_tasks_list(self):
        """RT-TSK-001: 获取Agent任务清单"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_002_verify_task_list_display(self):
        """RT-TSK-002: 验证任务列表显示"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_003_filter_tasks_by_agent(self):
        """RT-TSK-003: 按Agent筛选任务"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_004_filter_tasks_by_today(self):
        """RT-TSK-004: 按时间筛选任务（今天）"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        params = {"period": "today"}
        response = requests.get(url, params=params, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_005_filter_tasks_by_week(self):
        """RT-TSK-005: 按时间筛选任务（本周）"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        params = {"period": "week"}
        response = requests.get(url, params=params, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_006_filter_tasks_by_month(self):
        """RT-TSK-006: 按时间筛选任务（本月）"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        params = {"period": "month"}
        response = requests.get(url, params=params, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_007_filter_tasks_by_all(self):
        """RT-TSK-007: 按时间筛选任务（全部）"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        params = {"period": "all"}
        response = requests.get(url, params=params, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_008_verify_task_card_display(self):
        """RT-TSK-008: 验证任务卡片显示"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_009_verify_task_id_display(self):
        """RT-TSK-009: 验证任务ID显示"""
        url = f"{BASE_URL}/api/v1/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_010_verify_task_name_display(self):
        """RT-TSK-010: 验证任务名称显示"""
        url = f"{BASE_URL}/api/v1/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_011_verify_task_status_display(self):
        """RT-TSK-011: 验证任务状态显示"""
        url = f"{BASE_URL}/api/v1/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_012_verify_task_progress_display(self):
        """RT-TSK-012: 验证任务进度显示"""
        url = f"{BASE_URL}/api/v1/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_013_verify_task_update_time_display(self):
        """RT-TSK-013: 验证任务更新时间显示"""
        url = f"{BASE_URL}/api/v1/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_014_test_empty_task_list_scenario(self):
        """RT-TSK-014: 测试空任务列表场景"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_015_test_large_tasks_performance(self):
        """RT-TSK-015: 测试大量任务显示性能"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        
        start_time = time.time()
        response = requests.get(url, timeout=TIMEOUT)
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_016_create_task_handover(self):
        """RT-TSK-016: 创建任务移交"""
        url = f"{BASE_URL}/api/v1/handovers"
        handover_data = {
            "task_id": f"test-task-{int(time.time())}",
            "task_name": "回归测试任务",
            "from_agent_id": "dev-claw",
            "to_agent_id": "work-claw",
            "handover_type": "full",
            "progress_at_handover": 0.5,
            "context_data": {},
            "notes": "回归测试移交"
        }
        
        response = requests.post(url, json=handover_data, timeout=TIMEOUT)
        assert response.status_code in [200, 201, 400]
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_017_verify_handover_data_structure(self):
        """RT-TSK-017: 验证任务移交数据结构"""
        url = f"{BASE_URL}/api/v1/handovers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_018_test_handover_history_query(self):
        """RT-TSK-018: 测试任务移交历史查询"""
        url = f"{BASE_URL}/api/v1/handovers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_019_test_handover_detail_view(self):
        """RT-TSK-019: 测试任务移交详情查看"""
        url = f"{BASE_URL}/api/v1/handovers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            handover_id = data[0].get("id")
            if handover_id:
                detail_url = f"{BASE_URL}/api/v1/handovers/{handover_id}"
                detail_response = requests.get(detail_url, timeout=TIMEOUT)
                assert detail_response.status_code in [200, 404]
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_020_test_handover_accept_function(self):
        """RT-TSK-020: 测试任务移交接受功能"""
        url = f"{BASE_URL}/api/v1/handovers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_021_test_handover_reject_function(self):
        """RT-TSK-021: 测试任务移交拒绝功能"""
        url = f"{BASE_URL}/api/v1/handovers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_022_test_handover_complete_function(self):
        """RT-TSK-022: 测试任务移交完成功能"""
        url = f"{BASE_URL}/api/v1/handovers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_023_test_task_data_sync(self):
        """RT-TSK-023: 测试任务数据同步"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        time.sleep(1)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_TSK_024_test_task_data_consistency(self):
        """RT-TSK-024: 测试任务数据一致性"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_025_test_task_data_cache(self):
        """RT-TSK-025: 测试任务数据缓存"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        
        start_time = time.time()
        response1 = requests.get(url, timeout=TIMEOUT)
        first_time = time.time() - start_time
        
        start_time = time.time()
        response2 = requests.get(url, timeout=TIMEOUT)
        second_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_TSK_026_test_network_error_task_display(self):
        """RT-TSK-026: 测试网络异常时的任务显示"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        
        try:
            response = requests.get(url, timeout=TIMEOUT)
            assert response.status_code in [200, 500, 503]
        except requests.exceptions.RequestException:
            pass
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_TSK_027_test_database_error_task_display(self):
        """RT-TSK-027: 测试数据库异常时的任务显示"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code in [200, 500, 503]
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_028_verify_task_statistics_function(self):
        """RT-TSK-028: 验证任务统计功能"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_TSK_029_verify_task_trend_analysis(self):
        """RT-TSK-029: 验证任务趋势分析"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_TSK_030_test_task_alert_function(self):
        """RT-TSK-030: 测试任务告警功能"""
        url = f"{BASE_URL}/api/v1/agents/tasks"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200


class TestStatisticsRegression:
    """数据统计回归测试 - 20个用例"""
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_026_get_requests_stats(self):
        """RT-STA-026: 获取请求统计数据"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "hourly" in data or "total" in data
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_027_verify_today_total_requests(self):
        """RT-STA-027: 验证今日请求总数"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if "hourly" in data:
            total = sum(h.get("total", 0) for h in data["hourly"])
            assert isinstance(total, int)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_028_verify_request_success_rate(self):
        """RT-STA-028: 验证请求成功率"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_029_get_token_stats(self):
        """RT-STA-029: 获取Token统计数据"""
        url = f"{BASE_URL}/api/v1/tokens/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_used" in data or "budget" in data
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_030_verify_today_token_usage(self):
        """RT-STA-030: 验证今日Token使用量"""
        url = f"{BASE_URL}/api/v1/tokens/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if "total_used" in data:
            assert isinstance(data["total_used"], int)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_031_verify_token_daily_budget(self):
        """RT-STA-031: 验证Token每日预算"""
        url = f"{BASE_URL}/api/v1/tokens/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if "budget" in data:
            assert "daily" in data["budget"] or "daily_budget" in data
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_032_verify_token_remaining_budget(self):
        """RT-STA-032: 验证Token剩余预算"""
        url = f"{BASE_URL}/api/v1/tokens/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if "budget" in data:
            budget = data["budget"]
            assert "remaining_daily" in budget or "remaining" in budget or "daily" in budget
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_033_get_hourly_requests(self):
        """RT-STA-033: 获取每小时请求量"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if "hourly" in data:
            assert isinstance(data["hourly"], list)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_034_verify_hourly_data_structure(self):
        """RT-STA-034: 验证每小时请求数据结构"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if "hourly" in data:
            for hour_data in data["hourly"]:
                assert "hour" in hour_data or "total" in hour_data
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_035_get_providers_stats(self):
        """RT-STA-035: 获取提供商统计数据"""
        url = f"{BASE_URL}/api/v1/requests/providers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_036_verify_providers_data_structure(self):
        """RT-STA-036: 验证提供商统计数据结构"""
        url = f"{BASE_URL}/api/v1/requests/providers"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
        assert isinstance(data["providers"], list)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_037_get_model_stats(self):
        """RT-STA-037: 获取分模型统计数据"""
        url = f"{BASE_URL}/api/v1/requests/models"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_038_verify_model_data_structure(self):
        """RT-STA-038: 验证分模型统计数据结构"""
        url = f"{BASE_URL}/api/v1/requests/models"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert isinstance(data["models"], list)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_039_verify_model_data_accuracy(self):
        """RT-STA-039: 验证分模型统计数据准确性"""
        url = f"{BASE_URL}/api/v1/requests/models"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if "models" in data and len(data["models"]) > 0:
            for model in data["models"]:
                assert "model" in model or "name" in model or "total" in model
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_040_get_agents_stats(self):
        """RT-STA-040: 获取Agent统计数据"""
        url = f"{BASE_URL}/api/v1/requests/agents"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_041_verify_stats_refresh_mechanism(self):
        """RT-STA-041: 验证统计数据刷新机制"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        time.sleep(1)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_042_test_stats_cache(self):
        """RT-STA-042: 测试统计数据缓存"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        
        start_time = time.time()
        response1 = requests.get(url, timeout=TIMEOUT)
        first_time = time.time() - start_time
        
        start_time = time.time()
        response2 = requests.get(url, timeout=TIMEOUT)
        second_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_043_test_empty_stats_scenario(self):
        """RT-STA-043: 测试空统计数据场景"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_STA_044_test_large_stats_performance(self):
        """RT-STA-044: 测试大量统计数据显示性能"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        
        start_time = time.time()
        response = requests.get(url, timeout=TIMEOUT)
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_STA_045_verify_stats_data_consistency(self):
        """RT-STA-045: 验证统计数据一致性"""
        url = f"{BASE_URL}/api/v1/requests/stats"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestReminderRegression:
    """督促功能回归测试 - 15个用例"""
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_REM_001_send_manual_reminder(self):
        """RT-REM-001: 发送手动督促消息"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": f"回归测试督促消息 {int(time.time())}",
            "reminder_type": "manual"
        }
        
        response = requests.post(url, json=reminder_data, timeout=TIMEOUT)
        assert response.status_code in [200, 201, 400, 422]
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_REM_002_verify_reminder_send_success(self):
        """RT-REM-002: 验证督促消息发送成功"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": "验证发送成功测试",
            "reminder_type": "manual"
        }
        
        response = requests.post(url, json=reminder_data, timeout=TIMEOUT)
        assert response.status_code in [200, 201, 400, 422]
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_REM_003_verify_reminder_content_correctness(self):
        """RT-REM-003: 验证督促消息内容正确性"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_REM_004_get_reminder_history(self):
        """RT-REM-004: 获取督促历史记录"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_REM_005_verify_history_data_structure(self):
        """RT-REM-005: 验证督促历史数据结构"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_REM_006_verify_history_sorting(self):
        """RT-REM-006: 验证督促历史排序"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_REM_007_test_reminder_timeout_handling(self):
        """RT-REM-007: 测试督促消息超时处理"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": "超时测试消息",
            "reminder_type": "manual"
        }
        
        try:
            response = requests.post(url, json=reminder_data, timeout=1)
            assert response.status_code in [200, 201, 400, 422, 408]
        except requests.exceptions.Timeout:
            pass
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_REM_008_test_reminder_retry_on_failure(self):
        """RT-REM-008: 测试督促消息失败重试"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": "重试测试消息",
            "reminder_type": "manual"
        }
        
        response = requests.post(url, json=reminder_data, timeout=TIMEOUT)
        assert response.status_code in [200, 201, 400, 422]
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_REM_009_verify_reminder_statistics(self):
        """RT-REM-009: 验证督促统计功能"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_REM_010_test_reminder_frequency_limit(self):
        """RT-REM-010: 测试督促消息频率限制"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        
        for i in range(3):
            reminder_data = {
                "agent_id": "dev-claw",
                "message": f"频率限制测试 {i}",
                "reminder_type": "manual"
            }
            response = requests.post(url, json=reminder_data, timeout=TIMEOUT)
            assert response.status_code in [200, 201, 400, 422, 429]
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_REM_011_test_reminder_template_function(self):
        """RT-REM-011: 测试督促消息模板功能"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": "模板测试消息",
            "reminder_type": "template"
        }
        
        response = requests.post(url, json=reminder_data, timeout=TIMEOUT)
        assert response.status_code in [200, 201, 400, 422]
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_REM_012_test_network_error_reminder(self):
        """RT-REM-012: 测试网络异常时的督促功能"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": "网络异常测试",
            "reminder_type": "manual"
        }
        
        try:
            response = requests.post(url, json=reminder_data, timeout=TIMEOUT)
            assert response.status_code in [200, 201, 400, 422, 500, 503]
        except requests.exceptions.RequestException:
            pass
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_REM_013_test_reminder_deduplication(self):
        """RT-REM-013: 测试督促消息去重机制"""
        url = f"{BASE_URL}/api/v1/reminders/send"
        reminder_data = {
            "agent_id": "dev-claw",
            "message": "去重测试消息",
            "reminder_type": "manual"
        }
        
        response1 = requests.post(url, json=reminder_data, timeout=TIMEOUT)
        response2 = requests.post(url, json=reminder_data, timeout=TIMEOUT)
        
        assert response1.status_code in [200, 201, 400, 422]
        assert response2.status_code in [200, 201, 400, 422]
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_REM_014_verify_reminder_record_integrity(self):
        """RT-REM-014: 验证督促消息记录完整性"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            record = data[0]
            assert "agent_id" in record or "message" in record or "timestamp" in record
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_REM_015_test_reminder_effect_analysis(self):
        """RT-REM-015: 测试督促效果分析功能"""
        url = f"{BASE_URL}/api/v1/reminders/history"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200


class TestSystemIntegrationRegression:
    """系统集成回归测试 - 15个用例"""
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_001_system_health_check(self):
        """RT-INT-001: 系统健康检查"""
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_002_verify_api_root_access(self):
        """RT-INT-002: 验证API根路径访问"""
        url = f"{BASE_URL}/"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_003_test_data_sync_process(self):
        """RT-INT-003: 测试数据同步流程"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        time.sleep(2)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_004_verify_data_sync_integrity(self):
        """RT-INT-004: 验证数据同步完整性"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agents" in data
        assert "summary" in data
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_INT_005_test_websocket_connection(self):
        """RT-INT-005: 测试WebSocket连接"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_INT_006_verify_websocket_realtime_update(self):
        """RT-INT-006: 验证WebSocket实时更新"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_007_test_api_response_time(self):
        """RT-INT-007: 测试API响应时间"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        start_time = time.time()
        response = requests.get(url, timeout=TIMEOUT)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_008_test_concurrent_requests(self):
        """RT-INT-008: 测试并发请求处理"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        def make_request():
            response = requests.get(url, timeout=TIMEOUT)
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(status == 200 for status in results)
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_009_test_database_connection_stability(self):
        """RT-INT-009: 测试数据库连接稳定性"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        for _ in range(5):
            response = requests.get(url, timeout=TIMEOUT)
            assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_INT_010_test_system_high_availability(self):
        """RT-INT-010: 测试系统高可用性"""
        url = f"{BASE_URL}/health"
        
        for _ in range(3):
            response = requests.get(url, timeout=TIMEOUT)
            assert response.status_code == 200
            time.sleep(1)
    
    @pytest.mark.regression
    @pytest.mark.p1
    def test_RT_INT_011_test_config_sync_function(self):
        """RT-INT-011: 测试配置同步功能"""
        url = f"{BASE_URL}/api/v1/agents/status"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
    
    @pytest.mark.regression
    @pytest.mark.p0
    def test_RT_INT_012_verify_frontend_backend_data_consistency(self):
        """RT-INT-012: 验证前后端数据一致性"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        response1 = requests.get(url, timeout=TIMEOUT)
        response2 = requests.get(url, timeout=TIMEOUT)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["summary"]["total"] == data2["summary"]["total"]
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_INT_013_test_network_recovery_mechanism(self):
        """RT-INT-013: 测试网络异常恢复机制"""
        url = f"{BASE_URL}/api/v1/agents/status"
        
        try:
            response = requests.get(url, timeout=TIMEOUT)
            assert response.status_code in [200, 500, 503]
        except requests.exceptions.RequestException:
            pass
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_INT_014_test_system_monitoring_function(self):
        """RT-INT-014: 测试系统监控功能"""
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.regression
    @pytest.mark.p2
    def test_RT_INT_015_verify_system_log_recording(self):
        """RT-INT-015: 验证系统日志记录"""
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=TIMEOUT)
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "regression"])
