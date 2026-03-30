# OpenClaw 办公室 - API 文档

**版本**: v1.0.0
**最后更新**: 2026-03-30
**维护**: dev-claw (CTO)

## 📋 目录

1. [1. Agent 相关 API](#1-agent-相关-api)
2. [2. 任务相关 API](#2-任务相关-api)
3. [3. 统计相关 API](#3-统计相关-api)
4. [4. 督促相关 API](#4-督促相关-api)

---

## 1. Agent 相关 API

| API 路径 | 方法 | 功能 | 请求参数 | 成功响应 |
|----------|------|------|----------|----------|
| `/api/v1/agents/status` | GET | 获取 Agent 状态 | - | `{"agents": [...], "summary": {...}}` |
| `/api/v1/agents/tasks` | GET | 获取 Agent 任务 | - | `{"agent_id": {...}}` |
| `/api/v1/agents/{agent_id}` | GET | 获取单个 Agent 状态 | agent_id | `{"agent_id": "...", "status": "..."}` |

---

## 2. 任务相关 API

| API 路径 | 方法 | 功能 | 请求参数 | 成功响应 |
|----------|------|------|----------|----------|
| `/api/v1/tasks` | GET | 获取任务队列 | - | `{"in_progress": [...], "pending": [...], "blocked": [...], "completed_today": [...]}` |
| `/api/v1/tasks` | POST | 创建新任务 | task_data | `{"success": true, "task_id": "..."}` |
| `/api/v1/cron/sync` | POST | 手动触发 cron 任务同步 | - | `{"success": true, "message": "Cron tasks synced successfully"}` |
| `/api/v1/handovers` | POST | 创建任务移交 | handover_data, auto_extract | `{"success": true, "handover_id": "...", "task_updated": true}` |
| `/api/v1/handovers` | GET | 获取移交列表 | status, agent_id, task_id | `{"handovers": [...], "total": 10}` |
| `/api/v1/handovers/{handover_id}` | GET | 获取交接详情 | handover_id | `{"handover": {...}}` |
| `/api/v1/handovers/{handover_id}/accept` | POST | 接受任务移交 | handover_id, accept_data | `{"success": true, "handover": {...}}` |
| `/api/v1/handovers/{handover_id}/reject` | POST | 拒绝任务移交 | handover_id, reject_data | `{"success": true, "handover": {...}}` |
| `/api/v1/handovers/{handover_id}/complete` | POST | 完成任务移交 | handover_id, complete_data | `{"success": true, "handover": {...}}` |

---

## 3. 统计相关 API

| API 路径 | 方法 | 功能 | 请求参数 | 成功响应 |
|----------|------|------|----------|----------|
| `/api/v1/tokens/stats` | GET | 获取 Token 统计 | period | `{"period": "...", "total_used": 12345, "by_agent": [...], "budget": {...}}` |
| `/api/v1/tokens/budget` | PUT | 更新 Token 预算 | daily, monthly | `{"success": true, "budget": {...}}` |
| `/api/v1/requests/stats` | GET | 获取请求统计 | period, agent_id, date, start_date, end_date | `{"hourly": [...], "daily": [...]}` |
| `/api/v1/requests/providers` | GET | 获取服务商统计 | date | `{"date": "...", "providers": [...]}` |
| `/api/v1/requests/models` | GET | 获取模型统计 | date, provider | `{"date": "...", "models": [...]}` |
| `/api/v1/requests/agents` | GET | 获取 Agent 统计 | - | `{"agents": [...]}` |
| `/api/v1/requests/sync` | POST | 同步请求日志 | lookback_hours | `{"success": true, "synced_count": 100, "lookback_hours": 24}` |
| `/api/v1/config/sync` | POST | 同步配置到后端 | agent_sync_interval_minutes, task_sync_interval_minutes, request_sync_interval_minutes, cron_sync_interval_minutes | `{"success": true, "message": "配置已保存并生效", "config": {...}}` |

---

## 4. 督促相关 API

| API 路径 | 方法 | 功能 | 请求参数 | 成功响应 |
|----------|------|------|----------|----------|
| `/api/v1/reminders/send` | POST | 发送督促消息 | agent_id, interval, message | `{"success": true, "reminder_id": 123, "sent_at": "...", "feishu_result": {...}}` |
| `/api/v1/reminders/history` | GET | 获取督促历史 | agent_id, limit | `{"reminders": [...]}` |

---

**维护**: dev-claw (CTO)
**最后更新**: 2026-03-30
