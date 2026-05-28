# session-level-summary

## Goal

基于一个长录音 session 下多个 chunks 的转写和分段 AI 总结，生成自然、通用的整场总结，并支持 Markdown/TXT 基础导出。

## User Story

作为一个录制了长时间音频的用户，我希望在 chunks 都处理后点击“生成整场总结”，系统能把所有分段内容按时间顺序汇总成一份完整摘要，并能复制或下载，方便复盘和分享。

## Requirements

1. 后端必须根据 `session_id` 查找 session 和 chunks。
2. 后端必须按 `chunk_index` 升序聚合上下文。
3. 后端必须读取每个 chunk 对应 recording 的 transcript segments。
4. 后端必须读取每个 chunk 对应 recording 的 AI summary，如存在。
5. 后端必须调用 LLM 生成结构化整场总结 JSON。
6. 后端必须保存整场总结到 SQLite。
7. 前端必须展示“生成整场总结”按钮。
8. 前端必须展示 loading、error、empty、success 状态。
9. 前端必须展示 title、summary、key_points、timeline、chunk_summaries、notes。
10. 前端必须支持复制 Markdown、下载 Markdown、下载 TXT。
11. chunk 内容更新后，已有 session summary 必须能标记为可能过期。

## API Design

### POST /api/recording-sessions/{session_id}/summary

生成整场总结。

响应：

```json
{
  "id": "summary-id",
  "session_id": "session-id",
  "provider": "mock",
  "model": "mock-session-summary-v1",
  "title": "整场录音标题",
  "summary": "对整场录音的自然总结",
  "key_points": [],
  "timeline": [],
  "chunk_summaries": [],
  "notes": [],
  "is_stale": false,
  "created_at": "ISO time",
  "updated_at": "ISO time"
}
```

### GET /api/recording-sessions/{session_id}/summary

获取已有整场总结。若不存在，返回 404。

### GET /api/recording-sessions/{session_id}/export.md

导出 Markdown。

### GET /api/recording-sessions/{session_id}/export.txt

导出纯文本。

## Data Model

新增 `recording_session_summaries`：

- `id`
- `session_id`
- `provider`
- `model`
- `summary_json`
- `raw_response_json`
- `is_stale`
- `created_at`
- `updated_at`

`summary_json` 存储完整结构化 JSON。

## Prompt Design

LLM 输出必须是严格 JSON：

```json
{
  "title": "整场录音标题",
  "summary": "对整场录音的自然总结",
  "key_points": ["重点 1"],
  "timeline": [
    {
      "start_time": 0,
      "end_time": 180,
      "title": "阶段标题",
      "summary": "这一阶段大致讲了什么"
    }
  ],
  "chunk_summaries": [
    {
      "chunk_index": 1,
      "start_time": 0,
      "end_time": 180,
      "summary": "该 chunk 的摘要"
    }
  ],
  "notes": ["需要确认的地方"]
}
```

Prompt 必须强调：

- 不要假设这是游戏语音。
- 不要强行输出搞笑、冲突、高光片段。
- 如果是会议，按会议总结；如果是闲聊，按闲聊总结。
- 只根据已有 transcript 和 chunk summary 分析，不要编造。
- 如果 chunk 缺少转写或总结，在 notes 中说明。
- 输出中文。

## Frontend Interaction

- 在长录音 session 卡片中新增“生成整场总结”按钮。
- 生成中显示“正在生成整场总结...”
- 无总结时显示空状态。
- 错误时展示后端返回的清晰错误。
- 成功后展示整场总结内容。
- timeline 条目可以点击跳转到对应 chunk/recording 的播放器。
- 提供“复制 Markdown”“下载 Markdown”“下载 TXT”按钮。
- 若 summary stale，显示“部分分段内容已更新，整场总结可能不是最新结果，请重新生成。”

## Export Format

Markdown：

```markdown
# 标题

## 整体总结

## 重点信息

## 时间线

## 分段摘要

## 备注

## 生成信息
- provider
- model
- generated_at
```

TXT 使用相同结构的纯文本版本。

## Acceptance Criteria

1. 原有上传、播放功能仍然可用。
2. 原有 ASR 转写功能仍然可用。
3. 原有 AI 总结功能仍然可用。
4. 原有浏览器单段录音功能仍然可用。
5. 原有分段长录音功能没有被破坏。
6. session 页面出现“生成整场总结”按钮。
7. 无 chunks 时会显示清晰错误。
8. 有多个 completed chunks 时，可以生成整场总结。
9. 整场总结保存到 SQLite。
10. 刷新页面后，整场总结仍然存在。
11. 前端能展示 title、summary、key_points、timeline、chunk_summaries、notes。
12. 可以复制 Markdown。
13. 可以下载 Markdown。
14. 可以下载 TXT。
15. chunk 内容更新后，session summary 可以提示可能过期。
16. 前端 build/lint 通过。
17. 后端测试通过。
18. OpenSpec tasks.md 已更新。

## Out of Scope

- 真正实时流式 ASR。
- WebSocket。
- 系统声音录制。
- 游戏内语音捕获。
- 桌面端。
- FunASR 本地部署。
- 说话人分离算法。
- 游戏专用复盘模板。
- 高光片段检测。
- 复杂 UI 重设计。
- 登录系统。
- 权限系统。
- 复杂后台队列。
- 大规模重构现有上传、ASR、总结主链路。

## Risks / Trade-offs

- 长 session 可能超过 LLM 上下文，本阶段不做分层总结。
- 部分 chunk 缺失转写/总结时，整场总结质量会下降。
- 导出内容依赖已保存 summary，如果 summary stale，需要用户重新生成。

## Task List

任务拆分见 `tasks.md`。
