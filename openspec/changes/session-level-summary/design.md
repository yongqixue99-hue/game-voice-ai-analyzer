## Context

项目当前采用“分段近实时分析”路线：长录音 session 被切成多个 chunk，每个 chunk 保存为现有 `recording`，并复用已有 ASR 和 AI 总结能力。阶段 E 在此基础上生成整场总结，不改变现有上传、转写、分段总结主链路。

阶段 D 自检结论：

- 原有上传、播放、ASR、AI 总结代码路径未被 session/chunk API 替换。
- chunk 上传通过 `create_recording_from_upload` 复用现有 recording 保存逻辑。
- chunk 失败状态独立记录，不阻塞后续 chunk 继续录制。
- 已补一个必要小修：session 创建后若录音启动失败，将 session 标记为 `failed`，避免停留在 `recording`。
- 仍需用户手动确认：真实麦克风 30 秒分段、停止时最后 chunk、真实 ASR/LLM 云端调用链路。

## Goals / Non-Goals

**Goals:**

- 根据 session 下所有 chunks 的 transcript segments 和 chunk AI summary 生成整场总结。
- 使用通用自然总结，不套游戏复盘模板。
- 持久化 session summary。
- 支持读取已有 session summary。
- 支持 Markdown/TXT 导出。
- chunk summary 重新生成后，session summary 标记为 stale。
- 增加自动化测试覆盖无 chunks、缺少转写、多个 chunks 聚合、保存读取和导出。

**Non-Goals:**

- 不做真正实时流式 ASR。
- 不做后台 worker 或复杂队列。
- 不做整场总结长文本分批递归总结。
- 不做游戏专用模板、高光检测或冲突检测。
- 不做复杂 UI 重设计。
- 不做系统声音、游戏内语音或桌面端。

## Decisions

### 1. 使用独立 `recording_session_summaries` 表

新增表：

- `id`
- `session_id`
- `provider`
- `model`
- `summary_json`
- `raw_response_json`
- `is_stale`
- `created_at`
- `updated_at`

`summary_json` 保存完整结构化 JSON：

```json
{
  "title": "整场录音标题",
  "summary": "对整场录音的自然总结",
  "key_points": [],
  "timeline": [],
  "chunk_summaries": [],
  "notes": []
}
```

选择原因：

- 字段结构还在快速迭代，整体 JSON 比多列拆分更稳定。
- 导出 Markdown/TXT 可以直接从同一 JSON 渲染。
- 不影响已有 `recording_analyses` 表。

备选方案：为每个数组单独建 JSON 字段。暂不采用，因为当前没有按字段查询需求。

### 2. 扩展现有 LLM provider

在 `llm.py` 中让现有 provider 支持 session summary：

- `mock` provider 返回稳定 session summary。
- `dashscope/openai` provider 复用 chat completions 调用逻辑，使用新的 prompt 和 schema。

选择原因：

- 不新增 provider 体系。
- API key、model、错误处理继续沿用 `LLM_PROVIDER` 配置。

### 3. 后端聚合上下文

后端按 `chunk_index` 升序读取 chunks。每个 chunk 上下文包含：

- chunk 序号和时间范围。
- recording 元数据。
- transcript segments。
- chunk AI summary（如果有）。

如果 session 无 chunks，返回 400。

如果所有 chunks 都没有 transcript segments，返回 400。

如果只有部分 chunk 缺少 transcript 或 summary，允许生成整场总结，并把缺失情况写入 notes。

### 4. stale 策略

第一版实现简单策略：

- 重新生成某个 chunk 的 AI 总结后，将其所属 session summary 标记为 stale。
- 修改 chunk transcript segment 或 speaker label 后，也将所属 session summary 标记为 stale。

前端显示：

```text
部分分段内容已更新，整场总结可能不是最新结果，请重新生成。
```

### 5. 导出格式

Markdown 结构：

```markdown
# 标题

## 整体总结

## 重点信息

## 时间线

## 分段摘要

## 备注

## 生成信息
```

TXT 使用同样内容的纯文本变体。

## Risks / Trade-offs

- [Risk] session 很长时 prompt 可能超过模型上下文。→ Mitigation：本阶段不做长文本分块，后续再引入分层总结；当前先用于 MVP 和较短 session。
- [Risk] 部分 chunk 缺失转写/总结会降低总结质量。→ Mitigation：允许生成但在 notes 中说明；全部缺失转写时返回错误。
- [Risk] 页面关闭后前端自动分析中断。→ Mitigation：已上传 chunks 可恢复，用户可手动重试 chunk 分析和整场总结。
- [Risk] 导出内容可能过期。→ Mitigation：导出时使用已保存 summary，并在 UI 中显示 stale 提示。

## Migration Plan

- 使用 SQLAlchemy `create_all` 创建新表。
- 对已有 SQLite 不修改旧表。
- 回滚时可停止使用新 API；已有 recordings、chunks、segments、analyses 不受影响。

## Open Questions

- 后续是否需要长 session 分层总结来处理超长上下文。
- 后续是否需要导出包含完整 transcript。
