# Proposal — FunASR Provider 稳定化与 Beta 交接

## Goal

完成 `funasr_http` Provider 的工程闭环：在不部署真实 FunASR、不改动现有 ASR 主链路的前提下，补齐 Fake FunASR 服务、响应解析兼容、Provider 状态、自动化 smoke check 和明日 Win 3070 实测交接文档。

## Background

当前项目已支持 `mock`、`aliyun`、`funasr_http` 三种 ASR Provider。`funasr_http` 的价值是让桌面端本地音频通过 multipart 直传到本机或局域网 FunASR 服务，绕开阿里云 ASR 需要公网音频 URL 的限制。

今晚无法部署真实 Win 3070 FunASR 服务，因此本 change 聚焦调用侧稳定化与可测试性，不伪造真实 FunASR 端到端成功。

## Requirements

- 保留 `mock` 和 `aliyun` Provider，不删除、不回退。
- `funasr_http` Provider 支持 Fake FunASR server 的稳定响应。
- `parse_funasr_response` 兼容多种常见响应结构。
- `/api/asr/status` 返回 provider 配置和 FunASR reachability，服务不可达时不崩溃。
- 设置页展示当前 Provider、阿里云公网 URL 限制、FunASR 地址和连接状态。
- 提供可重复运行的 ASR provider smoke check。
- 提供明日真实 Win 3070 FunASR HTTP 实测交接文档。

## Acceptance Criteria

- Fake FunASR server 提供 `/health` 和转写接口。
- `ASR_PROVIDER=mock` 可 smoke transcribe。
- `ASR_PROVIDER=funasr_http` 且服务不可达时返回清晰错误。
- 启动 Fake FunASR server 后，`funasr_http` 可以生成 `transcript_segments`。
- `ASR_PROVIDER=aliyun` 的本地公网 URL 限制错误清晰。
- 后端测试通过。
- 前端 lint/build 通过。
- 如不耗时过大，Tauri/Rust `cargo test` 通过或记录原因。
- OpenSpec tasks 更新为完成状态。

## Out of Scope

- 不部署真实 FunASR。
- 不把 FunASR 模型内置进 Tauri 或安装包。
- 不实现系统声音录制、混音、托盘、悬浮窗、OSS。
- 不重构现有上传、ASR、AI 总结主链路。
- 不删除阿里云 ASR 或 mock Provider。
