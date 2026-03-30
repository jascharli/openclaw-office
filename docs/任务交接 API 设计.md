# 任务交接功能 API 设计

**版本**: v1.0  
**日期**: 2026-03-26  
**状态**: 设计中

---

## 📋 功能概述

任务交接功能支持以下场景：
1. **完整交接** - Agent A 将任务完全移交给 Agent B
2. **部分交接** - Agent A 保留部分工作，移交另一部分
3. **协作模式** - 多个 Agent 共同完成一个任务

---

## 🔌 API 端点

### 1. 创建交接

```http
POST /api/v1/handovers
Content-Type: application/json

{
  "task_id": "task-001",
  "task_name": "API 开发",
  "from_agent_id": "dev-claw",
  "to_agent_id": "work-claw",
  "handover_type": "full",  // full, partial, collaboration
  "progress_at_handover": 0.6,  // 60% 完成
  "context_data": {
    "completed": "后端 API 开发",
    "pending": "前端开发",
    "dependencies": ["Python 3.12", "端口 8000"],
    "notes": "注意参数验证"
  },
  "notes": "请继续完成前端开发"
}

Response: 201 Created
{
  "success": true,
  "handover_id": "handover-001",
  "handover": {
    "id": 1,
    "handover_id": "handover-001",
    "task_id": "task-001",
    "from_agent_id": "dev-claw",
    "to_agent_id": "work-claw",
    "status": "pending",
    "created_at": "2026-03-26T00:00:00"
  }
}
```

---

### 2. 查询交接列表

```http
GET /api/v1/handovers?status=pending&agent_id=work-claw

Query Parameters:
- status: pending, accepted, rejected, completed（可选）
- agent_id: 按 Agent 过滤（可选）
- task_id: 按任务过滤（可选）

Response: 200 OK
{
  "handovers": [
    {
      "id": 1,
      "handover_id": "handover-001",
      "task_id": "task-001",
      "task_name": "API 开发",
      "from_agent_id": "dev-claw",
      "from_agent_name": "dev-claw",
      "to_agent_id": "work-claw",
      "to_agent_name": "work-claw",
      "handover_type": "full",
      "progress_at_handover": 0.6,
      "context_data": {...},
      "notes": "请继续完成前端开发",
      "status": "pending",
      "created_at": "2026-03-26T00:00:00",
      "updated_at": "2026-03-26T00:00:00"
    }
  ],
  "total": 1
}
```

---

### 3. 查询交接详情

```http
GET /api/v1/handovers/{handover_id}

Response: 200 OK
{
  "handover": {
    "id": 1,
    "handover_id": "handover-001",
    "task_id": "task-001",
    "task_name": "API 开发",
    "from_agent_id": "dev-claw",
    "from_agent_name": "dev-claw",
    "to_agent_id": "work-claw",
    "to_agent_name": "work-claw",
    "handover_type": "full",
    "progress_at_handover": 0.6,
    "context_data": {
      "completed": "后端 API 开发",
      "pending": "前端开发",
      "dependencies": ["Python 3.12", "端口 8000"],
      "notes": "注意参数验证"
    },
    "notes": "请继续完成前端开发",
    "status": "pending",
    "accepted_at": null,
    "completed_at": null,
    "created_at": "2026-03-26T00:00:00",
    "updated_at": "2026-03-26T00:00:00"
  }
}
```

---

### 4. 接受交接

```http
POST /api/v1/handovers/{handover_id}/accept
Content-Type: application/json

{
  "message": "收到，我会继续完成前端开发"  // 可选
}

Response: 200 OK
{
  "success": true,
  "handover": {
    "id": 1,
    "handover_id": "handover-001",
    "status": "accepted",
    "accepted_at": "2026-03-26T00:05:00",
    ...
  }
}
```

---

### 5. 拒绝交接

```http
POST /api/v1/handovers/{handover_id}/reject
Content-Type: application/json

{
  "reason": "当前任务已满，无法接收新任务"  // 必填
}

Response: 200 OK
{
  "success": true,
  "handover": {
    "id": 1,
    "handover_id": "handover-001",
    "status": "rejected",
    ...
  }
}
```

---

### 6. 完成交接

```http
POST /api/v1/handovers/{handover_id}/complete
Content-Type: application/json

{
  "summary": "前端开发已完成，总计 3 个页面",  // 交接总结
  "final_progress": 1.0  // 最终进度
}

Response: 200 OK
{
  "success": true,
  "handover": {
    "id": 1,
    "handover_id": "handover-001",
    "status": "completed",
    "completed_at": "2026-03-26T12:00:00",
    ...
  }
}
```

---

### 7. 创建协作组

