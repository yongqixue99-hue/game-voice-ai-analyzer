# Tasks — multi-asr-provider-sprint

## 0. OpenSpec

- [x] 0.1 proposal / design / tasks 三文档。

## 1. 后端配置

- [x] 1.1 `config.py` 新增 `funasr_http_base_url`、`funasr_http_transcribe_path`、
      `funasr_http_timeout_seconds`；保留全部 aliyun 配置。

## 2. 后端 ASR provider

- [x] 2.1 新增 `FunasrHttpASRProvider`（stdlib urllib，multipart 直传本地文件）。
- [x] 2.2 FunASR 响应 → `ASRSegment`（宽容字段映射 + 无时间戳兜底单段）。
- [x] 2.3 `get_asr_provider` 支持 `funasr_http`。
- [x] 2.4 FunASR 不可用 → 503「FunASR 服务未连接…」清晰错误。
- [x] 2.5 aliyun 本地 URL 报错追加「或切换到 FunASR HTTP Provider」。

## 3. 状态端点

- [x] 3.1 新增 `app/asr_status.py` + `GET /api/asr/status`，挂到 `main.py`。

## 4. 前端（最小）

- [x] 4.1 设置页拉 `/api/asr/status`，只读展示 provider / aliyun / funasr 状态。

## 5. 测试

- [x] 5.1 mock 仍可用。
- [x] 5.2 aliyun 仍走现有逻辑。
- [x] 5.3 funasr_http 请求 `FUNASR_HTTP_BASE_URL`（monkeypatch urlopen）。
- [x] 5.4 FunASR 不可用 → 清晰 503。
- [x] 5.5 FunASR mock response → transcript_segments 落库。
- [x] 5.6 转写后 AI 总结不受影响。
- [x] 5.7 `/api/asr/status` 返回结构正确。

## 6. 文档与验收

- [x] 6.1 `docs/asr-providers.md`（三 provider 用法 + 公网 URL 限制 + FunASR 绕开原理 + 后续路线）。
- [x] 6.2 `backend/desktop-data-config.env.example` 增补 FunASR 配置。
- [x] 6.3 backend pytest 通过。
- [x] 6.4 前端 lint / build 通过。
- [x] 6.5 smoke 脚本仍通过（不破坏 Tauri real backend sidecar）。
- [x] 6.6 提交；输出报告。
