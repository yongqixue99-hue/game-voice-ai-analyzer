# real-asr-aliyun 规格

## Goal

实现一个真实转写接口，将已上传录音提交到阿里云 DashScope 非实时语音识别 API，并把返回的句级时间戳结果保存为本项目的可点击转写时间轴。

## User Story

用户上传音频后，在录音卡片点击“真实转写（阿里云）”。系统显示“正在提交阿里云转写任务，请稍候...”，后端提交并轮询 DashScope 任务。任务成功后，前端刷新并展示真实转写片段，用户可以点击任意片段跳转到对应音频时间，播放中当前片段继续高亮。

## Requirements

1. 后端新增 `POST /api/recordings/{recording_id}/transcribe`。
2. 后端必须校验录音记录存在。
3. 后端必须校验录音文件存在。
4. 后端使用 `PUBLIC_BASE_URL` 构造音频访问 URL。
5. `ASR_PROVIDER=aliyun` 时调用 `AliyunASRProvider`。
6. `ASR_PROVIDER=mock` 时调用 mock provider。
7. 阿里云 provider 逻辑必须放在独立 service 文件中。
8. 不允许在代码或文档中写死真实 API Key。
9. `DASHSCOPE_API_KEY` 未配置时返回清晰错误。
10. `PUBLIC_BASE_URL` 为本地地址时返回清晰错误。
11. 提交 DashScope 任务后必须读取 `task_id`。
12. 必须轮询 `/tasks/{task_id}` 直到成功、失败或超时。
13. 成功后必须下载 `output.results[].transcription_url`。
14. 必须解析 `result.transcripts[].sentences[]` 中的 `begin_time`、`end_time`、`text`。
15. `begin_time` / `end_time` 必须从毫秒转换为秒。
16. 多个 result、transcript 或 channel 的 sentences 先合并，再按开始时间保存和展示。
17. 如果没有句级时间戳，返回清晰错误，并把原始响应写入日志。
18. `transcript_segments` 新增 `source` 字段。
19. mock 片段写入 `source=mock`。
20. 阿里云片段写入 `source=aliyun`。
21. 真实转写成功后，才替换同一录音下旧的 `mock` / `aliyun` segments；失败时不删除已有 segments。
22. 前端新增“真实转写（阿里云）”按钮。
23. 前端展示阿里云转写 loading、成功和错误状态。
24. 真实转写成功后刷新该录音 segments。
25. 时间轴显示 `source=aliyun` 时，在标题旁展示“来源：阿里云 ASR”。

## API Design

### `POST /api/recordings/{recording_id}/transcribe`

请求体：无。

成功状态：`201 Created`。

返回：按 `start_time` 升序排列的 segment 数组。

错误：

- `404`：录音或音频文件不存在。
- `400`：配置错误或识别结果不可用。
- `502`：DashScope API 调用失败、任务失败、结果下载失败。

## Data Model

### `transcript_segments`

新增：

- `source`: `String(50)`, 非空，默认 `mock`。

字段含义：

- `source=mock` 表示由本地 mock 生成。
- `source=aliyun` 表示由阿里云 DashScope 真实转写生成。

迁移策略：

- SQLite 没有迁移工具时，在应用启动时检查 `transcript_segments` 表。
- 如果缺少 `source` 列，则添加 `source TEXT NOT NULL DEFAULT 'mock'`。
- 已存在的历史片段默认视为 `mock`。

## Environment Variables

```bash
ASR_PROVIDER=aliyun
DASHSCOPE_API_KEY=replace-with-your-key
ALIYUN_ASR_MODEL=fun-asr
ALIYUN_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
PUBLIC_BASE_URL=http://127.0.0.1:8000
```

说明：

- `.env` 可以放在项目根目录或 `backend/.env`。
- `.env` 不能提交。
- `DASHSCOPE_API_KEY` 必须由开发者在本机环境变量或 `.env` 中配置。
- 本地真实联调时，`PUBLIC_BASE_URL` 应改成公网隧道地址，例如 ngrok / localtunnel / Cloudflare Tunnel。

## Acceptance Criteria

1. 原有上传播放功能仍然可用。
2. 原有 mock 转写功能仍然可用。
3. 页面出现“真实转写（阿里云）”按钮。
4. 未配置 `DASHSCOPE_API_KEY` 时，点击按钮返回清晰错误。
5. `PUBLIC_BASE_URL` 为 localhost 时，系统能提示阿里云可能无法访问本地音频。
6. 配置 `DASHSCOPE_API_KEY` 和可公网访问的 `PUBLIC_BASE_URL` 后，可以提交阿里云转写任务。
7. 阿里云任务成功后，可以下载并解析 `transcription_url` 结果。
8. 真实转写结果保存为 `transcript_segments`。
9. 刷新页面后真实转写仍然存在。
10. 点击真实转写 segment 可以跳转音频。
11. 播放时当前 segment 仍然高亮。
12. 前端 build/lint 通过。
13. 后端测试通过。
14. OpenSpec tasks 已更新。

## Out of Scope

- FunASR 本地部署。
- Whisper / WhisperX。
- pyannote。
- 说话人分离 UI。
- AI 总结。
- 高光片段。
- 实时录音。
- 实时字幕。
- 登录系统。
- 支付系统。
- OSS 上传实现。
- 大规模 UI 重设计。

## Risks / Trade-offs

- 同步等待阿里云任务完成实现简单，但请求可能较长；后续需要拆为异步任务。
- 本地文件必须通过公网 URL 提供给阿里云访问；没有公网隧道时真实转写不能完成。
- 结果 JSON 结构可能随模型或参数变化，需要保留清晰错误和日志以便排查。
- 本次不做说话人分离，因此 `speaker_label` 只能来自返回字段或默认标签。
