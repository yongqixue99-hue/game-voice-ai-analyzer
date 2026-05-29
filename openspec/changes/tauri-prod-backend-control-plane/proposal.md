# tauri-prod-backend-control-plane

## Why

`tauri-prod-backend-launch-design` 已确定最终目标方案为 sidecar + PyInstaller，但直接跳到打包会同时引入「Python 打包」「macOS 签名」「Tauri 进程管理」三类风险。本 change 先做最低风险的「控制面骨架」：在 Tauri/Rust 侧搭好后续要承载 sidecar 的接口（API Base URL 解析、运行时信息、后端状态查询、启停占位命令），但**不真正启停任何进程**，也不打包 Python，也不做生产构建。

这样后续 P2 接 PyInstaller 时只需替换 `start_backend` / `stop_backend` 的内部实现，不必改 IPC 形状，也不会冲击当前 dev 链路。

## What Changes

- 新增 OpenSpec change：`tauri-prod-backend-control-plane`。
- Rust 侧新增 5 个 Tauri commands：
  - `get_api_base_url` —— 解析 API Base URL 与来源（默认 / `LUNARIS_API_BASE_URL` / `LUNARIS_PORT`）。
  - `get_runtime_info` —— 返回 runtime / 版本 / 当前后端管理模式 / `LUNARIS_DATA_DIR` 覆盖值。
  - `get_backend_status` —— 当前阶段固定返回 `mode: "external_dev"`，附带说明文案。
  - `start_backend` / `stop_backend` —— **占位实现**，明确返回 `ok=false` 与开发期文案，确保不会误启停用户已有进程。
- Rust 侧引入最小依赖 `serde` derive 用于命令返回值序列化。
- 前端**不接线**（理由见 §Out of Scope），保持 `scripts/dev-all.sh` 与现有设置页行为不变。
- 文档：本 change 的 4 份 OpenSpec 文件 + `docs/hand_off_status.md` 同步。

## Capabilities

### New Capabilities

- `tauri-prod-backend-control-plane`：Tauri/Rust 侧后端控制面 IPC 骨架，含 API Base URL 解析、runtime 信息、后端状态查询、启停占位。

### Modified Capabilities

- 无。`tauri-shell-mvp` 的「Tauri WebView 加载 Web UI / 设置页显示运行环境与健康状态」未变。

## Relationship to `tauri-prod-backend-launch-design`

- Design change 给出最终目标（sidecar + PyInstaller）与 P1-P5 路线图。
- 本 change 是 P1 的最小落地：只搭 IPC 形状，不动进程管理实质。
- P2 将新建 `tauri-prod-backend-pyinstaller`，用真正的 sidecar spawn 替换占位实现；本 change 的命令签名（`get_api_base_url` 等）保持稳定，无需破坏性更改。

## Risks & Rollback

- 风险：新增 Tauri commands 与 `serde` 依赖会触发 Rust 增量编译；首次约 10 秒。无运行时风险。
- 回滚：`git revert` 本提交即可，前端未接线，不会留下调用方残骸。
- 不影响：`scripts/dev-all.sh`、现有 `/api/health`、设置页 UI、Web 浏览器入口、SQLite、音频存储、ASR provider 配置。

## Impact

- Code：仅 `frontend/src-tauri/src/main.rs` 与 `frontend/src-tauri/Cargo.toml`。
- Docs：本 change 4 份文件 + `docs/hand_off_status.md`。
- Backend / DB / 业务逻辑：**不变**。
- 前端：**不变**（接线留作后续 P1.5 增量小 change）。
