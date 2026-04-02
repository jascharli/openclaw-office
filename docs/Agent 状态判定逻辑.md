# 龙虾办公室 - Agent 状态判定逻辑

**版本**: v2.0  
**更新日期**: 2026-03-26  
**维护**: dev-claw (CTO)

---

## 📋 概述

龙虾办公室通过**多维度判定逻辑**将每个 Agent 归类到三个区域之一：

- **😴 休闲区 (idle)** - 空闲待命
- **💬 对话区 (conversing)** - 与用户对话交互
- **💼 办公区 (working)** - 执行具体任务

---

## 🎯 三区域定义

### 1️⃣ 休闲区 (idle)

**定义**：Agent 当前没有活跃任务，处于空闲待命状态

**特征**：
- ❌ 无用户交互
- ❌ 无工具调用
- ❌ 无任务上下文
- ⏰ 最后活跃时间 > 5 分钟

**典型场景**：
- Agent 刚启动，等待任务分配
- 完成任务后进入待命状态
- 长时间无交互（如深夜）

**数据库字段**：
```sql
status = 'idle'
task_id = NULL
task_name = NULL
```

---

### 2️⃣ 对话区 (conversing)

**定义**：Agent 正在与用户进行对话交互，但没有执行具体任务

**特征**：
- ✅ 有用户提问
- ✅ 有 AI 回复
- ❌ 无工具调用或很少
- ⏰ 最近 5 分钟内有活跃

**典型场景**：
- 用户问："今天天气怎么样？"
- 用户问："解释一下这个概念"
- 闲聊、咨询、讨论

**数据库字段**：
```sql
status = 'conversing'
task_id = NULL
task_name = NULL
elapsed_time = 对话时长（秒）
```

---

### 3️⃣ 办公区 (working)

**定义**：Agent 正在执行具体任务，有明确的目标和进度

**特征**：
- ✅ 有明确任务目标
- ✅ 频繁工具调用
- ✅ 有任务上下文
- 📊 有进度追踪

**典型场景**：
- 执行 cron 定时任务（如"工作日志提醒"）
- 代码开发（如"龙虾办公室开发"）
- 文档整理
- 数据同步
- API 调用

**数据库字段**：
```sql
status = 'working'
task_id = 'task-001'
task_name = '龙虾办公室开发'
progress = 0.45  # 45% 完成度
elapsed_time = 1350  # 已用 22.5 分钟
```

---

## 🔍 核心差别对比

| 维度 | 休闲区 (idle) | 对话区 (conversing) | 办公区 (working) |
|------|--------------|-------------------|-----------------|
| **用户交互** | ❌ 无 | ✅ 有问答 | ⚠️ 可能有/无 |
| **工具调用** | ❌ 无 | ❌ 无 | ✅ 频繁 |
| **任务目标** | ❌ 无 | ❌ 无 | ✅ 明确 |
| **进度追踪** | ❌ 无 | ❌ 无 | ✅ 有进度% |
| **Token 消耗** | 低 | 中等 | 高 |
| **典型时长** | 无限 | 5-30 分钟 | 10 分钟 - 数小时 |
| **示例** | 待命 | 问答、闲聊 | 开发、同步、报告 |

---

## 🧠 判定逻辑（优先级从高到低）

### 判定流程图

```
┌──────────────────────────────────────────┐
│  开始判定                                 │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 0. 最后活跃 > 1 小时？                      │
│    YES → idle (长时间无响应)              │
│    NO  ↓                                  │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 1. 有 cron 任务在执行？                    │
│    YES → working (任务名=cron 任务名)      │
│    NO  ↓                                  │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 2. Session 中有任务上下文？                │
│    YES → working (任务名=提取的任务名)     │
│    NO  ↓                                  │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 3. 工具调用频繁 (≥2 次)？                   │
│    YES → working                          │
│    NO  ↓                                  │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 4. 工具调用 > AI 回复×2？                  │
│    YES → working                          │
│    NO  ↓                                  │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 5. 有对话交互 (user>0 AND assistant>0)?   │
│    YES → conversing                       │
│    NO  ↓                                  │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 6. 最后活跃 < 5 分钟？                      │
│    YES → idle                            │
│    NO  ↓                                  │
└────────────────┬─────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ idle (默认)   │
         └───────────────┘
```

