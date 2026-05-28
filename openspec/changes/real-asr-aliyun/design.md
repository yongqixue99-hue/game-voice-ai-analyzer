# real-asr-aliyun 设计说明

## Provider 边界

后端新增统一 ASR Provider 选择逻辑：

- `ASR_PROVIDER=mock`：使用本地 mock provider，生成固定片段并保存为 `source=mock`。
- `ASR_PROVIDER=aliyun`：使用 `AliyunASRProvider`，负责提交 DashScope 任务、轮询任务、下载结果并解析为统一 segment DTO。

Router 只负责：

- 校验录音和文件存在。
- 调用 provider。
- 在 provider 成功后替换并保存 segments。
- 把 segments 序列化返回。

阿里云 HTTP 调用、状态轮询和结果解析全部放在 service 文件中，避免云厂商逻辑散落到 router。

## DashScope 流程

1. 构造音频 URL：`{PUBLIC_BASE_URL}/api/recordings/{recording_id}/audio`。
2. `POST {ALIYUN_DASHSCOPE_BASE_URL}/services/audio/asr/transcription`。
3. Header：
   - `Authorization: Bearer $DASHSCOPE_API_KEY`
   - `Content-Type: application/json`
   - `X-DashScope-Async: enable`
4. Body：

```json
{
  "model": "fun-asr",
  "input": {
    "file_urls": ["<PUBLIC_AUDIO_URL>"]
  },
  "parameters": {
    "channel_id": [0],
    "language_hints": ["zh", "en"]
  }
}
```

5. 从响应中读取 `output.task_id`。
6. `GET {ALIYUN_DASHSCOPE_BASE_URL}/tasks/{task_id}` 轮询任务。
7. 任务成功后读取 `output.results[].transcription_url`。
8. 下载每个 `transcription_url` 指向的 JSON。
9. 合并 `transcripts[].sentences[]` 并转换为 `TranscriptSegment`。

## 结果替换策略

真实转写成功之前不删除任何已有 segments。

provider 成功返回统一 segment DTO 后，后端在同一事务中：

1. 删除该 recording 下 `source in ('mock', 'aliyun')` 的旧 segments。
2. 写入新的 `source=aliyun` segments。
3. commit 后返回最新 segments。

这样可以避免失败时清空时间轴，也可以避免重复点击真实转写产生重复片段。

## 本地公网 URL 策略

默认 `PUBLIC_BASE_URL=http://127.0.0.1:8000` 只能用于前端播放，不能用于阿里云抓取。真实转写前，后端会拒绝 `localhost`、`127.0.0.1`、`::1`，并提示使用公网隧道。

本 change 不引入 OSS。原因是 OSS 会带来账号、bucket、签名 URL、上传生命周期和权限配置，超出最小真实 ASR 闭环。后续生产化可以把本地文件上传到 OSS 后再把签名 URL 传给 DashScope。
