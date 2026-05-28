## Why

当前浏览器录音只能在停止后整体上传，长时间录音会让用户等到最后才能看到转写和总结。为了走“分段近实时分析”路线，需要把长录音自动切成多个 chunk，每段独立上传、转写和总结，同时保留现有上传、ASR、AI 总结主链路。

## What Changes

- 新增“长录音会话”能力，用户可以开始/停止一场长录音。
- 支持选择 chunk 分段时长：开发测试 30 秒，以及 1 / 3 / 5 分钟，默认 3 分钟。
- 浏览器持续录制麦克风，到达分段时长后自动生成 chunk。
- 每个 chunk 上传为一条现有 `recording`，并关联到 session/chunk 元数据。
- 每个 chunk 上传成功后自动执行现有 ASR 转写和 AI 总结流程。
- 前端展示当前 session 总时长、当前 chunk 序号、chunk 列表、处理状态、错误和查看入口。
- 新增后端 session/chunk API 和 SQLite 持久化，刷新页面后可以查看历史 session/chunk。
- 不引入真正实时 ASR、WebSocket、后台 worker、系统声音采集或整场总结。

## Capabilities

### New Capabilities

- `recording-session-auto-chunking`: 长录音会话、自动切片上传、分段自动转写和分段 AI 总结。

### Modified Capabilities

- 无。

## Impact

- 后端新增 `recording_sessions` 和 `recording_session_chunks` 数据表。
- 后端新增 `/api/recording-sessions` 相关接口。
- 后端复用现有 `create_recording_from_upload`、`POST /api/recordings/{id}/transcribe`、`POST /api/recordings/{id}/analyze` 主链路。
- 前端新增长录音会话 UI、MediaRecorder 分段控制、chunk 状态列表和自动分析编排。
- 不新增第三方依赖，不改变现有上传、播放、ASR、AI 总结接口语义。