```http
POST /api/v1/collaboration/groups
Content-Type: application/json

{
  "group_name": "用户管理功能开发组",
  "members": [
    {"agent_id": "dev-claw", "role": "lead", "responsibility": "后端 API"},
    {"agent_id": "work-claw", "role": "member", "responsibility": "前端开发"}
  ],
  "active_task_id": "task-002",
  "active_task_name": "用户管理功能"
}

Response: 201 Created
{
  "success": true,
  "group_id": "group-001",
  "group": {
    "id": 1,
    "group_id": "group-001",
    "group_name": "用户管理功能开发组",
    "members": [...],
    "status": "active",
    "created_at": "2026-03-26T00:00:00"
  }
}
```

---

### 8. 查询协作组列表

```http
GET /api/v1/collaboration/groups?status=active

Response: 200 OK
{
  "groups": [
    {
      "id": 1,
      "group_id": "group-001",
      "group_name": "用户管理功能开发组",
      "members": [
        {"agent_id": "dev-claw", "role": "lead", "responsibility": "后端 API"},
        {"agent_id": "work-claw", "role": "member", "responsibility": "前端开发"}
      ],
      "active_task_id": "task-002",
      "active_task_name": "用户管理功能",
      "status": "active",
      "created_at": "2026-03-26T00:00:00"
    }
  ],
  "total": 1
}
```

---

### 9. 添加到协作组

```http
POST /api/v1/collaboration/groups/{group_id}/members
Content-Type: application/json

{
  "agent_id": "main",
  "role": "member",
  "responsibility": "文档编写"
}

Response: 200 OK
{
  "success": true,
  "group": {
    "id": 1,
    "group_id": "group-001",
    "members": [
      {"agent_id": "dev-claw", "role": "lead", ...},
      {"agent_id": "work-claw", "role": "member", ...},
      {"agent_id": "main", "role": "member", "responsibility": "文档编写"}
    ],
    ...
  }
}
```

---

### 10. 从协作组移除

```http
DELETE /api/v1/collaboration/groups/{group_id}/members/{agent_id}

Response: 200 OK
{
  "success": true,
  "message": "Agent main 已从协作组移除"
}
```

---

## 📊 数据模型

### TaskHandover（任务交接记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| handover_id | String | 交接 ID（唯一） |
| task_id | String | 任务 ID |
| task_name | String | 任务名称 |
| from_agent_id | String | 交出方 Agent ID |
| from_agent_name | String | 交出方名称 |
| to_agent_id | String | 接收方 Agent ID |
| to_agent_name | String | 接收方名称 |
| handover_type | String | 交接类型（full/partial/collaboration） |
| progress_at_handover | Float | 交接时进度（0.0-1.0） |
| context_data | Text | 上下文数据（JSON） |
| notes | Text | 交接说明 |
| status | String | 状态（pending/accepted/rejected/completed） |
| accepted_at | DateTime | 接收时间 |
| completed_at | DateTime | 完成时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### CollaborationGroup（协作组）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| group_id | String | 协作组 ID（唯一） |
| group_name | String | 协作组名称 |
| members | Text | 成员列表（JSON 数组） |
| active_task_id | String | 当前任务 ID |
| active_task_name | String | 当前任务名称 |
| status | String | 状态（active/archived） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

## 🔔 WebSocket 通知

### 交接创建通知

```json
{
  "type": "handover_created",
  "data": {
    "handover_id": "handover-001",
    "from_agent_id": "dev-claw",
    "to_agent_id": "work-claw",
    "task_name": "API 开发"
  },
  "timestamp": "2026-03-26T00:00:00"
}
```

### 交接接受通知

```json
{
  "type": "handover_accepted",
  "data": {
    "handover_id": "handover-001",
    "accepted_by": "work-claw",
    "message": "收到，我会继续完成"
  },
  "timestamp": "2026-03-26T00:05:00"
}
```

---

## 📱 前端交互流程

### 场景 1：完整交接

```
1. 用户点击"交接"按钮
2. 弹出交接对话框
   - 选择接收方 Agent
   - 填写交接说明
   - 自动填充当前进度
3. 用户确认交接
4. 系统创建交接记录
5. 通知接收方 Agent
6. 接收方 Agent 确认接收
7. 任务状态更新
8. 交接完成
```

### 场景 2：协作组

```
1. 用户创建协作组
2. 添加成员 Agent
3. 分配任务给协作组
4. 成员 Agent 协作完成
5. 记录协作历史
```

---

## ✅ 验收标准

### 功能验收

- [ ] 能创建完整交接
- [ ] 能创建部分交接
- [ ] 能创建协作组
- [ ] 接收方能接受交接
- [ ] 接收方能拒绝交接
- [ ] 交接完成后状态正确更新
- [ ] WebSocket 通知正常推送
- [ ] 交接历史可查询

### 数据验收

- [ ] 交接记录完整保存
- [ ] 上下文数据不丢失
- [ ] 时间戳准确
- [ ] 状态流转正确

---

**下一步**: 开始后端实现
