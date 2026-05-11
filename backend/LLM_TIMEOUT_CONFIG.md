# LLM 超时配置总结

## 超时设置概览

项目中所有 LLM 调用都已添加超时保护，避免无限等待。

---

## 1. LLM 客户端基础配置

**文件：** `app/services/llm.py`

```python
ChatOpenAI(
    timeout=60,        # 60 秒基础超时
    max_retries=2,     # 失败时最多重试 2 次
)
```

**作用：** 所有通过 `get_llm()` 创建的 LLM 实例都会应用此配置。

---

## 2. 知识图谱提取 (Extraction Agent)

**文件：** `app/agents/extraction_agent.py`  
**函数：** `llm_extract()`

```python
response = await asyncio.wait_for(
    llm.ainvoke(EXTRACTION_PROMPT.format(text=text)),
    timeout=120.0  # 2 分钟超时
)
```

**超时时间：** 120 秒（2 分钟）  
**原因：** 需要处理长达 15000 字符的文本，提取实体、关系和超边，任务较重。

**错误处理：**
- 超时：返回 `{error: "LLM extraction timed out (120s limit)"}`
- 其他错误：返回 `{error: str(e)}`
- 不会中断整个流程，Source 状态会标记为 `parsed`

---

## 3. 测验生成 (Quiz Agent)

**文件：** `app/agents/quiz_agent.py` → `app/routers/tasks.py`  
**函数：** `_generate_quiz_background()`

```python
questions = await asyncio.wait_for(
    run_quiz_generation(...),
    timeout=90.0  # 90 秒超时
)
```

**超时时间：** 90 秒（1.5 分钟）  
**原因：** 生成 5 道单选题，需要基于知识内容出题。

**错误处理：**
- 超时：QuizAttempt 状态设为 `failed`，error = "生成超时，请稍后重试"
- 其他错误：QuizAttempt 状态设为 `failed`，error = 错误信息
- 前端可通过 `/api/tasks/{task_id}/quiz/status` 查询状态

---

## 4. 学习建议生成 (Suggestion Agent)

**文件：** `app/agents/suggestion_agent.py`  
**函数：** `generate_suggestions()`

```python
response = await asyncio.wait_for(
    llm.ainvoke([...]),
    timeout=30.0  # 30 秒超时
)
```

**超时时间：** 30 秒  
**原因：** 只需要根据节点掌握情况生成 3-5 条建议，任务较轻。

**错误处理：**
- 超时：返回空建议列表 `[]`
- 其他错误：返回空建议列表 `[]`
- 前端会显示 fallback 建议（基于规则的简单建议）

---

## 超时时间对比

| Agent | 超时时间 | 原因 |
|-------|---------|------|
| Extraction | 120 秒 | 处理长文本（15000 字符），提取复杂知识结构 |
| Quiz | 90 秒 | 生成 5 道高质量选择题 |
| Suggestion | 30 秒 | 生成 3-5 条简单建议 |
| LLM Client | 60 秒 | 基础超时设置 |

---

## 客户端调用建议

### 知识图谱提取
- 这是**后台异步任务**，用户上传后立即返回
- 用户可轮询 `/api/sources/{source_id}` 查看状态
- 状态流转：`uploaded` → `parsing` → `extracting` → `parsed`

### 测验生成
- 使用**异步模式**（HTTP 202）
- 流程：
  1. `POST /api/tasks/{task_id}/quiz/generate` → 返回 `{status: "generating"}`
  2. `GET /api/tasks/{task_id}/quiz/status` → 轮询直到 `{status: "ready"}`
  3. 提交答案

### 学习建议
- 使用**缓存 + 后台更新**策略
- `GET /api/learning/suggestions` 立即返回缓存建议
- 后台异步更新 LLM 建议（30 秒超时）

---

## 调优建议

如果经常超时，可以考虑：

1. **减少文本长度**
   - Extraction: 当前 15000 字符，可减少到 10000
   - Quiz: 当前 8000 字符，可减少到 5000

2. **增加超时时间**
   - 如果 LLM API 响应慢，可适当增加超时
   - 但要注意客户端体验

3. **优化 Prompt**
   - 简化指令，减少 LLM 推理时间
   - 使用更明确的 JSON Schema

4. **升级 LLM 模型**
   - 使用更快的模型（如 qwen-turbo vs qwen-plus）
   - 权衡速度和质量

---

## 监控和调试

查看所有 LLM 相关错误日志：

```bash
# 查看超时错误
grep "timed out" logs/app.log

# 查看提取错误
grep "LLM extraction failed" logs/app.log

# 查看测验生成错误
grep "Quiz generation" logs/app.log
```

---

## 更新记录

- **2026-04-20**: 为所有 Agent 添加 asyncio.wait_for 超时保护
- **2026-04-20**: LLM Client 添加 timeout=60, max_retries=2
