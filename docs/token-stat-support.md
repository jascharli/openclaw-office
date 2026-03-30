# 📊 Token 统计支持状态显示

**功能日期**: 2026-03-27  
**版本**: v1.0.7

---

## 🎯 功能概述

在"Token 使用统计"标题后自动显示当前大模型服务是否支持 Token 数据统计。

---

## 📋 显示规则

### 支持 Token 统计 ✅

**条件**: 模型数据包含 `tokens` 字段且值有效

**显示**:
```
📊 Token 使用统计 ✅ bailian 的 qwen-plus 支持 Token 数据统计
```

**样式**: 绿色文字 (#10b981)

---

### 不支持 Token 统计 ❌

**条件**: 模型数据有 `count`（请求数）但 `tokens` 为 0 或 null

**显示**:
```
📊 Token 使用统计 ❌ bailian 的 qwen-turbo 不支持 Token 数据统计
```

**样式**: 红色文字 (#ef4444)

---

### 检测中 ⏳

**条件**: 模型数据为空或正在加载

**显示**:
```
📊 Token 使用统计 正在检测...
```

**样式**: 灰色文字 (#999)

---

## 🔧 技术实现

### 计算属性

**tokenStatsSupport**:
```javascript
tokenStatsSupport() {
  if (!this.providerStats.models?.models?.length) {
    return 'unknown'  // 检测中
  }
  
  const firstModel = this.providerStats.models.models[0]
  
  if (firstModel.tokens !== undefined && firstModel.tokens !== null) {
    return true  // 支持
  } else if (firstModel.count > 0) {
    return false  // 不支持
  }
  
  return 'unknown'  // 无法判断
}
```

**primaryModelName**:
```javascript
primaryModelName() {
  if (!this.providerStats.models?.models?.length) {
    return '大模型'
  }
  return this.providerStats.models.models[0].model || '大模型'
}
```

---

## 📱 UI 呈现

### 完整标题

```html
<h3>
  📊 Token 使用统计
  <span v-if="tokenStatsSupport === true" 
        style="color: #10b981; font-size: 0.75em;">
    ✅ {{ providerName }} 的 {{ primaryModelName }} 支持 Token 数据统计
  </span>
  <span v-else-if="tokenStatsSupport === false" 
        style="color: #ef4444; font-size: 0.75em;">
    ❌ {{ providerName }} 的 {{ primaryModelName }} 不支持 Token 数据统计
  </span>
  <span v-else 
        style="color: #999; font-size: 0.75em;">
    正在检测...
  </span>
</h3>
```

### 视觉效果

```
┌────────────────────────────────────────┐
│ 📊 Token 使用统计                      │
│ ✅ bailian 的 qwen-plus 支持 Token 数据统计│  ← 绿色
├────────────────────────────────────────┤
│ 今日总消耗 │ 日预算 │ 剩余 │ 使用率   │
│  12,345   │ 500K  │ 487K │  2.5%    │
└────────────────────────────────────────┘

或

┌────────────────────────────────────────┐
│ 📊 Token 使用统计                      │
│ ❌ bailian 的 qwen-turbo 不支持 Token 数据统计│  ← 红色
├────────────────────────────────────────┤
│ 今日总消耗 │ 日预算 │ 剩余 │ 使用率   │
│     0     │ 500K  │ 500K │  0.0%    │
└────────────────────────────────────────┘
```

---

## 🧪 测试场景

### 场景 1: 支持 Token 统计的模型

**API 返回**:
```json
{
  "models": {
    "models": [
      {
        "model": "qwen-plus",
        "count": 100,
        "tokens": 50000
      }
    ]
  }
}
```

**显示**: ✅ bailian 的 qwen-plus 支持 Token 数据统计

---

### 场景 2: 不支持 Token 统计的模型

**API 返回**:
```json
{
  "models": {
    "models": [
      {
        "model": "qwen-turbo",
        "count": 100,
        "tokens": null
      }
    ]
  }
}
```

**显示**: ❌ bailian 的 qwen-turbo 不支持 Token 数据统计

---

### 场景 3: 数据加载中

**API 返回**:
```json
{
  "models": {
    "models": []
  }
}
```

**显示**: 正在检测...

---

## 📊 常见服务商支持情况

| 服务商 | 模型 | Token 统计 | 说明 |
|--------|------|-----------|------|
| **阿里云百炼** | qwen-plus | ✅ 支持 | 返回完整 tokens 数据 |
| **阿里云百炼** | qwen-max | ✅ 支持 | 返回完整 tokens 数据 |
| **阿里云百炼** | qwen-turbo | ❌ 不支持 | 不返回 tokens 字段 |
| **OpenAI** | gpt-3.5-turbo | ✅ 支持 | 返回 usage 对象 |
| **OpenAI** | gpt-4 | ✅ 支持 | 返回 usage 对象 |
| **Anthropic** | claude-3 | ✅ 支持 | 返回 usage 对象 |

---

## 🔍 判断逻辑

```
1. 检查模型数据是否存在
   ↓ 不存在 → "正在检测..."
   
2. 检查第一个模型的 tokens 字段
   ↓ 有值且有效 → ✅ 支持
   
3. 检查请求数 count
   ↓ count > 0 但 tokens 为 0/null → ❌ 不支持
   
4. 其他情况
   → "正在检测..."
```

---

## 🎨 样式设计

### 字体大小

| 元素 | 大小 | 说明 |
|------|------|------|
| 主标题 | 1.05em | 📊 Token 使用统计 |
| 状态文字 | 0.75em | 支持/不支持说明 |

### 颜色方案

| 状态 | 颜色 | 十六进制 |
|------|------|---------|
| **支持** | 绿色 | #10b981 |
| **不支持** | 红色 | #ef4444 |
| **检测中** | 灰色 | #999 |

### 间距

| 元素 | 间距 | 说明 |
|------|------|------|
| 状态文字左边距 | 10px | 与主标题间隔 |
| 状态文字字重 | normal | 非粗体 |

---

## 🔄 更新记录

| 日期 | 版本 | 改动 |
|------|------|------|
| 2026-03-27 | v1.0.7 | 新增 Token 统计支持状态显示 |
| 2026-03-27 | v1.0.4 | Token 预算前端编辑 |

---

## 💡 使用价值

### 对用户

- ✅ **即时反馈**: 一眼看出当前模型是否支持 Token 统计
- ✅ **避免困惑**: 解释为什么 Token 数据为 0
- ✅ **引导升级**: 提示用户切换到支持 Token 统计的模型

### 对运维

- ✅ **故障诊断**: 快速判断是配置问题还是模型不支持
- ✅ **成本核算**: 支持 Token 统计的模型便于成本分析
- ✅ **优化建议**: 推动使用支持 Token 统计的模型

---

**维护**: dev-claw (CTO)
