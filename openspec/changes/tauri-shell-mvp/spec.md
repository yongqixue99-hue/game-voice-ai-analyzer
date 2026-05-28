# tauri-shell-mvp

## Goal

实现最小 Tauri 桌面壳验证：Tauri 开发模式加载当前 Next.js Web UI，前端检测 FastAPI 本地服务状态，并在设置页显示运行环境、后端连接状态和 API Base URL。

## Background

当前项目已完成 Web MVP 主链路、桌面风格 Web UI 和 Tauri 优先的桌面端架构研究。本阶段只验证 Tauri Shell 的最小可行性，不实现完整桌面端能力。

## Requirements

1. 项目中必须新增最小 Tauri app 配置。
2. Tauri 必须复用当前 `frontend/`，不得复制新前端。
3. Tauri 开发模式必须加载 `http://localhost:3000`。
4. FastAPI 必须提供 `GET /api/health`。
5. 前端设置页必须显示运行环境 Browser / Tauri。
6. 前端设置页必须显示 FastAPI 状态。
7. 前端设置页必须显示 API Base URL。
8. 浏览器中的 Web UI 必须继续可用。
9. 不得重构上传、录音、ASR、LLM、session/chunk 或导出主链路。

## Architecture

```text
Tauri Shell
  -> loads http://localhost:3000

Next.js Web UI
  -> reused as-is
  -> calls FastAPI at runtime API Base URL
  -> displays runtime and backend health

FastAPI Backend
  -> manually started
  -> exposes /api/health
```

## Development Mode Behavior

开发模式使用三个终端：

1. 后端：`uvicorn app.main:app --reload`
2. 前端：`npm run dev`
3. Tauri：`npm run tauri dev`

Tauri 第一版只打开窗口，不启动后端、不管理 Python 子进程、不打包。

## Backend Health Check

接口：

```http
GET /api/health
```

响应：

```json
{
  "status": "ok",
  "service": "fastapi",
  "version": "0.1.0"
}
```

如果后端未启动，前端显示：

```text
后端未连接，请先启动 FastAPI 服务
```

## API Base URL Strategy

前端 API Base URL 优先级：

1. `window.__LUNARIS_CONFIG__?.apiBaseUrl`
2. `NEXT_PUBLIC_API_BASE_URL`
3. `http://127.0.0.1:8000`

本阶段可以只预留运行时读取能力，不要求 Tauri Rust 侧完成注入。

## Acceptance Criteria

1. `openspec/changes/tauri-shell-mvp` 文档已创建。
2. Tauri 相关文件已创建在当前前端项目中。
3. `frontend/package.json` 新增 `tauri` script。
4. 后端新增或复用 `/api/health`。
5. 设置页显示运行环境。
6. 设置页显示 FastAPI 状态。
7. 设置页显示 API Base URL。
8. 前端 lint/build 通过。
9. 后端测试通过。
10. 文档说明三终端开发启动方式。
11. 若本机缺少 Rust，必须记录无法运行 Tauri dev 的环境问题。

## Out of Scope

- 系统声音录制。
- 麦克风 + 系统声音混录。
- 托盘。
- 悬浮窗。
- 开机启动。
- Python sidecar。
- FastAPI 打包。
- 生产安装包。
- FunASR 本地部署。
- OSS。
- 数据库重构。
- ASR/LLM provider 重构。
- UI 重做。

## Risks / Trade-offs

- Tauri WebView 中的 MediaRecorder、文件上传和音频播放需要手动实测。
- 本机必须安装 Rust 工具链才能运行 `tauri dev`。
- 生产构建尚未解决 Next.js 静态导出问题。
- 第一版仍依赖用户手动启动 FastAPI 和 Next.js。

## Task List

见 `tasks.md`。
