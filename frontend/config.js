// OpenClaw 办公室配置文件
// 刷新频率设置（单位：秒）
// 动态获取当前页面的协议和主机名
const protocol = window.location.protocol;
const hostname = window.location.hostname;
const backendPort = 8000;

window.OPENCLAW_CONFIG = {
  // API 基础配置
  API_BASE: protocol + '//' + hostname + ':' + backendPort,
  BACKEND_PORT: backendPort,
  
  // WebSocket 配置
  WS_URL: (protocol === 'https:' ? 'wss:' : 'ws:') + '//' + hostname + ':' + backendPort + '/ws',
  
  // 刷新频率设置（单位：秒）
  refresh: {
    // 页面自动刷新频率（30-600秒）
    auto_refresh: 300,
    
    // 状态数据刷新频率（30-600秒）
    status_data: 300,
    
    // 统计数据刷新频率（30-600秒）
    stats_data: 300
  },
  
  // Token 预算配置
  token_budget: {
    daily: 500000,
    monthly: 15000000
  },
  
  // 验证配置
  validate: function() {
    const errors = [];
    
    // 验证刷新频率
    if (this.refresh) {
      // 验证自动刷新频率
      if (this.refresh.auto_refresh) {
        if (typeof this.refresh.auto_refresh !== 'number' || 
            this.refresh.auto_refresh < 30 || 
            this.refresh.auto_refresh > 600) {
          errors.push('自动刷新频率必须在30-600秒之间');
        }
      }
      
      // 验证状态数据刷新频率
      if (this.refresh.status_data) {
        if (typeof this.refresh.status_data !== 'number' || 
            this.refresh.status_data < 30 || 
            this.refresh.status_data > 600) {
          errors.push('状态数据刷新频率必须在30-600秒之间');
        }
      }
      
      // 验证统计数据刷新频率
      if (this.refresh.stats_data) {
        if (typeof this.refresh.stats_data !== 'number' || 
            this.refresh.stats_data < 30 || 
            this.refresh.stats_data > 600) {
          errors.push('统计数据刷新频率必须在30-600秒之间');
        }
      }
    }
    
    // 验证 Token 预算
    if (this.token_budget) {
      if (this.token_budget.daily && 
          (typeof this.token_budget.daily !== 'number' || 
           this.token_budget.daily < 1)) {
        errors.push('日 Token 预算必须是正整数');
      }
      
      if (this.token_budget.monthly && 
          (typeof this.token_budget.monthly !== 'number' || 
           this.token_budget.monthly < 1)) {
        errors.push('月 Token 预算必须是正整数');
      }
    }
    
    return errors.length > 0 ? errors : null;
  },
  
  // 获取 API URL
  getApiUrl: function(path) {
    return this.API_BASE + '/api/v1' + path;
  }
};

// 确保配置对象存在
if (!window.OPENCLAW_CONFIG) {
  console.error('配置文件加载失败，使用默认配置');
  window.OPENCLAW_CONFIG = {
    API_BASE: protocol + '//' + hostname + ':' + backendPort,
    BACKEND_PORT: backendPort,
    WS_URL: (protocol === 'https:' ? 'wss:' : 'ws:') + '//' + hostname + ':' + backendPort + '/ws',
    refresh: {
      auto_refresh: 300,
      status_data: 300,
      stats_data: 300
    },
    token_budget: {
      daily: 500000,
      monthly: 15000000
    },
    validate: function() { return null; },
    getApiUrl: function(path) {
      return this.API_BASE + '/api/v1' + path;
    }
  };
}
