# OpenClaw 办公室 - 安装部署指南

**版本**: v2.3  
**最后更新**: 2026-03-30

---

## 📋 目录

- [环境要求](#环境要求)
- [方式一：Docker 部署（推荐）](#方式一docker-部署推荐)
- [方式二：脚本部署](#方式二脚本部署)
- [方式三：源码部署](#方式三源码部署)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [故障排查](#故障排查)

---

## 🌍 环境要求

### 最低配置

| 配置项 | 要求 |
|--------|------|
| 操作系统 | Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+) |
| CPU | 2 核 |
| 内存 | 4 GB |
| 硬盘 | 10 GB 可用空间 |

### 推荐配置

| 配置项 | 要求 |
|--------|------|
| 操作系统 | Windows 11, macOS 12+, Linux (Ubuntu 22.04+) |
| CPU | 4 核+ |
| 内存 | 8 GB+ |
| 硬盘 | 20 GB+ 可用空间 |

---

## 🐳 方式一：Docker 部署（推荐 ⭐⭐⭐⭐⭐）

### 前置要求

- 已安装 Docker
- 已安装 Docker Compose

#### 安装 Docker

**Windows/macOS**:
下载 Docker Desktop: https://www.docker.com/products/docker-desktop

**Linux (Ubuntu)**:
```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### 部署步骤

#### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/openclaw-office.git
cd openclaw-office
```

#### 2. 配置（可选）

```bash
# 复制配置文件
cp config.example.json config.json

# 编辑配置文件
# Windows: 用记事本打开 config.json
# macOS/Linux: nano config.json 或 vim config.json
```

配置说明见 [配置说明](#配置说明)

#### 3. 启动服务

```bash
# 后台启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

#### 4. 访问应用

打开浏览器访问：

- **前端页面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

#### 5. 停止服务

```bash
# 停止服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v
```

### Docker 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 更新镜像
docker-compose pull
docker-compose up -d

# 进入容器
docker exec -it openclaw-office bash
```

---

## 📜 方式二：脚本部署（推荐 ⭐⭐⭐⭐）

### 前置要求

- Python 3.11+
- pip

#### 安装 Python

**Windows**:
下载 Python: https://www.python.org/downloads/
安装时勾选 "Add Python to PATH"

**macOS**:
```bash
# 使用 Homebrew
brew install python@3.11

# 或从官网下载
# https://www.python.org/downloads/macos/
```

**Linux (Ubuntu)**:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

### 部署步骤

#### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/openclaw-office.git
cd openclaw-office
```

#### 2. 运行安装脚本

```bash
# 给脚本执行权限（Linux/macOS）
chmod +x install.sh

# 运行安装脚本
./install.sh
```

**Windows 用户**:
```batch
# 手动执行安装步骤
cd backend
pip install -r requirements.txt
cd ..

# 复制配置文件
copy config.example.json config.json

# 创建启动脚本
# 参考 start.sh 内容创建 start.bat
```

#### 3. 配置（可选）

```bash
# 编辑配置文件
# Windows: 记事本打开 config.json
# macOS/Linux: nano config.json
```

配置说明见 [配置说明](#配置说明)

#### 4. 启动服务

```bash
# Linux/macOS
./start.sh        # 前台运行（适合调试，关闭终端服务停止）
./start.sh -d     # 后台运行（推荐用于局域网访问）

# Windows
# 双击 start.bat 或在命令行运行 start.bat
```

**运行模式说明**:
- **前台运行**: 实时显示日志，按 `Ctrl+C` 停止，关闭终端服务会停止
- **后台运行**: 不占用终端，关闭终端服务继续运行，日志写入文件

#### 5. 访问应用

打开浏览器访问：

- **前端页面**: http://localhost:5173
- **局域网访问**: http://你的服务器IP:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

#### 6. 查看日志（后台运行模式）

```bash
# 实时查看日志
tail -f backend.log frontend.log

# 查看后端日志
tail -f backend.log

# 查看前端日志
tail -f frontend.log
```

#### 7. 停止服务

```bash
# Linux/macOS
./stop.sh

# Windows
# 双击 stop.bat 或在命令行运行 start.bat
```

---

## 💻 方式三：源码部署（推荐 ⭐⭐⭐）

### 前置要求

- Python 3.11+
- pip
- Git

### 部署步骤

#### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/openclaw-office.git
cd openclaw-office
```

#### 2. 创建虚拟环境（推荐）

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**:
```batch
python -m venv venv
venv\Scripts\activate
```

#### 3. 安装依赖

```bash
cd backend
pip install -r requirements.txt
cd ..
```

#### 4. 配置

```bash
# 复制配置文件
cp config.example.json config.json

# 编辑配置文件
# Windows: 记事本打开 config.json
# macOS/Linux: nano config.json
```

配置说明见 [配置说明](#配置说明)

#### 5. 初始化数据库（可选）

```bash
cd backend
python scripts/init_database.py
cd ..
```

#### 6. 启动后端

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端会在 http://localhost:8000 启动

#### 7. 启动前端（新终端）

```bash
cd frontend
python -m http.server 5173 --bind 0.0.0.0
```

**注意**: Windows 用户如果端口被占用，可以使用其他端口：
```bash
python -m http.server 3000 --bind 0.0.0.0
```

#### 8. 配置前端

编辑 `frontend/config.js`，设置后端地址：

```javascript
window.LOBSTER_CONFIG = {
  API_BASE: "http://localhost:8000",
  WS_URL: "ws://localhost:8000/ws"
};
```

#### 9. 访问应用

打开浏览器访问：

- **前端页面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

#### 10. 停止服务

在运行后端和前端的终端按 `Ctrl+C`

---

## ⚙️ 配置说明

### 配置文件结构

```json
{
  "app": {
    "name": "OpenClaw 办公室",
    "version": "2.2.0",
    "description": "AI 团队工作空间 - 上帝视角的实时监控"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "frontend_port": 5173
  },
  "database": {
    "path": "./openclaw_office.db",
    "timezone": "Asia/Shanghai"
  },
  "agents": {
    "scan_mode": "auto",
    "scan_base_dir": "~/.openclaw/agents",
    "custom_agents": []
  },
  "token_budget": {
    "daily": 500000,
    "monthly": 10000000
  },
  "data_sync": {
    "request_sync_interval_minutes": 5,
    "agent_sync_interval_minutes": 2,
    "session_sync_interval_minutes": 5,
    "task_sync_interval_minutes": 10,
    "request_lookback_hours": 6,
    "agent_lookback_hours": 1,
    "session_lookback_hours": 24
  },
  "features": {
    "handover_enabled": true,
    "reminder_enabled": true,
    "feishu_enabled": false,
    "task_extraction_enabled": true
  },
  "feishu": {
    "webhook_url": "",
    "app_id": "",
    "app_secret": ""
  }
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| app.name | 应用名称 | OpenClaw 办公室 |
| app.version | 应用版本 | 1.0.0 |
| app.description | 应用描述 | AI 团队工作空间 - 上帝视角的实时监控 |
| server.host | 服务器主机 | 0.0.0.0 |
| server.port | 后端端口 | 8000 |
| server.frontend_port | 前端端口 | 5173 |
| database.path | 数据库路径 | ./openclaw_office.db |
| database.timezone | 数据库时区 | Asia/Shanghai |
| agents.scan_mode | Agent 扫描模式 | auto |
| agents.scan_base_dir | Agent 扫描基础目录 | ~/.openclaw/agents |
| agents.custom_agents | 自定义 Agent 列表 | [] |
| token_budget.daily | 每日 Token 预算 | 500000 |
| token_budget.monthly | 每月 Token 预算 | 10000000 |
| data_sync.request_sync_interval_minutes | 请求同步间隔（分钟） | 5 |
| data_sync.agent_sync_interval_minutes | Agent 同步间隔（分钟） | 2 |
| data_sync.session_sync_interval_minutes | 会话同步间隔（分钟） | 5 |
| data_sync.task_sync_interval_minutes | 任务同步间隔（分钟） | 10 |
| data_sync.request_lookback_hours | 请求回溯小时数 | 6 |
| data_sync.agent_lookback_hours | Agent 回溯小时数 | 1 |
| data_sync.session_lookback_hours | 会话回溯小时数 | 24 |
| features.handover_enabled | 是否启用任务移交 | true |
| features.reminder_enabled | 是否启用督促功能 | true |
| features.feishu_enabled | 是否启用飞书集成 | false |
| features.task_extraction_enabled | 是否启用任务提取 | true |
| feishu.webhook_url | 飞书 Webhook URL | "" |
| feishu.app_id | 飞书应用 ID | "" |
| feishu.app_secret | 飞书应用密钥 | "" |

### 环境变量

可以使用环境变量覆盖配置：

```bash
# 端口配置
LOBSTER_BACKEND_PORT=8000
LOBSTER_FRONTEND_PORT=5173

# Token 预算
LOBSTER_TOKEN_BUDGET_DAILY=500000
LOBSTER_TOKEN_BUDGET_MONTHLY=10000000

# 飞书 Webhook（可选）
FEISHU_WEBHOOK_URL=your-webhook-url

# 同步间隔（分钟）
LOBSTER_SYNC_REQUEST_INTERVAL=5
LOBSTER_SYNC_AGENT_INTERVAL=2
LOBSTER_SYNC_SESSION_INTERVAL=5
LOBSTER_SYNC_TASK_INTERVAL=10
```

---

## ❓ 常见问题

### Q: 端口被占用怎么办？

**A**: 修改端口配置

Docker 方式：
```bash
# 编辑 docker-compose.yml
# 修改 ports 映射
ports:
  - "8080:8000"   # 后端改为 8080
  - "3000:5173"   # 前端改为 3000
```

脚本方式：
```bash
# 设置环境变量
export LOBSTER_BACKEND_PORT=8080
export LOBSTER_FRONTEND_PORT=3000

# 或编辑 .env 文件
```

### Q: 如何更新到新版本？

**A**:

Docker 方式：
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

脚本方式：
```bash
# 拉取最新代码
git pull

# 重新安装依赖（如果有变化）
cd backend
pip install -r requirements.txt
cd ..

# 重启服务
./stop.sh
./start.sh
```

### Q: 数据存储在哪里？

**A**:

Docker 方式：
- 数据库: `./backend/openclaw_office.db`
- 日志: `./backend/logs/`
- 配置: `./config.json`

脚本方式：
- 数据库: `backend/openclaw_office.db`
- 日志: `backend/logs/`
- 配置: `config.json`

### Q: 如何备份数据？

**A**:

```bash
# 备份数据库
cp backend/openclaw_office.db backup/openclaw_office_$(date +%Y%m%d).db

# 备份配置
cp config.json backup/config_$(date +%Y%m%d).json
```

### Q: 支持局域网访问吗？

**A**: 支持！

- 启动时使用 `0.0.0.0` 绑定（已默认配置）
- 防火墙开放相应端口
- 访问 `http://你的IP:5173`

---

## 🔧 故障排查

### 问题：Docker 启动失败

**排查步骤**:
1. 检查 Docker 是否运行: `docker ps`
2. 查看日志: `docker-compose logs`
3. 检查端口是否被占用
4. 检查配置文件格式是否正确

### 问题：后端启动失败

**排查步骤**:
1. 检查 Python 版本: `python --version`
2. 检查依赖是否安装: `pip list`
3. 查看错误信息
4. 检查端口是否被占用

### 问题：前端无法连接后端

**排查步骤**:
1. 确认后端已启动
2. 检查 `frontend/config.js` 配置
3. 检查浏览器控制台错误
4. 确认防火墙设置

### 问题：数据不同步

**排查步骤**:
1. 检查网络连接
2. 查看后端日志
3. 检查同步间隔配置
4. 检查 Agent 扫描目录配置

### 获取帮助

如果问题仍未解决：
1. 查看 [README.md](./README.md)
2. 提交 [Issue](https://github.com/你的用户名/openclaw-office/issues)
3. 查看测试文档 [test/](./test/)

---

## 📞 技术支持

- GitHub Issues: https://github.com/你的用户名/openclaw-office/issues
- 文档: https://github.com/你的用户名/openclaw-office/tree/main/docs

---

**祝你使用愉快！** 🦞✨
