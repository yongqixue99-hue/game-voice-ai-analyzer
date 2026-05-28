## ADDED Requirements

### Requirement: 创建长录音会话
系统 SHALL 允许前端创建长录音会话，并持久化 session 元数据。

#### Scenario: 创建 session
- **WHEN** 前端调用 `POST /api/recording-sessions` 并提供 `chunk_duration_seconds`
- **THEN** 系统 SHALL 返回一个状态为 `recording` 的 session
- **AND** session SHALL 包含 `id`、`title`、`chunk_duration_seconds`、`started_at`、`created_at` 和 `updated_at`

#### Scenario: 拒绝非法分段时长
- **WHEN** 前端提交非允许值的 `chunk_duration_seconds`
- **THEN** 系统 SHALL 返回 400 错误

### Requirement: 上传并关联 session chunk
系统 SHALL 允许前端向指定 session 上传音频 chunk，并将 chunk 关联为一条现有 recording。

#### Scenario: 上传 chunk
- **WHEN** 前端调用 `POST /api/recording-sessions/{session_id}/chunks` 并上传音频文件、chunk 序号和时间范围
- **THEN** 系统 SHALL 保存音频为 recording
- **AND** 系统 SHALL 创建 `recording_session_chunks` 记录并关联 `recording_id`
- **AND** 响应 SHALL 包含 chunk 和 recording 信息

#### Scenario: session 不存在
- **WHEN** 前端向不存在的 session 上传 chunk
- **THEN** 系统 SHALL 返回 404 错误

### Requirement: 查询历史 session 和 chunks
系统 SHALL 允许前端查询历史 session 列表和 session 详情。

#### Scenario: 查询 session 列表
- **WHEN** 前端调用 `GET /api/recording-sessions`
- **THEN** 系统 SHALL 按创建时间倒序返回 session 列表

#### Scenario: 查询 session 详情
- **WHEN** 前端调用 `GET /api/recording-sessions/{session_id}`
- **THEN** 系统 SHALL 返回 session 详情
- **AND** 响应 SHALL 包含按 `chunk_index` 升序排列的 chunks

### Requirement: 更新 session 和 chunk 状态
系统 SHALL 允许前端更新 session 和 chunk 处理状态。

#### Scenario: 更新 session 为完成
- **WHEN** 前端停止长录音并调用 `PATCH /api/recording-sessions/{session_id}`
- **THEN** 系统 SHALL 更新 session 状态为 `completed`
- **AND** 系统 SHALL 保存 `stopped_at`

#### Scenario: 更新 chunk 状态
- **WHEN** 前端调用 `PATCH /api/recording-sessions/{session_id}/chunks/{chunk_id}`
- **THEN** 系统 SHALL 更新该 chunk 的 `status` 和 `error_message`

### Requirement: 前端长录音分段
前端 SHALL 使用浏览器 MediaRecorder 录制麦克风，并按用户选择的分段时长生成 chunk。

#### Scenario: 自动生成 chunk
- **WHEN** 用户开始长录音且录制时间达到分段时长
- **THEN** 前端 SHALL 生成一个 chunk Blob
- **AND** 前端 SHALL 立即上传该 chunk
- **AND** 录音 SHALL 继续进行

#### Scenario: 停止后上传最后 chunk
- **WHEN** 用户点击停止长录音
- **THEN** 前端 SHALL 停止 MediaRecorder
- **AND** 若当前缓冲中有音频，前端 SHALL 上传最后一个不足分段时长的 chunk

### Requirement: chunk 自动分析
每个 chunk 上传成功后，前端 SHALL 自动执行现有 ASR 转写和 AI 总结流程。

#### Scenario: chunk 自动分析成功
- **WHEN** chunk 上传成功并获得 `recording_id`
- **THEN** 前端 SHALL 调用 `POST /api/recordings/{recording_id}/transcribe`
- **AND** 转写成功后 SHALL 调用 `POST /api/recordings/{recording_id}/analyze`
- **AND** chunk 状态 SHALL 更新为 `completed`

#### Scenario: ASR 失败
- **WHEN** chunk ASR 转写失败
- **THEN** 前端 SHALL 将 chunk 状态更新为 `failed`
- **AND** 前端 SHALL 不继续调用 AI 总结

#### Scenario: AI 总结失败
- **WHEN** chunk AI 总结失败
- **THEN** 前端 SHALL 保留已生成转写
- **AND** 前端 SHALL 将 chunk 状态更新为 `failed`

### Requirement: chunk 状态展示和重试
前端 SHALL 展示 session chunk 列表、每个 chunk 的处理状态和错误，并允许失败 chunk 手动重试分析。

#### Scenario: 展示 chunk 状态
- **WHEN** session 下存在 chunks
- **THEN** 前端 SHALL 展示 chunk 序号、时间范围、状态、错误、播放器、转写和 AI 总结区域

#### Scenario: 重试失败 chunk
- **WHEN** 用户点击失败 chunk 的重试分析按钮
- **THEN** 前端 SHALL 使用该 chunk 的 `recording_id` 重新调用 ASR 和 AI 总结流程
