## Why

当前用户只能上传已经存在的本地音频文件。为了让 Web 版更容易使用，需要提供基础麦克风录音能力，让用户在浏览器内直接录音并复用已有上传、播放、ASR 和 AI 总结主链路。

本阶段只实现“整段录完后上传”的最小闭环，不引入分段上传、真正实时 ASR 或系统声音采集。

## What Changes

- 前端新增“浏览器录音”区域。
- 使用浏览器 `MediaRecorder` API 录制麦克风音频。
- 支持开始录音、暂停、继续、停止。
- 页面展示录音状态和录音时长。
- 停止后生成 `browser-recording-YYYYMMDD-HHmmss.webm` 文件。
- 录音文件复用现有 `POST /api/recordings/upload` 上传接口。
- 上传成功后刷新现有录音列表，新录音可继续使用播放器、ASR 转写、AI 总结和转写编辑功能。
- 后端只补充安全的 `webm/audio-webm` 上传格式支持，不新增录音 API。

## Capabilities

### New Capabilities

- `browser-recording-basic`: 浏览器麦克风录音、暂停/继续、停止后上传并创建 recording。

### Modified Capabilities

- `audio-upload-playback`: 上传接口支持 Web 录音生成的 `.webm` / `audio/webm` 文件。

## Impact

- Frontend:
  - `frontend/src/app/page.tsx` 增加 MediaRecorder 状态、计时、录音控制和上传逻辑。
- Backend:
  - `backend/app/config.py` 允许 `.webm`、`audio/webm`。
  - 上传接口继续复用，不新增后端 API。
- Tests:
  - 后端增加 `webm` 上传测试。
  - 前端通过 lint/build 验证。

