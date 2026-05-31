# ASR Providers（语音识别供给方）

LUNARIS 的语音识别（ASR）支持三种 provider，由后端环境变量 `ASR_PROVIDER` 选择。
三者输出统一的 `transcript_segments`（说话人 / 起止时间 / 文本 / source），复用同一套
时间轴、点击跳转、转写编辑、AI 总结链路。

| provider | 适合场景 | 是否需公网音频 URL |
|---|---|---|
| `mock` | 开发 / 测试，无需任何外部服务 | 否 |
| `aliyun` | 云端 ASR；音频已有公网 URL（或未来 OSS 签名 URL） | **是** |
| `funasr_http` | 本地 / 局域网 / 桌面端本地音频 | 否（直传文件） |

切换 provider：在后端 `.env`（或桌面数据目录 `config/.env`）设置 `ASR_PROVIDER=...` 后重启后端。
设置页「ASR Provider 状态」会实时显示当前 provider、阿里云 key 状态、FunASR 地址与连接状态。

---

## 1. `ASR_PROVIDER=aliyun`

阿里云 DashScope 非实时 ASR。**保留不变**，适合云端 / 已有公网 URL 的场景。

```env
ASR_PROVIDER=aliyun
DASHSCOPE_API_KEY=sk-xxxxxxxx
ALIYUN_ASR_MODEL=fun-asr
PUBLIC_BASE_URL=https://your-public-host.example.com   # 必须公网可下载
```

工作方式：后端把录音的音频 URL（`PUBLIC_BASE_URL` + `/api/recordings/{id}/audio`）交给阿里云，
**阿里云主动去下载这个 URL**。因此该 URL 必须公网可达。

### 为什么桌面端本地音频对阿里云有公网 URL 限制

桌面端音频是本机文件，后端跑在 `127.0.0.1`。如果 `PUBLIC_BASE_URL` 指向 `127.0.0.1` /
`localhost`，阿里云云端**无法下载**，后端会返回清晰错误：

> 阿里云 ASR 无法访问本地音频文件。请配置 PUBLIC_BASE_URL / localtunnel / OSS 公网 URL，
> 或切换到 FunASR HTTP Provider（ASR_PROVIDER=funasr_http）。

开发期可用 localtunnel / ngrok / Cloudflare Tunnel 把后端临时暴露成公网地址。

---

## 2. `ASR_PROVIDER=funasr_http`

本地 / 局域网 FunASR HTTP 服务。**新增**，用来绕开上面的公网 URL 限制。

```env
ASR_PROVIDER=funasr_http
FUNASR_HTTP_BASE_URL=http://127.0.0.1:10095     # FunASR HTTP 服务地址
FUNASR_HTTP_TRANSCRIBE_PATH=/asr                # 转写接口路径（默认 /asr）
FUNASR_HTTP_TIMEOUT_SECONDS=120
```

### 为什么 FunASR HTTP 能绕开公网 URL 限制

与阿里云「给我 URL 我去下载」相反，FunASR HTTP provider 把**音频字节直接 multipart
上传**给 FunASR 服务。服务跑在本机 / 局域网，**不需要公网回源**，所以桌面端本地音频可直接转写。

### FunASR 服务可以跑在哪里

- 本机（CPU/GPU 均可，视模型而定）
- 局域网的 Win + 3070 笔记本
- 未来的 GPU 服务器

LUNARIS **只负责调用** `FUNASR_HTTP_BASE_URL`，**不负责部署 FunASR、不内置 FunASR 模型、
不把模型塞进安装包**。部署 FunASR HTTP 服务是使用方自己的事（高级用户）。

### 未连接时的错误

FunASR 服务没起来时，转写返回明确错误（HTTP 503）：

> FunASR 服务未连接，请先启动本地或局域网 FunASR HTTP 服务。（http://127.0.0.1:10095，<原因>）

### 响应格式（宽容解析）

provider 对 FunASR 响应做宽容解析，依次尝试 `segments` / `sentences` / `sentence_info` /
`result` / `results` 等常见结构；每段文本取 `text|value|sentence`，时间取 `start/end`
（秒；大数值按毫秒兜底）或 `begin_time/end_time`（毫秒），说话人取
`speaker|speaker_label|spk`。若只返回整段纯文本无时间戳，则生成一段
`[0, 录音时长]`，保证可落库、可总结。真实 FunASR 服务接入后如字段不同，可在
`backend/app/asr.py::parse_funasr_response` 微调映射。

当前已覆盖的响应形态：

```json
{ "text": "...", "segments": [{ "start": 0, "end": 3000, "text": "..." }] }
```

```json
{ "text": "...", "sentence_info": [{ "start": 0, "end": 3000, "text": "..." }] }
```

```json
{ "result": { "text": "...", "segments": [{ "start": 0, "end": 3000, "text": "..." }] } }
```

```json
[{ "text": "...", "sentence_info": [{ "start": 0, "end": 3000, "text": "..." }] }]
```

### Fake FunASR server（本地验证）

仓库提供一个最小 Fake server，用于验证 LUNARIS 调用侧链路，不代表真实识别质量：

```bash
scripts/fake_funasr_server.py --host 127.0.0.1 --port 10095
```

接口：

- `GET /health`
- `POST /recognize`
- `POST /asr`

配合后端：

```env
ASR_PROVIDER=funasr_http
FUNASR_HTTP_BASE_URL=http://127.0.0.1:10095
FUNASR_HTTP_TRANSCRIBE_PATH=/recognize
FUNASR_HTTP_TIMEOUT_SECONDS=120
```

快速 smoke check：

```bash
scripts/asr_provider_smoke_check.sh
```

---

## 3. `ASR_PROVIDER=mock`

开发 / 测试用，生成确定性的假转写，无需任何外部服务。

```env
ASR_PROVIDER=mock
```

---

## 4. 后续可选路线（本次不实现）

桌面端真实 ASR 端到端的三条路线，按推荐顺序：

1. **FunASR HTTP Provider（本次已支持调用侧）**：本地/局域网推理，隐私 + 离线，
   不依赖公网回源。下一步是接一个真实 FunASR HTTP 服务做端到端手测。
2. **OSS 临时签名 URL**：把音频上传对象存储，生成带签名的临时公网 URL 交给阿里云。
   适合走云 ASR + 多端同步的形态。本次不引入 OSS。
3. **支持文件直传的云 ASR Provider**：换用允许直接 POST 音频、无需公网 URL 的云服务。

阿里云 ASR 与 mock 都会**长期保留**：普通用户后续可用云 ASR，高级用户可自部署 FunASR。

---

## 配置位置速查

- Web / 源码 dev：仓库根 `.env` 或 `backend/.env`。
- 桌面端（frozen sidecar）：数据目录 `config/.env`
  （macOS：`~/Library/Application Support/com.lunaris.voice-analyzer/data/config/.env`）。
  模板见 `backend/desktop-data-config.env.example`。
