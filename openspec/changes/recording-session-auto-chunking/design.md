## Context

项目当前已经具备稳定主链路：

```text
上传/录音音频 -> 保存为 recording -> ASR 转写 -> 时间轴播放 -> AI 总结
```

阶段 D 的目标不是引入真正实时 ASR，而是把长录音拆成多个可独立处理的 chunk，形成“分段近实时分析”体验。Web 版仍只录制麦克风输入，不采集系统声音或游戏内语音。

## Goals / Non-Goals

**Goals:**

- 支持浏览器长录音会话。
- 支持 30 秒（开发测试）、1 分钟、3 分钟、5 分钟分段，默认 3 分钟。
- 每个 chunk 自动上传为现有 `recording`。
- 每个 chunk 自动执行现有 ASR 和 AI 总结。
- session/chunk 元数据持久化，刷新后可以看到历史 session 和 chunks。
- 某个 chunk 失败不影响后续 chunk 继续录制。
- 失败 chunk 可以手动重试分析。

**Non-Goals:**

- 不做真正实时流式 ASR。
- 不做 WebSocket。
- 不做后台 worker 或复杂任务队列。
- 不采集系统声音、游戏内语音或混音。
- 不做整场 session 总总结。
- 不大规模重构现有上传、ASR、总结主链路。

## Decisions

### 1. session/chunk 元数据入库

新增两张表：

`recording_sessions`

- `id`
- `title`
- `status`
- `chunk_duration_seconds`
- `started_at`
- `stopped_at`
- `created_at`
- `updated_at`

`recording_session_chunks`

- `id`
- `session_id`
- `recording_id`
- `chunk_index`
- `start_offset_seconds`
- `end_offset_seconds`
- `status`
- `error_message`
- `created_at`
- `updated_at`

选择原因：

- 用户刷新页面后仍能看到历史 session/chunk。
- chunk 可以关联现有 recording，继续复用播放、转写、AI 总结、编辑等能力。
- 不需要把长录音业务硬塞进 `recordings` 表。

备选方案：第一版只在前端维护 session。放弃原因是刷新后无法恢复历史，不满足验收标准。

### 2. chunk 上传复用现有保存逻辑

新增接口：

- `POST /api/recording-sessions`
- `GET /api/recording-sessions`
- `GET /api/recording-sessions/{session_id}`
- `PATCH /api/recording-sessions/{session_id}`
- `POST /api/recording-sessions/{session_id}/chunks`
- `PATCH /api/recording-sessions/{session_id}/chunks/{chunk_id}`

`POST /chunks` 接收 multipart：

- `file`
- `chunk_index`
- `start_offset_seconds`
- `end_offset_seconds`

后端内部调用现有 `create_recording_from_upload(file, db)` 保存音频并创建 recording，再创建 chunk 记录并关联 `recording_id`。

选择原因：

- 上传校验、存储路径、SQLite recording 记录全部复用。
- 不改变现有 `/api/recordings/upload` 语义。

备选方案：在现有 upload API 上增加 session 字段。放弃原因是会让普通上传接口承担 session 语义，影响边界清晰度。

### 3. 自动分析仍由前端编排

chunk 上传成功后，前端调用现有：

```text
POST /api/recordings/{recording_id}/transcribe
POST /api/recordings/{recording_id}/analyze
```

同时通过 chunk PATCH 接口更新 chunk 状态。

选择原因：

- 阶段 C 已经证明前端编排可以满足 MVP。
- 避免引入后台 worker。
- 失败状态可在前端即时展示，也可写回 chunk 表。

### 4. 分段方式

前端使用 `MediaRecorder` 的 `timeslice` 能力：

```text
recorder.start(chunkDurationMs)
```

每次 `dataavailable` 生成一个 chunk Blob，立即上传并启动该 chunk 的自动分析。停止长录音时，调用 `recorder.stop()` 触发最后一个不足分段时长的 Blob。

选择原因：

- 不需要频繁 stop/start recorder，降低丢音风险。
- 录音继续进行时，已产生 chunk 可以并发上传和分析。

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

- 麦克风权限被拒绝：session 显示 failed，不创建后续 chunk。
- 浏览器不支持 `MediaRecorder`：显示“当前浏览器不支持网页录音，请换用 Chrome / Edge。”
- chunk 上传失败：该 chunk 标记 failed，后续 chunk 继续录制。
- ASR 失败：该 chunk 标记 failed，不继续 AI 总结，用户可以手动重试。
- AI 总结失败：保留转写结果，该 chunk 标记 failed，用户可以手动重试总结/分析。
- 页面关闭前仍在录音：注册 `beforeunload` 提示用户确认。

## Risks / Trade-offs

- [Risk] 前端长任务编排在页面关闭后会中断。→ Mitigation：本阶段明确不做后台 worker；已上传 chunk 和状态会持久化，用户可以返回后手动重试。
- [Risk] 多个 chunk 并发 ASR/LLM 可能触发云服务速率限制。→ Mitigation：第一版按 chunk 产生顺序启动，失败明确展示并允许重试；后续可加队列。
- [Risk] `MediaRecorder.start(timeslice)` 的实际分片时间可能有轻微偏差。→ Mitigation：前端用 session elapsed 估算 offset，展示为近似时间范围。
- [Risk] 30 秒分段仅用于开发测试，真实使用容易产生过多云调用。→ Mitigation：UI 标注“开发测试”，默认仍为 3 分钟。

## Migration Plan

- 通过 SQLAlchemy `create_all` 创建新表。
- 对已有 SQLite 库无需修改旧表。
- 回滚时可停止使用新 API；旧 recordings、segments、analyses 不受影响。

## Open Questions

- 后续是否需要后台 worker 来处理页面关闭后的 chunk 分析。
- 后续是否需要 session-level summary，把所有 chunk 的结果汇总成整场总结。
