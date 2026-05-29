# tauri-prod-backend-control-plane 能力规格

## Goal

新增能力 `tauri-prod-backend-control-plane`：在 Tauri/Rust 侧提供后端控制面的稳定 IPC 形状（API Base URL 解析、运行时信息、后端状态、启停占位），为后续 sidecar 实现做接口约束。

## Requirements

1. 必须提供 5 个 Tauri commands，且签名遵循 design.md §IPC Contract。
2. `get_api_base_url` 必须返回 `{ url, source }`，`source` 取值范围：`"default" | "env:LUNARIS_API_BASE_URL" | "env:LUNARIS_PORT"`。
3. `get_backend_status` 在本阶段必须固定返回 `mode="external_dev"` 并带 `note` 文案。
4. `start_backend` / `stop_backend` 必须为占位实现，调用时 `ok` 必须为 `false`，并必须在文案中说明本阶段由开发者通过 `scripts/dev-all.sh` 或 uvicorn 管理后端。
5. `get_runtime_info` 必须返回 `runtime / tauri_version / app_version / backend_management_mode / data_dir_override`。
6. 必须不影响：现有前端代码、`npm run tauri dev`、`scripts/dev-all.sh`、`/api/health`、Web 浏览器入口。
7. 必须保持 capability 文件 `capabilities/default.json` 的现有权限范围；不得新增任何系统权限。
8. 后续 change 替换占位实现时，命令名与字段名必须保持兼容（仅 `mode` 与 `ok` 取值变化）。

## Out of Scope

- 前端接线、PyInstaller、Tauri sidecar、生产构建、签名公证。