---

## 📊 判定规则详细说明

### 规则 0：长时间无响应优先（最高优先级）

**逻辑**：
```python
time_since_activity = (datetime.utcnow() - last_activity).total_seconds() / 3600
if time_since_activity > 1.0:
    return 'idle', None
```

**时间阈值**：
```python
LONG_IDLE_THRESHOLD = 1.0  # 1 小时
```

**原因**：
- 如果 Agent 超过 1 小时无活跃，说明已停止工作
- 即使 session 中有历史工具调用记录，也不应判定为 working
- 避免误判（如 daughter 昨晚的对话被误判为当前工作）

**示例**：
- daughter：最后活跃 20:20（昨晚），距今 5.2 小时 → **idle** ✅
- dev-claw：最后活跃 09:28（刚刚），距今 0 分钟 → 继续后续判定

---

### 规则 1：Cron 任务优先

**逻辑**：
```python
if agent_id in active_cron_tasks:
    return 'working', cron_task['task_name']
```

**原因**：
- cron 任务是明确的定时任务
- 有清晰的任务名称和执行时间
- 优先级最高

**数据来源**：
- `openclaw cron list` 命令
- 解析任务名称中的 agent 归属（如"work-claw 心跳" → work-claw）

---

### 规则 2：任务上下文检测

**逻辑**：
```python
if session_analysis['has_task_context']:
    return 'working', session_analysis['task_name']
```

**检测方法**：
- 检测用户消息中的任务关键词：`请执行`、`帮我`、`完成`、`开发`、`创建`
- 检测 AI 消息中的任务关键词：`任务`、`执行`、`完成`、`进度`、`正在`
- 从引号中提取任务名称

**示例**：
- 用户："请执行**数据同步**任务" → task_name = "数据同步"
- AI："正在执行**龙虾办公室开发**" → has_task_context = True

---

### 规则 3：工具调用频率

**逻辑**：
```python
if tool_count >= 2:
    return 'working', '工具执行中'

if tool_count > assistant_count * 2.0:
    return 'working', '工具执行中'
```

**权重配置**：
```python
WORKING_MIN_TOOL_CALLS = 2         # 最少工具调用次数
TOOL_CALL_WEIGHT = 2.0             # 工具调用权重
```

**原因**：
- 工具调用是工作的明确信号
- 频繁调用工具说明在执行复杂任务

---

### 规则 4：对话活跃度

**逻辑**：
```python
if user_count > 0 and assistant_count > 0:
    time_since_activity = (now - last_activity).seconds / 60
    if time_since_activity < 5:
        return 'conversing', None
```

**时间阈值**：
```python
RECENT_ACTIVITY_THRESHOLD = 5    # 5 分钟
CONVERSING_MAX_DURATION = 30     # 对话状态最长 30 分钟
```

---

### 规则 5：默认空闲

**逻辑**：
```python
time_since_activity = (now - last_activity).seconds / 60
if time_since_activity > 5:
    return 'idle', None

return 'idle', None  # 默认
```

---

## 🔧 实现代码

### 核心函数

