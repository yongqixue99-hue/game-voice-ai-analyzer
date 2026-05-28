# tauri-shell-mvp

## Why

桌面端架构研究已经确定 Tauri 优先、Electron 兜底。下一步需要用最小 Tauri Shell 验证当前 Next.js Web UI 能否在 Tauri WebView 中打开，并能连接现有 FastAPI 本地后端。

本 change 不做完整桌面端产品，只验证“桌面壳 + 当前 Web UI + 本地后端健康状态”的最小闭环。

## What Changes

- 在当前前端项目中新增最小 Tauri 配置和 Rust shell。
- 新增 `npm run tauri dev` 运行入口。
- Tauri 开发模式加载当前 Next.js dev server：`http://localhost:3000`。
- FastAPI 新增或复用健康检查接口：`GET /api/health`。
- 前端设置页显示：
  - 运行环境：Browser / Tauri。
  - FastAPI 状态：已连接 / 未连接 / 检查中。
  - API Base URL。
- 前端 API Base URL 增加运行时配置读取策略，为后续 Tauri 注入做准备。
- 新增 Tauri Shell MVP 开发运行文档。
- 不自动启动 FastAPI，不打包 Python，不处理生产安装包。

## Capabilities

### New Capabilities

- `tauri-shell-mvp`: 提供最小 Tauri 桌面壳、后端健康检查展示、运行环境展示和开发运行说明。

### Modified Capabilities

- 无。本阶段不改变上传、录音、ASR、AI 总结、分段长录音、整场总结、导出、数据库或 provider 的业务要求。

## Impact

- Frontend：新增 Tauri 配置、开发脚本、运行环境检测、后端健康状态展示。
- Backend：新增 `GET /api/health`，保留 `/health` 兼容。
- Docs：新增 Tauri Shell MVP 开发运行文档。
- Tooling：新增 Tauri CLI dev dependency 和最小 Rust/Tauri 工程文件。
- Risks：本机需要安装 Rust 工具链才能运行 `npm run tauri dev`；Tauri WebView 中的 MediaRecorder、文件上传、音频播放需要用户手动实测。
