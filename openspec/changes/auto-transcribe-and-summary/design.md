# auto-transcribe-and-summary 设计说明

## API 复用

第一版不新增后端 API。

原因：

- 现有 `POST /transcribe` 和 `POST /analyze` 已经稳定。
- 自动分析只是顺序编排，不需要改变后端数据模型。
- 避免过早引入任务表、后台 worker 或队列。

自动流程由前端函数 `runAutoAnalysis(recordingId)` 编排。

## 状态模型

前端新增：

```ts
type AutoAnalysisStatus =
  | "idle"
  | "uploading"
  | "uploaded"
  | "transcribing"
  | "transcribed"
  | "summarizing"
  | "completed"
  | "failed";
```

状态按 recording id 存储：

```ts
autoAnalysisByRecordingId: Record<string, {
  status: AutoAnalysisStatus;
  error: string;
}>
```

上传阶段还没有 recording id，因此上传中状态用全局 `uploadFlowStatus` 或上传表单/录音区域已有状态展示。上传成功拿到 recording id 后，进入 per-recording 自动分析状态。

## 前端流程

手动文件上传：

```text
uploadRecording -> loadRecordings -> if auto enabled runAutoAnalysis(recording.id)
```

浏览器录音：

```text
MediaRecorder stop -> uploadRecording -> loadRecordings -> if auto enabled runAutoAnalysis(recording.id)
```

自动分析：

```text
set uploaded
set transcribing
POST /transcribe
update segments
set transcribed
set summarizing
POST /analyze
update analysis
set completed
```

## 错误处理

ASR 失败：

- 设置 `failed`。
- 保存错误信息。
- 不调用 `analyze`。
- 手动“真实转写”按钮仍可用。

AI 总结失败：

- 已经成功的 segments 保留。
- 设置 `failed`。
- 保存错误信息。
- 手动“生成 AI 总结”按钮仍可用。

## UI

新增一个简单开关：

- 文案：“上传/录音完成后自动分析”
- 辅助文案：“开启后会自动执行真实转写和 AI 总结。”

录音卡片中显示当前自动分析状态：

- 上传完成
- 转写中
- 转写完成
- 总结中
- 完成
- 失败 + 错误原因

不做复杂任务面板。

