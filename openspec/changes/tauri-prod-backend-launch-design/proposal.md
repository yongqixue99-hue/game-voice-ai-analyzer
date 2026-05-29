# tauri-prod-backend-launch-design

## Why

当前 Tauri Shell MVP 已通过本机验证，但仍依赖用户手动开三个终端（uvicorn / next dev / tauri dev），并依赖开发期工具链。一旦打包成桌面 App 分发，用户不会、也不应该手动启动 FastAPI。
同时，SQLite 数据库、用户音频、配置文件、ASR provider 密钥的存储位置在开发期是仓库内的相对路径，这在打包后会落到只读 App Bundle 内部，无法正常工作。

本 change **只做设计**，不写实现代码、不动业务逻辑、不动现有启动链路、不动数据库结构。目标是把生产版后端启动方案、数据/配置/密钥落盘策略、macOS 打包风险、退出与崩溃处理形成一份评审稿，作为后续实现 change（例如 `tauri-prod-backend-sidecar-impl`）的输入。

## What Changes

- 新增 OpenSpec change：`tauri-prod-backend-launch-design`。
- 对比 3 种生产后端启动方案：
  - A：Tauri sidecar + PyInstaller 打包 FastAPI 后端。
  - B：继续本地 HTTP 服务，开发/生产都由 Tauri command 管理后端进程。
  - C：取消本地 HTTP，迁移到 Tauri command / IPC。
- 给出推荐方案与理由。
- 给出数据 / 音频 / 配置 / 密钥 / 日志的落盘策略。
- 给出端口选择、端口冲突、健康检查、退出清理、崩溃恢复方案。
- 给出 macOS 打包、代码签名、公证的已知坑列表。
- 明确哪些是「本阶段不做」的事项。

## Capabilities

### New Capabilities

- `tauri-prod-backend-launch-design`：生产版后端启动方案设计、数据/配置存储策略、macOS 打包风险清单。

### Modified Capabilities

- 无。本阶段不改业务能力。

## Impact

- Docs：新增设计文档与 OpenSpec change。
- Code：**无代码改动**。
- DB / 业务逻辑 / 现有启动链路：**不变**。
- 后续实现 change（例如 sidecar 打包、生产 build、macOS 签名）以本设计为输入。
- Risks：设计阶段不引入运行风险；若后续按方案 A 实施，PyInstaller 与 macOS 签名/公证仍是主要不确定性。
