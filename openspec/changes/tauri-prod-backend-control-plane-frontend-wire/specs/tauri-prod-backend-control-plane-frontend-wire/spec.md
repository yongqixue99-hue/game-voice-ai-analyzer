# tauri-prod-backend-control-plane-frontend-wire 能力规格

## Goal

新增能力 `tauri-prod-backend-control-plane-frontend-wire`：在设置页消费 P1 的三个只读 Tauri commands，验证控制面 IPC 真实可用。

## Requirements

1. 必须在 Tauri 模式下调用 `get_api_base_url`、`get_runtime_info`、`get_backend_status` 三个命令并展示结果。
2. 必须不调用 `start_backend` / `stop_backend`，UI 不暴露启停按钮。
3. 必须在 Browser 模式下走 fallback 文案，不抛错、不发额外请求。
4. 必须保留现有「运行环境」「API Base URL」「FastAPI 状态」三行的渲染与行为。
5. 必须不引入新 npm 依赖，必须不新增源文件。
6. 必须不破坏 `scripts/dev-all.sh`、不修改后端、不修改 Rust。
7. 必须在 IPC 失败时让 UI 显示「查询中」或不渲染该行，不抛 React 错误。

## Out of Scope

PyInstaller、sidecar、签名公证、UI 重构、新增设置页面。
