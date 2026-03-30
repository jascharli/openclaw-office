"""
龙虾办公室 - 配置管理模块
从配置文件加载配置，支持环境变量覆盖
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
CONFIG_EXAMPLE = BASE_DIR / "config.example.json"

# 默认配置
DEFAULT_CONFIG = {
    "app": {
        "name": "龙虾办公室",
        "version": "1.0.0",
        "description": "AI 团队工作空间"
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "frontend_port": 5173
    },
    "database": {
        "path": "./lobster_office.db",
        "timezone": "Asia/Shanghai"
    },
    "agents": {
        "scan_mode": "auto",  # auto | manual
        "scan_base_dir": "~/.openclaw/agents",
        "custom_agents": []
    },
    "token_budget": {
        "daily": 500000,
        "monthly": 10000000
    },
    "features": {
        "handover_enabled": True,
        "reminder_enabled": True,
        "feishu_enabled": False
    },
    "feishu": {
        "webhook_url": "",
        "app_id": "",
        "app_secret": ""
    }
}


class Config:
    """配置管理器"""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self._merge_config(file_config)
                print(f"✅ 已加载配置文件：{CONFIG_FILE}")
            except Exception as e:
                print(f"⚠️ 加载配置文件失败：{e}，使用默认配置")
        else:
            print(f"⚠️ 配置文件不存在：{CONFIG_FILE}，使用默认配置")
            print(f"💡 提示：复制 config.example.json 到 config.json 并修改")
    
    def _merge_config(self, file_config: Dict):
        """合并配置"""
        for key, value in file_config.items():
            if isinstance(value, dict) and key in self.config:
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_agent_list(self) -> List[Dict]:
        """
        获取 Agent 列表（自动扫描，无需配置）
        
        扫描策略：
        1. 优先扫描 ~/.openclaw/agents（OpenClaw 默认路径）
        2. 如果没有找到，扫描当前工作目录的 agents 子目录
        3. 如果还是没有，扫描所有可能的 OpenClaw 安装路径
        """
        scan_mode = self.get('agents.scan_mode', 'auto')
        custom_agents = self.get('agents.custom_agents', [])
        
        agents = []
        
        # 自动扫描
        if scan_mode == 'auto':
            # 候选路径列表（按优先级排序）
            candidate_paths = [
                '~/.openclaw/agents',  # OpenClaw 默认路径
                './agents',  # 当前工作目录
                os.path.expanduser('~/.openclaw/agents'),  # 展开的绝对路径
            ]
            
            # 尝试每个候选路径
            for scan_base_dir in candidate_paths:
                scan_base_dir = os.path.expanduser(scan_base_dir)
                if not os.path.exists(scan_base_dir):
                    continue
                
                print(f"🔍 扫描 Agent 目录：{scan_base_dir}")
                
                for agent_dir in os.listdir(scan_base_dir):
                    agent_path = os.path.join(scan_base_dir, agent_dir)
                    if not os.path.isdir(agent_path):
                        continue
                    
                    sessions_dir = os.path.join(agent_path, 'sessions')
                    if os.path.exists(sessions_dir):
                        # 避免重复
                        if not any(a['id'] == agent_dir for a in agents):
                            agents.append({
                                'id': agent_dir,
                                'name': agent_dir,
                                'workspace': agent_path
                            })
                
                # 如果找到了 Agent，停止扫描
                if agents:
                    print(f"✅ 找到 {len(agents)} 个 Agent")
                    break
            
            if not agents:
                print("⚠️ 未找到任何 Agent（没有 sessions 目录的文件夹）")
        
        # 添加自定义 Agent
        for custom_agent in custom_agents:
            if not any(a['id'] == custom_agent['id'] for a in agents):
                agents.append(custom_agent)
        
        return agents
    
    def get_token_budget(self) -> Dict:
        """获取 Token 预算"""
        return {
            'daily': self.get('token_budget.daily', 500000),
            'monthly': self.get('token_budget.monthly', 10000000)
        }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        return self.get(f'features.{feature}', False)


# 全局配置实例
config = Config()


def get_config() -> Config:
    """获取配置实例"""
    return config


if __name__ == '__main__':
    # 测试配置
    cfg = get_config()
    print(f"应用名称：{cfg.get('app.name')}")
    print(f"服务器端口：{cfg.get('server.port')}")
    print(f"Agent 列表：{cfg.get_agent_list()}")
    print(f"Token 预算：{cfg.get_token_budget()}")
