## Goal

为已上传录音接入阿里云百炼 / DashScope 的非实时语音识别能力，让用户可以在上传音频后生成真实转写时间轴，并继续复用已有的点击片段跳转播放和播放高亮体验。

## User Story

作为游戏开黑语音复盘用户，我希望上传一段真实游戏语音后，可以点击“真实转写（阿里云）”，系统自动调用 DashScope 识别音频并生成带时间戳的转写片段，这样我可以直接点击某句语音定位回听，而不再只依赖 mock 文本。

## Requirements

- 新增 `POST /api/recordings/{recording_id}/transcribe`。
- 后端根据 `recording_id` 查找录音元数据，并确认录音文件存在。
- 后端通过 `PUBLIC_BASE_URL` 构造公网可访问的音频 URL：`{PUBLIC_BASE_URL}/api/recordings/{recording_id}/audio`。
- `ASR_PROVIDER=aliyun` 时使用 `AliyunASRProvider` 调用 DashScope 非实时语音识别 API。
- `ASR_PROVIDER=mock` 时使用 mock provider，保留本地无云服务的开发路径。
- `DASHSCOPE_API_KEY` 必须从环境变量读取，不能写入代码、OpenSpec 或示例以外的文件。
- 如果 `DASHSCOPE_API_KEY` 未配置，接口返回清晰错误，不崩溃。
- 如果 `PUBLIC_BASE_URL` 是 `localhost`、`127.0.0.1` 或 `::1`，接口返回清晰错误，提示阿里云无法访问本地音频 URL，需要公网映射。
- 阿里云返回的 `begin_time` / `end_time` 按毫秒处理，保存前转换为秒。
- 识别成功后把结果保存为 `transcript_segments`，并设置 `source=aliyun`。
- 如果真实转写成功，可以替换同一录音下旧的 `mock` 和旧的 `aliyun` segments；失败时不能删除已有 segments。
- 前端新增“真实转写（阿里云）”按钮、loading 文案和错误展示。
- 时间轴继续复用现有点击跳转和播放高亮逻辑。

## API Design

### POST `/api/recordings/{recording_id}/transcribe`

请求体：无。

成功响应：

```json
[
  {
    "id": "segment-id",
    "recording_id": "recording-id",
    "speaker_label": "Speaker 1",
    "start_time": 0.0,
    "end_time": 3.2,
    "text": "真实识别文本",
    "source": "aliyun",
    "created_at": "2026-05-27T00:00:00+00:00"
  }
]
```

错误响应：

- `404`：录音不存在或音频文件不存在。
- `400`：缺少 `DASHSCOPE_API_KEY`、`PUBLIC_BASE_URL` 不是公网地址、识别结果没有可用句级时间戳。
- `502`：DashScope 提交、轮询、任务失败或结果下载失败。

## Data Model

`transcript_segments` 新增字段：

- `source: string`

取值：

- `mock`：本地 mock 转写。
- `aliyun`：阿里云 DashScope 真实转写。

原有字段保持不变：

- `id`
- `recording_id`
- `speaker_label`
- `start_time`
- `end_time`
- `text`
- `created_at`

## Environment Variables

- `ASR_PROVIDER=aliyun`：真实转写使用阿里云 provider。
- `ASR_PROVIDER=mock`：转写接口使用 mock provider。
- `DASHSCOPE_API_KEY`：DashScope API Key，必须从环境变量读取。
- `ALIYUN_ASR_MODEL=fun-asr`：DashScope 非实时录音文件识别模型。
- `ALIYUN_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1`：DashScope API 基础地址。
- `PUBLIC_BASE_URL=http://127.0.0.1:8000`：后端公网基础地址，用于构造阿里云可访问的音频 URL。

本地开发时，`PUBLIC_BASE_URL` 通常需要设置为 ngrok、localtunnel 或 Cloudflare Tunnel 提供的公网 HTTPS 地址。

## Acceptance Criteria

- 原有上传播放功能仍然可用。
- 原有 mock 转写功能仍然可用。
- 页面出现“真实转写（阿里云）”按钮。
- 未配置 `DASHSCOPE_API_KEY` 时，点击按钮返回清晰错误。
- `PUBLIC_BASE_URL` 为 localhost / 127.0.0.1 / ::1 时，系统提示阿里云无法访问本地音频 URL。
- 配置 `DASHSCOPE_API_KEY` 和可公网访问的 `PUBLIC_BASE_URL` 后，可以提交阿里云转写任务。
- 阿里云任务成功后，可以下载并解析 `transcription_url` 结果。
- 真实转写结果保存为 `transcript_segments`，且 `source=aliyun`。
- 刷新页面后真实转写仍然存在。
- 点击真实转写 segment 可以跳转音频。
- 播放时当前 segment 仍然高亮。
- 前端 build/lint 通过。
- 后端测试通过。
- `openspec/changes/real-asr-aliyun/tasks.md` 已更新。

## Out of Scope

- 不做 FunASR 本地部署。
- 不接 Whisper / WhisperX。
- 不接 pyannote。
- 不做说话人分离 UI。
- 不做 AI 总结。
- 不做高光片段。
- 不做实时录音。
- 不做实时字幕。
- 不做登录系统。
- 不做支付系统。
- 不引入 OSS 上传实现；公网 URL 无法满足时先在设计中说明，不直接扩大范围。
- 不做大规模 UI 重设计。

## Risks / Trade-offs

- DashScope 需要公网可访问的音频 URL；本地 `127.0.0.1` 不能被阿里云访问，因此本地真实联调需要公网隧道。
- 本次接口采用同步等待任务完成的方式，便于 MVP 闭环，但长音频会让 HTTP 请求等待较久；后续应改为后台任务和任务状态轮询。
- 真实转写会把音频 URL 暴露给第三方云服务；正式产品需要补充隐私说明、访问控制和临时 URL 策略。
- 未引入 OSS，最小实现依赖公网隧道的稳定性；后续生产化可考虑对象存储和签名 URL。
