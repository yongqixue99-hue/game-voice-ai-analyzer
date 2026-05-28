## 1. OpenSpec

- [x] 1.1 创建 `auto-transcribe-and-summary` change。
- [x] 1.2 编写 `proposal.md`、`spec.md`、`design.md`、`tasks.md`。
- [x] 1.3 补充 capability spec 文件。

## 2. 自动分析状态

- [x] 2.1 新增自动分析开关状态。
- [x] 2.2 新增 `AutoAnalysisStatus` 类型和中文状态文案。
- [x] 2.3 新增 per-recording 自动分析状态和错误状态。
- [x] 2.4 防止同一 recording 重复触发自动分析。

## 3. 自动分析流程

- [x] 3.1 实现 `runAutoAnalysis(recordingId)`。
- [x] 3.2 自动流程调用现有 `transcribeRecording`。
- [x] 3.3 转写成功后更新 segments 和 speaker labels。
- [x] 3.4 自动流程调用现有 `analyzeRecording`。
- [x] 3.5 总结成功后更新 AI 总结。
- [x] 3.6 ASR 失败时停止流程并展示错误。
- [x] 3.7 AI 总结失败时保留 segments 并展示错误。

## 4. 上传与录音接入

- [x] 4.1 手动上传成功后，在自动分析开启时触发自动流程。
- [x] 4.2 浏览器录音上传成功后，在自动分析开启时触发自动流程。
- [x] 4.3 自动分析关闭时，上传和录音保持原手动流程。

## 5. 前端展示

- [x] 5.1 上传区域新增“自动分析”开关。
- [x] 5.2 浏览器录音区域说明复用同一个开关。
- [x] 5.3 录音卡片显示自动分析状态。
- [x] 5.4 录音卡片显示自动分析错误。
- [x] 5.5 保留手动“真实转写”和“生成 AI 总结”按钮。

## 6. 验证

- [x] 6.1 运行后端测试。
- [x] 6.2 运行前端 lint/build。
- [x] 6.3 浏览器验证自动分析开关和状态展示。
- [ ] 6.4 手动验收上传自动分析。
- [ ] 6.5 手动验收浏览器录音自动分析。
