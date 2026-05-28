## 1. OpenSpec

- [x] 1.1 创建 `recording-session-auto-chunking` change。
- [x] 1.2 编写 `proposal.md`、`spec.md`、`design.md`。
- [x] 1.3 编写 capability spec 文件。
- [x] 1.4 实现完成后更新本任务清单。

## 2. 后端数据模型

- [x] 2.1 新增 `RecordingSession` 模型。
- [x] 2.2 新增 `RecordingSessionChunk` 模型。
- [x] 2.3 确保 SQLite 初始化时创建新表。
- [x] 2.4 编写 session/chunk 序列化函数。

## 3. 后端 API

- [x] 3.1 新增 `POST /api/recording-sessions`。
- [x] 3.2 新增 `GET /api/recording-sessions`。
- [x] 3.3 新增 `GET /api/recording-sessions/{session_id}`。
- [x] 3.4 新增 `PATCH /api/recording-sessions/{session_id}`。
- [x] 3.5 新增 `POST /api/recording-sessions/{session_id}/chunks` 并复用现有上传保存逻辑。
- [x] 3.6 新增 `PATCH /api/recording-sessions/{session_id}/chunks/{chunk_id}`。
- [x] 3.7 将 session router 注册到 FastAPI。

## 4. 后端测试

- [x] 4.1 测试创建 session。
- [x] 4.2 测试非法分段时长返回 400。
- [x] 4.3 测试 chunk 上传会创建 recording 并关联 session。
- [x] 4.4 测试 session 详情返回 chunks。
- [x] 4.5 测试更新 session/chunk 状态。

## 5. 前端类型与 API

- [x] 5.1 新增 session/chunk 类型定义。
- [x] 5.2 新增 session/chunk API helper。
- [x] 5.3 新增长录音状态、计时器、MediaRecorder refs。
- [x] 5.4 新增 beforeunload 录音中确认提示。

## 6. 前端长录音流程

- [x] 6.1 新增“长录音会话”区域。
- [x] 6.2 支持选择 30 秒、1 分钟、3 分钟、5 分钟分段时长。
- [x] 6.3 实现开始长录音并创建 session。
- [x] 6.4 使用 MediaRecorder timeslice 自动生成 chunk。
- [x] 6.5 每个 chunk 生成后立即上传。
- [x] 6.6 上传成功后自动执行 ASR 和 AI 总结。
- [x] 6.7 停止长录音后上传最后 chunk 并完成 session。
- [x] 6.8 chunk 失败时不影响后续录制。
- [x] 6.9 失败 chunk 支持手动重试分析。

## 7. 前端展示

- [x] 7.1 展示 session 总时长和当前 chunk 序号。
- [x] 7.2 展示当前 session chunk 列表和状态。
- [x] 7.3 chunk 展示播放器、转写时间轴和 AI 总结。
- [x] 7.4 加载并展示历史 session 和 chunks。
- [x] 7.5 保留原上传、单段录音、手动转写、手动 AI 总结能力。

## 8. 验证

- [x] 8.1 运行后端测试。
- [x] 8.2 运行前端 lint/build。
- [x] 8.3 浏览器验证长录音会话区域、分段选择和历史 session 展示。
- [ ] 8.4 手动验收 30 秒分段生成 chunk。
- [ ] 8.5 手动验收 chunk 上传后自动转写和总结。
- [ ] 8.6 手动验收停止后最后 chunk 上传。
