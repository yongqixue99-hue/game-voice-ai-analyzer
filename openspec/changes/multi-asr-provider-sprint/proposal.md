# multi-asr-provider-sprint

## Why

桌面 Beta 当前最大限制：阿里云非实时 ASR 需要**公网可下载**的音频 URL，桌面端本地
`127.0.0.1` 文件云端访问不到，真实转写端到端不通。但我们不想放弃阿里云（云端/未来 OSS
场景仍合适）。

把 ASR 改造成**多 Provider**：`aliyun`（保留）、`funasr_http`（新增，本地/局域网，绕开公网
URL 限制）、`mock`（保留）。LUNARIS 只调用 FunASR HTTP 服务，不负责部署 FunASR、不内置模型。

## What Changes

- 后端 ASR Provider 工厂支持三种：`mock` / `aliyun` / `funasr_http`。
- 新增 `FunasrHttpASRProvider`：把当前录音的**本地文件**以 multipart 上传给
  `FUNASR_HTTP_BASE_URL`，结果转换成统一 `ASRSegment` → 复用现有时间轴/编辑/总结链路。
  用 stdlib `urllib`（与现有 aliyun provider 一致，不引入运行时新依赖）。
- 新增配置 `ASR_PROVIDER=mock|aliyun|funasr_http`、`FUNASR_HTTP_BASE_URL`
  （默认 `http://127.0.0.1:10095`）、`FUNASR_HTTP_*` 超时/路径。保留全部阿里云配置。
- FunASR 服务未连接时清晰报错；aliyun 本地 URL 报错增强，提示可切 funasr_http。
- 新增 `GET /api/asr/status`：当前 provider、aliyun 配置状态、funasr base url + 连接状态。
- 设置页最小展示该状态（不大改 UI）。
- 新增 `docs/asr-providers.md`。

## Capabilities

### New Capabilities

- `asr-funasr-http`：本地/局域网 FunASR HTTP provider，桌面端本地音频直传、无需公网回源。

### Modified Capabilities

- `asr-provider`：从单一(`mock`/`aliyun`)扩展为三 provider 工厂；统一 `ASRSegment` 输出契约不变，
  下游持久化/总结不受影响。

## Impact

- 后端：`app/asr.py`（新增 provider + 工厂）、`app/config.py`（新增 settings）、
  新增 `app/asr_status.py`（状态端点）、`app/main.py`（挂路由）、新增测试。
- 前端：`page.tsx` 设置页最小状态展示。
- 文档：`docs/asr-providers.md`、本 change 三文档、`desktop-data-config.env.example` 增补。
- 不做：系统声音录制/混录/托盘/悬浮窗、UI 大改、OSS 实现、FunASR 本地部署、
  把 FunASR 模型塞进安装包、删除 aliyun/mock、重构主链路。
