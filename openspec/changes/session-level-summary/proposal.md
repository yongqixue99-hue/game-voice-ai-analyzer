## Why

阶段 D 已经把长录音拆成多个 chunk 并分别转写、总结，但用户仍需要自己跨 chunk 阅读。阶段 E 需要在不改变现有上传、ASR、分段总结主链路的前提下，把一个 session 下的多个 chunk 汇总成整场级别总结，并提供基础 Markdown/TXT 导出。

## What Changes

- 先对 `recording-session-auto-chunking` 做代码自检和测试加固，只修必要 bug，不做大规模重构。
- 新增 session-level summary 能力：基于 session 下 chunks 的 transcript segments 和 chunk AI summary 生成整场总结。
- 新增 session summary SQLite 持久化。
- 新增整场总结 API：
  - `POST /api/recording-sessions/{session_id}/summary`
  - `GET /api/recording-sessions/{session_id}/summary`
  - `GET /api/recording-sessions/{session_id}/export.md`
  - `GET /api/recording-sessions/{session_id}/export.txt`
- 前端在“长录音会话”区域展示“生成整场总结”按钮、loading/error/success 状态、总结内容和导出按钮。
- 支持复制 Markdown、下载 `.md`、下载 `.txt`。
- chunk AI 总结重新生成后，已有 session summary 标记为可能过期。
- 不引入后台队列、WebSocket、实时流式 ASR、游戏专用模板或复杂 UI 重设计。

## Capabilities

### New Capabilities

- `session-level-summary`: 基于长录音 session 的 chunks 生成整场总结，并支持 Markdown/TXT 导出。

### Modified Capabilities

- 无。

## Impact

- 后端新增 `recording_session_summaries` 数据表。
- 后端扩展 LLM provider，支持 session summary prompt 和 JSON schema。
- 后端新增 session summary API 和导出接口。
- 后端测试覆盖无 chunks、缺少转写、多个 chunks 顺序聚合、保存读取和导出。
- 前端扩展现有长录音会话区域，新增整场总结展示和导出交互。
- 对阶段 D 做一次轻量 bug fix：session 创建后若录音启动失败，将 session 标记为 failed。
