## 1. 阶段 D 自检与小修

- [x] 1.1 检查原上传、播放、ASR、AI 总结主链路是否被长录音代码替换或破坏。
- [x] 1.2 检查 session/chunk 模型和状态流转。
- [x] 1.3 检查 chunk 上传是否复用现有 recording 保存逻辑。
- [x] 1.4 检查失败 chunk 是否不会阻塞后续 chunk。
- [x] 1.5 修复 session 创建后录音启动失败时未回写 failed 状态的问题。
- [x] 1.6 记录仍需用户手动确认的真实麦克风分段和云端调用链路。

## 2. OpenSpec

- [x] 2.1 创建 `session-level-summary` change。
- [x] 2.2 编写 `proposal.md`、`spec.md`、`design.md`。
- [x] 2.3 编写 capability spec 文件。
- [x] 2.4 实现完成后更新本任务清单。

## 3. 后端数据模型与 LLM

- [x] 3.1 新增 `RecordingSessionSummary` 模型。
- [x] 3.2 扩展 LLM provider，支持 session summary。
- [x] 3.3 增加 session summary JSON 归一化和 prompt。

## 4. 后端 API

- [x] 4.1 新增 `POST /api/recording-sessions/{session_id}/summary`。
- [x] 4.2 新增 `GET /api/recording-sessions/{session_id}/summary`。
- [x] 4.3 新增 `GET /api/recording-sessions/{session_id}/export.md`。
- [x] 4.4 新增 `GET /api/recording-sessions/{session_id}/export.txt`。
- [x] 4.5 chunk 分段 AI 总结或转写修改后标记 session summary stale。
- [x] 4.6 将 session summary router 注册到 FastAPI。

## 5. 后端测试

- [x] 5.1 测试无 chunks 时生成整场总结返回清晰错误。
- [x] 5.2 测试 chunks 全部缺少 transcript 时返回清晰错误。
- [x] 5.3 测试多个 chunks 按 `chunk_index` 聚合并保存 mock session summary。
- [x] 5.4 测试读取已有 session summary。
- [x] 5.5 测试 Markdown/TXT 导出。
- [x] 5.6 测试 chunk AI 总结更新后 session summary 标记为 stale。

## 6. 前端类型与 API

- [x] 6.1 新增 session summary 类型定义。
- [x] 6.2 新增获取、生成、导出 session summary 的 API helper。
- [x] 6.3 加载历史 sessions 时同时加载已有 session summary。

## 7. 前端展示与交互

- [x] 7.1 在长录音 session 区域新增“生成整场总结”按钮。
- [x] 7.2 展示整场总结 loading、empty、error、success 状态。
- [x] 7.3 展示 title、summary、key_points、timeline、chunk_summaries、notes。
- [x] 7.4 实现点击 timeline 跳转到对应 chunk 播放器。
- [x] 7.5 实现复制 Markdown、下载 Markdown、下载 TXT。
- [x] 7.6 显示 stale 过期提示。

## 8. 验证

- [x] 8.1 运行后端测试。
- [x] 8.2 运行前端 lint/build。
- [x] 8.3 记录无法由自动化确认、需要用户明天手动测试的项目。
