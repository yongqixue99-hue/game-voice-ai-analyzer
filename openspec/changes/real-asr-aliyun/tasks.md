## 1. OpenSpec

- [x] 1.1 创建 `real-asr-aliyun` change 目录。
- [x] 1.2 编写 `proposal.md`、`spec.md`、`design.md` 和 `tasks.md`。

## 2. 后端配置与数据模型

- [x] 2.1 添加 ASR 相关环境变量读取，不写死 API Key。
- [x] 2.2 为 `TranscriptSegment` 增加 `source` 字段，默认 `mock`。
- [x] 2.3 添加 SQLite 轻量迁移，确保旧库补齐 `source` 字段。

## 3. 后端 ASR Provider

- [x] 3.1 新增独立 ASR service 文件。
- [x] 3.2 实现 `MockASRProvider`。
- [x] 3.3 实现 `AliyunASRProvider` 的提交任务、轮询、结果下载和解析。
- [x] 3.4 对缺少 `DASHSCOPE_API_KEY`、本地 `PUBLIC_BASE_URL`、任务失败和结果无时间戳返回清晰错误。

## 4. 后端 API

- [x] 4.1 实现 `POST /api/recordings/{recording_id}/transcribe`。
- [x] 4.2 成功后保存 `source=aliyun` 或 `source=mock` 的 segments。
- [x] 4.3 保留现有 `/segments/mock` 功能。
- [x] 4.4 添加后端测试覆盖配置错误、本地 URL 错误、样例解析和成功保存。

## 5. 前端

- [x] 5.1 增加 `source` 类型字段。
- [x] 5.2 增加“真实转写（阿里云）”按钮。
- [x] 5.3 调用 `POST /api/recordings/{recording_id}/transcribe` 并展示 loading / error。
- [x] 5.4 成功后刷新该录音 segments。
- [x] 5.5 `source=aliyun` 时展示“来源：阿里云 ASR”。

## 6. 验证

- [x] 6.1 运行后端测试。
- [x] 6.2 运行前端 lint/build。
- [x] 6.3 用浏览器或 API 验证上传、mock、真实转写错误提示和时间轴交互。
