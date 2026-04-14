# 🦞 龙虾办公室 (OpenClaw Office)

**AI 团队管理系统 - v2.3**

[![GitHub release](https://img.shields.io/github/release/你的用户名/openclaw-office.svg)](https://github.com/你的用户名/openclaw-office/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## 📋 项目简介

龙虾办公室 (OpenClaw Office)是一个专为 AI 团队设计的智能管理系统，帮助团队高效管理 Agent 状态、任务、数据统计和督促功能。想法参考一堂 truman的分享,产品设计和代码完全自我编写.

### ✨ 核心功能

- 🎯 **Agent 状态监控** - 三区域显示（空闲/对话中/工作中），实时更新
- 📋 **任务管理** - 任务清单、筛选、移交功能
- 📊 **数据统计** - 请求统计、Token 统计、分模型统计
- 🔔 **督促功能** - 手动督促 + 自动督促（4种触发条件）
- 📱 **响应式设计** - 完美适配 PC、平板、移动端
- 🔄 **WebSocket 实时更新** - 状态实时同步

### 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Python 3.11+ |
| 前端 | Vue 3 + JavaScript |
| 数据库 | SQLite + SQLAlchemy |
| 实时通信 | WebSocket |
| 定时任务 | APScheduler |
| 部署 | Docker + Docker Compose |

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐 ⭐⭐⭐⭐⭐）

最简单的方式，一键启动！

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/openclaw-office.git
cd openclaw-office

# 2. 配置（可选）
cp config.example.json config.json
# 编辑 config.json 自定义配置

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 前端页面: http://localhost:5173
# API 文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/health

# 5. 停止服务
docker-compose down
```

### 方式二：脚本部署（推荐 ⭐⭐⭐⭐）

适合有 Python 基础的用户。

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/openclaw-office.git
cd openclaw-office

# 2. 安装依赖
./install.sh

# 3. 配置（可选）
cp config.example.json config.json
# 编辑 config.json 自定义配置

# 4. 启动服务
./start.sh        # 前台运行（关闭终端服务停止）
./start.sh -d     # 后台运行（推荐用于局域网访问）

# 5. 访问应用
# 前端页面: http://localhost:5173
# 局域网访问: http://你的IP:5173

# 6. 停止服务
./stop.sh

# 7. 查看日志（后台运行模式）
tail -f backend.log frontend.log
```

### 方式三：源码部署（推荐 ⭐⭐⭐）

适合开发者或需要自定义的用户。

详见 [INSTALL.md](./INSTALL.md)

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 项目介绍（本文档） |
| [INSTALL.md](./INSTALL.md) | 详细安装部署指南 |
| [USAGE.md](./USAGE.md) | 使用说明书 |
| [docs/](./docs/) | 技术文档 |
| [test/](./test/) | 测试文档 |

---

## 🎮 功能使用

### Agent 状态监控

访问首页即可看到 Agent 状态三区域显示：
- 🟢 **空闲** - 可承接新任务
- 🟡 **对话中** - 正在与用户对话
- 🔴 **工作中** - 正在执行任务

### 任务管理

- 查看所有 Agent 的任务清单
- 按 Agent、时间筛选任务
- 任务移交功能

### 数据统计

- 请求统计（今日总数、成功率）
- Token 统计（使用量、预算）
- 分模型统计
- 每小时请求趋势

### 督促功能

- 手动发送督促消息
- 自动督促（任务超时、无更新、Token超预算、进度停滞）

---

## 🧪 测试

项目包含完整的测试套件：

```bash
cd test

# 运行冒烟测试
python -m pytest scripts/test_smoke.py -v

# 运行回归测试
python -m pytest scripts/test_regression.py -v

# 运行所有测试
python -m pytest scripts/ -v
```

**测试结果**:
- 冒烟测试: 8/8 通过 ✅
- 回归测试: 105/105 通过 ✅
- 通过率: 100%

详细测试报告见 [test/](./test/)

---

## 🔧 开发

### 环境要求

- Python 3.11+
- pip
- Docker（可选）

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/openclaw-office.git
cd openclaw-office

# 2. 安装依赖
cd backend
pip install -r requirements.txt

# 3. 启动后端
python -m uvicorn main:app --reload --port 8000

# 4. 启动前端（新终端）
cd ../frontend
python -m http.server 5173

# 5. 访问
# 前端: http://localhost:5173
# 后端: http://localhost:8000/docs
```

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- FastAPI 团队
- Vue.js 团队
- 所有贡献者

---

## 📞 支持

如有问题，请：
- 提交 [Issue](https://github.com/你的用户名/openclaw-office/issues)
- 查看 [文档](./docs/)
- 查看 [常见问题](./INSTALL.md#-常见问题)

---

**享受使用 OpenClaw 办公室！** 🦞✨

---

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.3 | 2026-04-14 | 健康检测与自动恢复功能 |
| v2.2 | 2026-03-30 | 初始版本发布 |
