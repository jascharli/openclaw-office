# OpenClaw 办公室 - 数据库设计文档

**版本**: v1.0.0
**最后更新**: 2026-03-30
**维护**: dev-claw (CTO)

## 📋 目录

1. [1. 核心表结构](#1-核心表结构)
2. [2. 辅助表结构](#2-辅助表结构)

---

## 1. 核心表结构

### AgentStatus 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `id` | `Integer` | `PRIMARY KEY, INDEX` | 主键 |
| `agent_id` | `String(100)` | `NOT NULL, UNIQUE, INDEX` | Agent 唯一标识 |
| `agent_name` | `String(200)` | | Agent 名称 |
| `status` | `String(50)` | `NOT NULL` | 状态（idle, conversing, working） |
| `task_id` | `String(100)` | | 当前任务 ID |
| `task_name` | `String(500)` | | 当前任务名称 |
| `progress` | `Float` | `DEFAULT 0.0` | 任务进度 |
| `elapsed_time` | `Integer` | `DEFAULT 0` | 已用时间（秒） |
| `estimated_remaining` | `Integer` | `DEFAULT 0` | 预计剩余时间（秒） |
| `token_used` | `Integer` | `DEFAULT 0` | 已用 Token |
| `last_activity` | `DateTime` | `NOT NULL, INDEX` | 最后活跃时间（北京时间） |
| `created_at` | `DateTime` | `DEFAULT utcnow` | 创建时间 |
| `updated_at` | `DateTime` | `DEFAULT utcnow, ON UPDATE utcnow` | 更新时间 |

### TaskRecord 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `id` | `Integer` | `PRIMARY KEY, INDEX` | 主键 |
| `task_id` | `String(100)` | `NOT NULL, UNIQUE, INDEX` | 任务唯一标识 |
| `task_name` | `String(500)` | `NOT NULL` | 任务名称 |
| `agent_id` | `String(100)` | `NOT NULL, INDEX` | 执行 Agent |
| `task_type` | `String(50)` | `NOT NULL, DEFAULT 'cron'` | 任务类型（session/cron） |
| `session_id` | `String(100)` | `INDEX` | 关联 Session ID |
| `status` | `String(50)` | `NOT NULL` | 状态（in_progress/completed/cancelled/blocked/pending） |
| `priority` | `Integer` | `DEFAULT 2` | 优先级（0:P0, 1:P1, 2:P2, 3:P3） |
| `started_at` | `DateTime` | | 开始时间 |
| `completed_at` | `DateTime` | | 完成时间 |
| `token_used` | `Integer` | `DEFAULT 0` | 已用 Token |
| `progress_log` | `Text` | | 进度日志（JSON 格式） |
| `created_at` | `DateTime` | `NOT NULL, INDEX` | 创建时间（北京时间） |

### RequestLog 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| `id` | `Integer` | `PRIMARY KEY, INDEX` | 主键 |
| `request_id` | `String(100)` | `NOT NULL, UNIQUE, INDEX` | 请求唯一标识 |
| `agent_id` | `String(100)` | `NOT NULL, INDEX` | Agent ID |
| `agent_name` | `String(200)` | | Agent 名称 |
| `request_type` | `String(50)` | | 请求类型（chat, tool, search 等） |
| `provider` | `String(100)` | | 服务商（bailian, openai, anthropic 等） |
| `model_name` | `String(100)` | | 模型名称 |
| `action` | `String(200)` | | 具体动作描述 |
| `tokens_input` | `Integer` | `DEFAULT 0` | 输入 Token |
| `tokens_output` | `Integer` | `DEFAULT 0` | 输出 Token |
| `tokens_total` | `Integer` | `DEFAULT 0` | 总 Token |
| `tokens_cache_read` | `Integer` | `DEFAULT 0` | 缓存读取 |
| `tokens_cache_write` | `Integer` | `DEFAULT 0` | 缓存写入 |
| `cost_input` | `Float` | `DEFAULT 0.0` | 输入成本 |
| `cost_output` | `Float` | `DEFAULT 0.0` | 输出成本 |
| `cost_total` | `Float` | `DEFAULT 0.0` | 总成本 |
| `status` | `String(50)` | `DEFAULT 'success'` | 状态（success, error） |
| `error_message` | `Text` | | 错误信息 |
| `response_time_ms` | `Integer` | | 响应时间（毫秒） |
| `session_id` | `String(100)` | `INDEX` | Session ID |
| `task_id` | `String(100)` | | 任务 ID |
| `message_id` | `String(100)` | | 消息 ID |
| `created_at` | `DateTime` | `DEFAULT utcnow, INDEX` | 创建时间 |

---

## 2. 辅助表结构

### TokenLog 表
| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `Integer` | `PRIMARY KEY, INDEX` | 主键 |
| `agent_id` | `String(100)` | `NOT NULL, INDEX` | Agent ID |
| `task_id` | `String(100)` | | 任务 ID |
| `token_count` | `Integer` | `NOT NULL` | Token 数量 |
| `token_type` | `String(50)` | | Token 类型（input, output, total） |
| `action` | `String(100)` | | 动作（chat, task, search 等） |
| `created_at` | `DateTime` | `DEFAULT utcnow, INDEX` | 创建时间 |

### ReminderLog 表
| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `Integer` | `PRIMARY KEY, INDEX` | 主键 |
| `agent_id` | `String(100)` | `NOT NULL, INDEX` | Agent ID |
| `task_id` | `String(100)` | | 任务 ID |
| `reminder_type` | `String(50)` | | 督促类型（auto, manual） |
| `reminder_interval` | `Integer` | | 督促间隔（分钟） |
| `response_status` | `String(50)` | | 响应状态（responded, ignored, blocked, sent, failed） |
| `response_content` | `Text` | | 响应内容 |
| `created_at` | `DateTime` | `DEFAULT utcnow, INDEX` | 创建时间 |

### TaskHandover 表
| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `Integer` | `PRIMARY KEY, INDEX` | 主键 |
| `handover_id` | `String(100)` | `NOT NULL, UNIQUE, INDEX` | 交接 ID |
| `task_id` | `String(100)` | `NOT NULL, INDEX` | 任务 ID |
| `task_name` | `String(500)` | `NOT NULL` | 任务名称 |
| `from_agent_id` | `String(100)` | `NOT NULL, INDEX` | 交出方 |
| `from_agent_name` | `String(200)` | | 交出方名称 |
| `to_agent_id` | `String(100)` | `NOT NULL, INDEX` | 接收方 |
| `to_agent_name` | `String(200)` | | 接收方名称 |
| `handover_type` | `String(50)` | `NOT NULL` | 交接类型（full, partial, collaboration） |
| `progress_at_handover` | `Float` | `DEFAULT 0.0` | 交接时进度 |
| `context_data` | `Text` | | 上下文数据（JSON 格式） |
| `notes` | `Text` | | 交接说明/备注 |
| `status` | `String(50)` | `NOT NULL, DEFAULT 'pending'` | 状态（pending, accepted, rejected, completed） |
| `accepted_at` | `DateTime` | | 接收时间 |
| `completed_at` | `DateTime` | | 完成时间 |
| `created_at` | `DateTime` | `DEFAULT utcnow, INDEX` | 创建时间 |
| `updated_at` | `DateTime` | `DEFAULT utcnow, ON UPDATE utcnow` | 更新时间 |

### Session 表
| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `session_id` | `String(100)` | `PRIMARY KEY, INDEX` | Session ID |
| `agent_id` | `String(100)` | `NOT NULL, INDEX` | Agent ID |
| `file_path` | `String(500)` | `NOT NULL` | 会话文件路径 |
| `last_activity` | `DateTime` | `NOT NULL, INDEX` | 最后活跃时间（北京时间） |
| `message_count` | `Integer` | `DEFAULT 0` | 消息数量 |
| `created_at` | `DateTime` | `DEFAULT utcnow` | 创建时间 |
| `updated_at` | `DateTime` | `DEFAULT utcnow, ON UPDATE utcnow` | 更新时间 |

### CollaborationGroup 表
| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `Integer` | `PRIMARY KEY, INDEX` | 主键 |
| `group_id` | `String(100)` | `NOT NULL, UNIQUE, INDEX` | 协作组 ID |
| `group_name` | `String(200)` | `NOT NULL` | 协作组名称 |
| `members` | `Text` | `NOT NULL` | 组成员（JSON 数组格式） |
| `active_task_id` | `String(100)` | | 当前任务 ID |
| `active_task_name` | `String(500)` | | 当前任务名称 |
| `status` | `String(50)` | `DEFAULT 'active'` | 状态（active, archived） |
| `created_at` | `DateTime` | `DEFAULT utcnow, INDEX` | 创建时间 |
| `updated_at` | `DateTime` | `DEFAULT utcnow, ON UPDATE utcnow` | 更新时间 |

---

**维护**: dev-claw (CTO)
**最后更新**: 2026-03-30
