# tauri-prod-backend-control-plane

## Goal

在 Tauri/Rust 侧建立后端控制面 IPC 骨架与配置解析逻辑，作为后续 sidecar 实现的稳定接口；本阶段不启停任何进程，不打扰当前 dev 链路。

## Requirements

1. MUST 仅修改 `frontend/src-tauri/` 下的文件；MUST NOT 修改 `frontend/src/`、`backend/`、`scripts/`、`docs/` 之外的代码（`docs/hand_off_status.md` 仅做交接同步）。
2. MUST 提供 5 个 Tauri commands：`get_api_base_url`、`get_runtime_info`、`get_backend_status`、`start_backend`、`stop_backend`。
3. `get_api_base_url` MUST 解析优先级 `LUNARIS_API_BASE_URL` > `LUNARIS_PORT` > 默认 `http://127.0.0.1:8000`，并返回 `source` 标识。
4. `get_backend_status` MUST 在本阶段固定返回 `mode="external_dev"` 与说明文案。
5. `start_backend` / `stop_backend` MUST 是占位实现，MUST 返回 `ok=false` 且 MUST NOT 执行任何系统级 spawn/kill。
6. `get_runtime_info` MUST 暴露 `LUNARIS_DATA_DIR` 的存在与否（不解析、不验证、不写盘）。
7. MUST 不破坏 `npm run tauri dev`、`scripts/dev-all.sh`、当前设置页 UI、Web 浏览器入口。
8. MUST NOT 引入 PyInstaller、不做生产构建、不修改 `tauri.conf.json` 的 `bundle.active`。
9. MUST 编写 OpenSpec 4 份文档（proposal / design / spec / capability spec / tasks）。
10. MUST 在 `docs/hand_off_status.md` 同步当前阶段、新增 OpenSpec 路径、本阶段实现 / 未实现说明、下一步建议。

## Architecture

```text
frontend (unchanged)
src-tauri/Cargo.toml      + serde derive
src-tauri/src/main.rs     + 5 个 #[tauri::command] 函数
                          + invoke_handler 注册
```

## Out of Scope

- 前端接线（独立 P1.5 增量 change 处理）。
- 真正的 sidecar spawn / kill（P2）。
- PyInstaller、签名公证、生产打包（P2 / P3 / P4）。
- 业务代码、ASR provider、SQLite schema、音频存储、设置页布局重构。

## Acceptance

- 5 个 Tauri commands 已注册并可被 `invoke_handler` 识别。
- `npm run tauri dev` 编译通过、窗口可打开、Web UI 正常加载。
- 后端 `/api/health` 切换（启动/停止/重启）时设置页状态显示与本 change 之前一致。
- 无前端代码改动；无 backend 改动；无 dev-all 改动。
- 文档齐全且 hand_off_status 已同步。
