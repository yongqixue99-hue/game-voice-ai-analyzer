# Design — FunASR Provider 稳定化与 Beta 交接

## Fake FunASR Server

新增 `scripts/fake_funasr_server.py`，使用 Python 标准库实现最小 HTTP 服务：

- `GET /health` 返回 `{status, service, version}`。
- `POST /recognize` 与 `POST /asr` 接收 multipart/form-data 音频。
- 响应稳定 JSON，包含 `text` 和 `segments`，时间戳使用毫秒，模拟真实 HTTP ASR 常见形态。

Fake server 只用于本地/CI 验证调用侧，不代表真实识别质量。

## FunASR Response Parser

`parse_funasr_response` 做宽容解析，覆盖以下结构：

1. `{ "text": "...", "segments": [{"start":0,"end":3000,"text":"..."}] }`
2. `{ "text": "...", "sentence_info": [{"start":0,"end":3000,"text":"..."}] }`
3. `{ "result": {"text":"...", "segments":[...]}}`
4. `[{"text":"...", "sentence_info":[...]}]`

解析策略：

- 片段数组优先于整段 `text`。
- `begin_time/end_time` 强制按毫秒解析。
- `start/end`、`start_time/end_time`、`ts/te` 默认按秒解析，但数值大于等于 1000 时按毫秒兜底。
- 无片段但有整段文本时，生成 `[0, recording.duration]` 单段，保证可落库与总结。

## Provider Status

`GET /api/asr/status` 保持向后兼容，同时新增更直观字段：

```json
{
  "provider": "mock|aliyun|funasr_http",
  "asr_provider": "mock|aliyun|funasr_http",
  "aliyun": {
    "configured": true,
    "api_key_configured": true,
    "public_base_url_configured": true,
    "public_url_is_local": true
  },
  "funasr_http": {
    "configured": true,
    "base_url": "http://127.0.0.1:10095",
    "reachable": false,
    "error": "Connection refused"
  }
}
```

FunASR 探测先访问 `/health`，失败后尝试 base URL；任何异常都返回状态字段，不抛到页面。

## Smoke Check

新增 `scripts/asr_provider_smoke_check.sh`，使用临时 `LUNARIS_DATA_DIR` 和临时端口启动后端，覆盖：

- `mock` 上传与转写。
- `funasr_http` 服务不可达错误。
- Fake FunASR server + `funasr_http` 转写 + mock AI 总结。
- `aliyun` 在 localhost `PUBLIC_BASE_URL` 下返回公网 URL 限制错误。

该脚本不触碰真实开发数据库和音频目录。

## Handoff

新增 `docs/funasr-http-provider-handoff.md`，说明：

- 当前已完成内容。
- Fake server 启动方式。
- `funasr_http` 环境变量配置。
- 明日 Win 3070 真实 FunASR HTTP 服务实测步骤。
- 如果真实响应字段不同，只改 `parse_funasr_response` 映射，不重构主链路。
