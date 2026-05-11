# 异步测验生成接口使用说明

## 改动概述

已将 `/api/tasks/{task_id}/quiz/generate` 接口改造为**异步模式**，避免客户端长时间等待。

## 新的接口流程

### 1. 触发生成 (POST)
```
POST /api/tasks/{task_id}/quiz/generate
```

**响应 (立即返回，HTTP 202):**
```json
{
  "attempt_id": 123,
  "status": "generating",
  "message": "测验题目正在生成中，请查询状态接口获取结果"
}
```

### 2. 查询状态 (GET)
```
GET /api/tasks/{task_id}/quiz/status
```

**响应示例 - 生成中:**
```json
{
  "id": 123,
  "task_id": 1,
  "stage_at_attempt": 0,
  "status": "generating",
  "questions": null,
  "error": null,
  "created_at": "2026-04-20T10:00:00"
}
```

**响应示例 - 生成完成:**
```json
{
  "id": 123,
  "task_id": 1,
  "stage_at_attempt": 0,
  "status": "ready",
  "questions": [
    {
      "index": 0,
      "question": "题目内容",
      "options": ["A", "B", "C", "D"]
    },
    ...
  ],
  "error": null,
  "created_at": "2026-04-20T10:00:00"
}
```

**响应示例 - 生成失败:**
```json
{
  "id": 123,
  "task_id": 1,
  "stage_at_attempt": 0,
  "status": "failed",
  "questions": null,
  "error": "生成超时，请稍后重试",
  "created_at": "2026-04-20T10:00:00"
}
```

### 3. 提交答案 (POST)
```
POST /api/tasks/{task_id}/quiz/submit
```

只有当 `status = "ready"` 时才能提交答案。

## 状态说明

- `generating`: 正在生成中
- `ready`: 生成完成，可以答题
- `failed`: 生成失败，查看 error 字段了解原因

## 数据库迁移

如果数据库已存在，运行迁移脚本：
```bash
psql -U postgres -d hexamind -f migrate_quiz_attempts.sql
```

或者直接运行 SQL 文件中的语句。

## 超时设置

- LLM API 超时: 60秒
- 重试次数: 2次
- 总超时时间: 90秒

## 客户端使用示例

```javascript
// 1. 触发生成
const response = await fetch('/api/tasks/1/quiz/generate', {
  method: 'POST'
});
const { attempt_id, status } = await response.json();

// 2. 轮询状态
let quizQuestions = null;
while (!quizQuestions) {
  await new Promise(resolve => setTimeout(resolve, 2000)); // 等待2秒
  
  const statusResp = await fetch('/api/tasks/1/quiz/status');
  const statusData = await statusResp.json();
  
  if (statusData.status === 'ready') {
    quizQuestions = statusData.questions;
  } else if (statusData.status === 'failed') {
    console.error('生成失败:', statusData.error);
    break;
  }
}

// 3. 显示题目并收集答案
// ... 用户答题 ...

// 4. 提交答案
await fetch('/api/tasks/1/quiz/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ answers: [0, 1, 2, 3, 0] })
});
```
