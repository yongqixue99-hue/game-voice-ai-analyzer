## Why

当前上传或浏览器录音完成后，用户还需要手动点击“真实转写”和“生成 AI 总结”。当用户只是想快速得到可浏览转写和总结时，这两个步骤会打断流程。

本 change 增加自动分析开关，让上传或录音完成后可自动执行 ASR 转写和 AI 总结，同时保留原有手动按钮作为重试和高级控制入口。

## What Changes

- 前端新增“自动分析”开关。
- 手动文件上传成功后，如果开关开启，自动执行 ASR 转写。
- 浏览器录音上传成功后，如果开关开启，复用同一自动分析流程。
- ASR 成功后自动执行 AI 总结。
- 自动流程显示状态：idle、uploading、uploaded、transcribing、transcribed、summarizing、completed、failed。
- ASR 失败时停止流程，不继续 AI 总结，并展示错误。
- AI 总结失败时保留已成功的转写结果，并展示错误。
- 保留“真实转写”和“生成 AI 总结”手动按钮。
- 不新增后端组合 API，第一版由前端顺序调用现有接口。

## Capabilities

### New Capabilities

- `auto-transcribe-and-summary`: 上传或录音完成后自动执行 ASR 转写和 AI 总结，并展示处理状态。

### Modified Capabilities

- `audio-upload-playback`: 上传成功后可触发可选自动分析流程。
- `browser-recording-basic`: 浏览器录音上传成功后可触发可选自动分析流程。
- `real-asr-aliyun`: 自动流程复用现有 `POST /transcribe`。
- `ai-summary-highlights`: 自动流程复用现有 `POST /analyze`。

## Impact

- Frontend:
  - `frontend/src/app/page.tsx` 增加自动分析开关、状态机、顺序调用逻辑和错误展示。
- Backend:
  - 不新增 API。
  - 不新增数据库字段。
  - 不改 ASR/LLM provider。
- Tests:
  - 复用现有后端测试。
  - 前端通过 lint/build 和浏览器页面检查验证。

