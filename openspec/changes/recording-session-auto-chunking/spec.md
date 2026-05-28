# recording-session-auto-chunking

## Goal

实现长录音会话：浏览器持续录制麦克风音频，按固定时长自动切出 chunk；每个 chunk 自动上传、自动转写、自动生成 AI 总结，并在页面展示处理状态。

## User Story

作为一个需要复盘长时间语音的用户，我希望点击“开始长录音”后不用反复手动停止和上传，系统可以每隔几分钟自动切片并分析，这样我能边录边看到分段转写和总结；停止录音后，最后一段不足时长的内容也能被保存和分析。

## Requirements

1. 前端必须提供“长录音会话”区域。
2. 用户必须可以选择分段时长：30 秒（开发测试）、1 分钟、3 分钟、5 分钟，默认 3 分钟。
3. 用户点击“开始长录音”后，浏览器必须请求麦克风权限并开始录制。
4. 录音期间页面必须显示 session 总时长和当前 chunk 序号。
5. 到达分段时长后，系统必须自动生成 chunk Blob。
6. 每个 chunk 必须上传为一条现有 recording。
7. 每个 chunk 上传成功后必须自动执行 ASR 转写和 AI 总结。
8. 录制过程中 chunk 上传和分析不能阻塞下一段录音。
9. 用户停止长录音后，最后一个不足分段时长的 chunk 必须上传并分析。
10. 页面必须展示当前 session chunk 列表。
11. 每个 chunk 必须展示 chunk 序号、时间范围、处理状态、错误信息、播放入口、转写和 AI 总结入口。
12. session 和 chunk 元数据必须持久化，刷新页面后可以查看历史。
13. 某个 chunk 失败时，不得影响后续 chunk 继续录制。
14. 失败 chunk 必须允许用户手动重试分析。
15. 正在录制时用户关闭页面，浏览器必须提示确认。

## Frontend Interaction

- 新增“长录音会话”区块。
- 状态展示：
  - 未开始
  - 录音中
  - 停止中
  - 已完成
  - 失败
- 分段时长控件使用下拉选择或按钮组。
- 开始后禁用分段时长选择。
- 每生成一个 chunk，立即出现在 chunk 列表中。
- chunk 列表中展示：
  - `Chunk 1`
  - `00:00 - 03:00`
  - 当前状态：录制中 / 上传中 / 已上传 / 转写中 / 转写完成 / 总结中 / 完成 / 失败
  - 错误信息
  - 播放器
  - 转写时间轴
  - AI 总结
  - 重试分析按钮

## API Design

新增 API：

### POST /api/recording-sessions

创建 session。

请求：

```json
{
  "title": "长录音 2026-05-27 21:00",
  "chunk_duration_seconds": 180
}
```

响应：session 对象。

### GET /api/recording-sessions

返回 session 列表，按创建时间倒序。

### GET /api/recording-sessions/{session_id}

返回 session 详情和 chunks。

### PATCH /api/recording-sessions/{session_id}

更新 session 状态。

请求：

```json
{
  "status": "completed",
  "stopped_at": "2026-05-27T21:30:00Z"
}
```

### POST /api/recording-sessions/{session_id}/chunks

上传 chunk 并关联 session。

multipart 字段：

- `file`
- `chunk_index`
- `start_offset_seconds`
- `end_offset_seconds`

响应：chunk 对象，包含关联 recording。

### PATCH /api/recording-sessions/{session_id}/chunks/{chunk_id}

更新 chunk 状态或错误。

请求：

```json
{
  "status": "transcribing",
  "error_message": null
}
```

## Data Model

新增 `recording_sessions`：

- `id`
- `title`
- `status`
- `chunk_duration_seconds`
- `started_at`
- `stopped_at nullable`
- `created_at`
- `updated_at`

新增 `recording_session_chunks`：

- `id`
- `session_id`
- `recording_id nullable`
- `chunk_index`
- `start_offset_seconds`
- `end_offset_seconds`
- `status`
- `error_message nullable`
- `created_at`
- `updated_at`

chunk 的 `recording_id` 指向已有 `recordings.id`，因此播放、转写、总结、编辑能力继续复用现有 recording 主链路。

## State Machine

session:

```text
idle -> recording -> stopping -> completed
idle -> recording -> failed
```

chunk:

```text
recording -> uploading -> uploaded -> transcribing -> transcribed -> summarizing -> completed
recording -> uploading -> failed
uploaded -> transcribing -> failed
transcribed -> summarizing -> failed
```

## Error Handling

- 未授权麦克风：显示“无法访问麦克风，请检查浏览器权限。”
- 浏览器不支持录音：显示“当前浏览器不支持网页录音，请换用 Chrome / Edge。”
- 上传失败：chunk 标记 failed 并展示错误。
- ASR 失败：chunk 标记 failed，不继续总结。
- AI 总结失败：保留转写，chunk 标记 failed。
- 后续 chunk 不受前一个 chunk 失败影响。
- 正在录音关闭页面时提示确认。

## Acceptance Criteria

1. 原有上传音频功能仍然可用。
2. 原有浏览器单段录音功能仍然可用。
3. 原有自动 ASR + 自动总结功能仍然可用。
4. 页面出现“长录音会话”区域。
5. 用户可以选择分段时长。
6. 用户可以开始长录音。
7. 页面显示录音总时长。
8. 到达分段时间后，会自动生成并上传第一个 chunk。
9. 第一个 chunk 上传后会自动转写和总结。
10. 录制过程中可以继续生成第二个、第三个 chunk。
11. chunk 处理状态在页面上可见。
12. 用户停止长录音后，最后一个不足分段时长的 chunk 也会上传。
13. 刷新页面后，可以看到历史 session 和 chunks。
14. chunk 可以播放。
15. chunk 可以查看转写。
16. chunk 可以查看 AI 总结。
17. 某个 chunk 失败时，不影响后续 chunk 继续录制。
18. 失败 chunk 可以手动重试分析。
19. 前端 build/lint 通过。
20. 后端测试通过。
21. OpenSpec tasks.md 已更新。

## Out of Scope

- 真正实时流式 ASR。
- WebSocket。
- 系统声音录制。
- 游戏内语音捕获。
- 麦克风 + 系统声音混录。
- 桌面端。
- FunASR 本地部署。
- 说话人分离算法。
- 整场 session 总总结。
- 导出 Markdown / TXT。
- 登录系统。
- 权限系统。
- 复杂 UI 重设计。
- 大规模重构现有上传、ASR、总结主链路。

## Risks / Trade-offs

- 依赖页面存活：页面关闭后正在执行的自动分析会中断，本阶段不做后台 worker。
- 云服务调用增加：短分段会增加 ASR/LLM 调用次数，30 秒仅用于开发测试。
- 时间范围为近似值：浏览器分片时间可能有轻微偏差。
- 长录音内存压力：MediaRecorder 按分片清理 Blob，避免把整段录音留在内存。

## Task List

任务拆分见 `tasks.md`。