```python
def determine_agent_status(
    session_analysis: Dict,
    active_cron_tasks: Dict,
    agent_id: str,
    active_minutes: int,
    last_activity: datetime
) -> Tuple[str, Optional[str]]:
    """
    多维度判断 Agent 状态（核心逻辑）
    
    参数：
    - session_analysis: session 消息分析结果
    - active_cron_tasks: 当前活跃的 cron 任务
    - agent_id: Agent ID
    - active_minutes: 活跃分钟数
    - last_activity: 最后活跃时间
    
    返回：
    (status, task_name)
    - status: 'idle' | 'conversing' | 'working'
    - task_name: 任务名称或 None
    """
    
    # 1. 最高优先级：有 cron 任务在执行
    if agent_id in active_cron_tasks:
        return 'working', active_cron_tasks[agent_id]['task_name']
    
    # 2. 次高优先级：session 中有明确任务上下文
    if session_analysis and session_analysis.get('has_task_context'):
        task_name = session_analysis.get('task_name') or '未命名任务'
        return 'working', task_name
    
    # 3. 检查工具调用频率
    if session_analysis:
        tool_count = session_analysis.get('tool_count', 0)
        assistant_count = session_analysis.get('assistant_count', 0)
        
        if tool_count >= WORKING_MIN_TOOL_CALLS:
            return 'working', '工具执行中'
        
        if tool_count > assistant_count * TOOL_CALL_WEIGHT:
            return 'working', '工具执行中'
    
    # 4. 检查对话活跃度
    if session_analysis:
        user_count = session_analysis.get('user_count', 0)
        assistant_count = session_analysis.get('assistant_count', 0)
        
        if user_count > 0 and assistant_count > 0:
            time_since_activity = (datetime.utcnow() - last_activity).total_seconds() / 60
            if time_since_activity < RECENT_ACTIVITY_THRESHOLD:
                return 'conversing', None
    
    # 5. 检查活跃时间
    time_since_activity = (datetime.utcnow() - last_activity).total_seconds() / 60
    if time_since_activity > RECENT_ACTIVITY_THRESHOLD:
        return 'idle', None
    
    # 6. 默认：空闲
    return 'idle', None
```

---

## 📈 状态流转

### 典型流转路径

```
启动 → idle → (用户提问) → conversing → (分配任务) → working → (完成) → idle
```

### 直接流转

- `idle → working`: 直接分配任务（如 cron 触发）
- `conversing → idle`: 对话结束，无任务
- `working → conversing`: 任务暂停，用户打断提问

### 流转触发条件

| 从 | 到 | 触发条件 |
|----|----|---------|
| idle | conversing | 用户发送消息 |
| idle | working | 分配任务/cron 触发 |
| conversing | working | 用户分配任务 |
| conversing | idle | 5 分钟无活跃 |
| working | conversing | 用户打断提问 |
| working | idle | 任务完成 |

---

## 🧪 测试用例

### 测试场景 1：Cron 任务执行中

**输入**：
- `active_cron_tasks = {'work-claw': {'task_name': '工作日志提醒'}}`
- `session_analysis = None`

**预期输出**：
```python
status = 'working'
task_name = '工作日志提醒'
```

---

### 测试场景 2：对话交互中

**输入**：
- `active_cron_tasks = {}`
- `session_analysis = {'user_count': 3, 'assistant_count': 2, 'tool_count': 0}`
- `active_minutes = 2`

**预期输出**：
```python
status = 'conversing'
task_name = None
```

---

### 测试场景 3：工具调用频繁

**输入**：
- `active_cron_tasks = {}`
- `session_analysis = {'user_count': 0, 'assistant_count': 2, 'tool_count': 5}`
- `active_minutes = 10`

**预期输出**：
```python
status = 'working'
task_name = '工具执行中'
```

---

### 测试场景 4：空闲状态

**输入**：
- `active_cron_tasks = {}`
- `session_analysis = {'user_count': 0, 'assistant_count': 0, 'tool_count': 0}`
- `active_minutes = 30`

**预期输出**：
```python
status = 'idle'
task_name = None
```

---

## 📝 版本记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-03-23 | 初始版本 - 简单判定逻辑 |
| v2.0 | 2026-03-26 | 多维度判定 - 增加 cron 任务、任务上下文、工具调用权重 |

---

## 🔗 相关文件

- `backend/openclaw_sync.py` - 实现代码
- `backend/database.py` - 数据库 Schema
- `backend/main.py` - API 端点
- `docs/需求文档.md` - 整体需求

---

**维护**: dev-claw (CTO)  
**最后更新**: 2026-03-26  
**下次审查**: 2026-04-02
