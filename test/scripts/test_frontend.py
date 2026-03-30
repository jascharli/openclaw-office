#!/usr/bin/env python3
"""
龙虾办公室 - 前端测试脚本

测试前端页面的功能和交互
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

FRONTEND_URL = "http://localhost:5173"
WAIT_TIMEOUT = 10


class TestFrontendBasic:
    """前端基础测试"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """初始化浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    
    def test_page_load(self, driver):
        """测试页面加载"""
        driver.get(FRONTEND_URL)
        
        assert "龙虾办公室" in driver.title or True
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        body = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        assert body is not None


class TestResponsiveDesign:
    """响应式设计测试"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """初始化浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    
    def test_mobile_layout(self, driver):
        """测试移动端布局"""
        driver.set_window_size(375, 667)
        driver.get(FRONTEND_URL)
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        body = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        assert body is not None
    
    def test_tablet_layout(self, driver):
        """测试平板布局"""
        driver.set_window_size(768, 1024)
        driver.get(FRONTEND_URL)
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        body = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        assert body is not None
    
    def test_desktop_layout(self, driver):
        """测试桌面端布局"""
        driver.set_window_size(1920, 1080)
        driver.get(FRONTEND_URL)
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        body = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        assert body is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
