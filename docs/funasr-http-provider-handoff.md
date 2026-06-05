# FunASR HTTP Provider 交接说明

## 当前已完成

- `ASR_PROVIDER=funasr_http` 已接入后端 ASR Provider 工厂。
- FunASR HTTP Provider 通过 multipart/form-data 直传本地音频文件，不需要 `PUBLIC_BASE_URL` 公网回源。
- `parse_funasr_response` 已兼容 `segments`、`sentence_info`、`result` wrapper、list wrapper 和纯文本兜底。
- `/api/asr/status` 可显示当前 provider、阿里云配置、本地 URL 风险、FunASR base URL 和连接状态。
- 设置页可看到 ASR Provider 状态。
- Fake FunASR server 与 ASR provider smoke check 已加入。

## 启动 Fake FunASR Server

```bash
cd /Users/xueyongqi/project/project-2
scripts/fake_funasr_server.py --host 127.0.0.1 --port 10095
```

健康检查：

```bash
curl http://127.0.0.1:10095/health
```

## 配置 funasr_http

在仓库根 `.env`、`backend/.env` 或桌面数据目录 `config/.env` 中配置：

```env
ASR_PROVIDER=funasr_http
FUNASR_HTTP_BASE_URL=http://127.0.0.1:10095
FUNASR_HTTP_HEALTH_PATH=/health
FUNASR_HTTP_TRANSCRIBE_PATH=/v1/audio/transcriptions
FUNASR_HTTP_MODEL=sensevoice
FUNASR_HTTP_TIMEOUT_SECONDS=120
LLM_PROVIDER=mock
```

`ASR_PROVIDER=funasr` 也可用，会归一化为 `funasr_http`。

如果使用真实 LLM 总结，再把 `LLM_PROVIDER` 和对应 key 改为真实 provider。

## Win 3070 真实 FunASR 实测步骤

1. 在 Win 3070 机器启动真实 FunASR HTTP 服务。
2. 确认 HTTP 服务端口、健康检查路径和转写接口路径。
3. 在 Mac 上确认能访问 Win 局域网 IP，例如：
   ```bash
   curl http://<WIN_LAN_IP>:10095/health
   ```
4. 配置 Mac 后端：
   ```env
   ASR_PROVIDER=funasr_http
   FUNASR_HTTP_BASE_URL=http://<WIN_LAN_IP>:10095
   FUNASR_HTTP_HEALTH_PATH=/health
   FUNASR_HTTP_TRANSCRIBE_PATH=/v1/audio/transcriptions
   FUNASR_HTTP_MODEL=sensevoice
   FUNASR_HTTP_TIMEOUT_SECONDS=120
   ```
5. 启动后端和前端，上传一段音频。
6. 点击「真实转写」。
7. 检查返回的 `transcript_segments` 是否有合理的 `start_time/end_time/text/source=funasr_http`。
8. 点击「生成 AI 总结」，确认总结基于 FunASR 转写内容。

## 如果真实 FunASR 响应字段不同

优先只调整：

```text
backend/app/asr.py
parse_funasr_response(...)
```

不要重构上传、转写、segments 落库、AI 总结主链路。真实响应样例最好保存到临时本地文件或 issue 描述中，但不要提交包含敏感音频或隐私文本的数据。

## 2026-05-31 Win 3070 实测结果

- `GET http://192.168.1.5:10095/health` 返回 200，`device=cuda`，已加载 `sensevoice`。
- `GET /v1/models` 返回 200，包含 `fun-asr-nano`、`sensevoice`、`paraformer`。
- `POST /v1/audio/transcriptions` 使用 `file=<mp3>`、`model=sensevoice` 返回 200。
- 真实响应当前只有整段 `text`，没有句级时间戳；LUNARIS 会落成 1 个 `source=funasr_http`
  片段，时间范围使用上传时探测到的音频时长。
- 本地样例 MP3 经后端上传 + 转写成功，生成 1 个片段，时间范围 `0.0 -> 138.579563`。
- 本地样例 WebM 直连 Win 服务返回 500；在 Win 服务确认 WebM 解码前，实测优先使用 MP3/WAV/M4A。
- Tauri 桌面端已配置为自动拉起真实 sidecar，并通过桌面数据目录 `config/.env` 使用 Win FunASR。
- 桌面窗口上传 MP3 后，转写使用 Win FunASR，AI 总结使用 DashScope `qwen-plus`。

## 当前不做

- 不内置 FunASR 模型。
- 不打包 FunASR 到 Tauri。
- 不实现系统声音采集。
- 不实现麦克风 + 系统声音混录。
- 不引入 OSS。

普通用户后续仍可使用云 ASR；高级用户可自部署 FunASR HTTP 服务。
