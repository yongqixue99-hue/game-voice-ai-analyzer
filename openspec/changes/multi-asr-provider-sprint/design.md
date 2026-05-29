# Design — multi-asr-provider-sprint

## 目标

ASR 支持 `mock` / `aliyun` / `funasr_http` 三 provider，统一输出 `ASRSegment`，复用现有
时间轴/点击跳转/转写编辑/AI 总结链路。最小改动，不破坏 aliyun / mock，不重构主链路。

## Provider 接口（已存在，沿用）

```python
class ASRProvider(Protocol):
    def transcribe(self, recording: Recording, public_audio_url: str) -> list[ASRSegment]: ...
```

- `ASRSegment(speaker_label, start_time, end_time, text, source)` 不变。
- `public_audio_url` 对 aliyun 必需；对 funasr_http 忽略（它直传本地文件），对 mock 忽略。

## FunASR HTTP Provider

`FunasrHttpASRProvider(settings)`：

1. 解析 `resolve_recording_path(recording)` 得到**本地文件路径**。
2. 以 `multipart/form-data` POST 文件到 `{FUNASR_HTTP_BASE_URL}{FUNASR_HTTP_TRANSCRIBE_PATH}`
   （默认路径 `/asr`，可配）。用 stdlib `urllib`（手写 multipart body），与现有 aliyun
   provider 的 `urllib` 风格一致，**不引入运行时新依赖**（httpx 仅 dev）。
3. 解析响应 JSON → `ASRSegment` 列表，`source="funasr_http"`。
4. 错误处理：
   - 连接失败（URLError/timeout）→ `ASRProviderError(503, "FunASR 服务未连接，请先启动本地或局域网 FunASR HTTP 服务。")`
   - HTTP 非 2xx → `ASRProviderError(502, ...)`
   - JSON 不可解析 / 无可用片段 → 清晰报错。

### FunASR 响应解析（宽容）

FunASR 部署形态多样，解析尽量宽容，按以下顺序找片段数组：
- 顶层 `segments` / `sentences` / `result`（list）/ `results`。
每个片段字段映射（多名兜底）：
- 文本：`text` | `value` | `sentence`
- 起止（秒或毫秒，>1000 视为毫秒）：`start`/`end` | `begin_time`/`end_time` | `start_time`/`end_time` | `ts`/`te`
- 说话人：`speaker` | `speaker_label` | `spk`(→`Speaker {spk}`)，缺省 `Speaker 1`
若只有整段纯文本无时间戳 → 生成单段 `[0, recording.duration]`（保证可落库、可总结）。

### 为什么 FunASR 绕开公网 URL 限制

aliyun 非实时 ASR 是「给我一个公网 URL，我去下载」——桌面端本地文件云端拿不到。
FunASR HTTP 是「我把音频字节直接 POST 给你」——服务在本机/局域网，不需要公网回源。

## 配置（config.py 新增，保留 aliyun）

| env | 默认 | 说明 |
|---|---|---|
| `ASR_PROVIDER` | `aliyun` | `mock`/`aliyun`/`funasr_http` |
| `FUNASR_HTTP_BASE_URL` | `http://127.0.0.1:10095` | FunASR HTTP 服务地址 |
| `FUNASR_HTTP_TRANSCRIBE_PATH` | `/asr` | 转写接口路径 |
| `FUNASR_HTTP_TIMEOUT_SECONDS` | `120` | 请求超时 |

阿里云配置全部保留：`DASHSCOPE_API_KEY`、`ALIYUN_ASR_MODEL`、`PUBLIC_BASE_URL` 等。

## aliyun 本地 URL 报错增强

`AliyunASRProvider._validate_settings` 本地 host 报错末尾追加：
「…或切换到 FunASR HTTP Provider（ASR_PROVIDER=funasr_http）。」

## 状态端点

`GET /api/asr/status`（新增 `app/asr_status.py`）：
```json
{
  "asr_provider": "funasr_http",
  "aliyun": {"api_key_configured": true, "model": "fun-asr", "public_base_url": "...", "public_url_is_local": true},
  "funasr_http": {"base_url": "http://127.0.0.1:10095", "reachable": false, "detail": "..."}
}
```
`reachable` 通过对 base_url 做一个短超时 GET 探测（失败即 false，不抛异常）。

## 前端（最小）

设置页「语音识别服务」行下方新增只读状态：当前 provider、aliyun key 是否配置、
funasr base url + 连接状态。拉 `/api/asr/status`，不改 UI 结构。

## 测试

- `ASR_PROVIDER=mock` 仍出 mock 片段。
- `ASR_PROVIDER=aliyun` 仍走现有逻辑（monkeypatch 网络层断言被调用 / 本地 URL 报错）。
- `ASR_PROVIDER=funasr_http`：monkeypatch `urlopen`，断言请求了 `FUNASR_HTTP_BASE_URL`。
- FunASR 不可用（urlopen 抛 URLError）→ 503 清晰错误。
- FunASR mock response → 正确转换为 `transcript_segments`（落库 + 时间戳）。
- 转写后 AI 总结流程不受影响（沿用现有总结测试路径）。

## 风险

- FunASR 响应格式未知 → 解析宽容 + 无时间戳兜底单段；真实服务接入后可能需微调字段映射。
- 大文件直传 multipart 内存占用：本次按整文件读入（与现有上传量级一致），不做分片流式。
- 无真实 FunASR 服务可测 → 用 mock HTTP response 覆盖；真实手测列为「需要时」。
