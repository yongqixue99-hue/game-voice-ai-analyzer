# tauri-prod-backend-control-plane 设计

## Goal

在 Tauri/Rust 侧搭建后端控制面的 IPC 骨架与配置解析逻辑，为后续 sidecar 接管做准备，同时**绝不打扰当前开发链路**：不启动后端、不杀任何进程、不改前端、不改业务代码、不改数据库、不动 `scripts/dev-all.sh`。

## Background

`tauri-prod-backend-launch-design` 已选定方案 A（sidecar + PyInstaller）作为最终目标，并把实施拆为 P1-P5。本 change 是 P1，目标是把控制面接口先稳定下来，让 P2 的 PyInstaller 工作可以只替换实现，不动调用方。

## Non-Goals

- 不实现真正的 spawn / kill 后端进程逻辑。
- 不打包 Python，不引入 PyInstaller。
- 不做 `tauri build` 生产构建。
- 不接线前端（前端 IPC 调用留给后续小 change，避免本 change 触碰 `frontend/src/app/page.tsx` 大文件）。
- 不修改 `/api/health`、ASR、LLM、SQLite schema、音频存储路径。
- 不修改 `scripts/dev-all.sh`。

## Architecture

```text
frontend (unchanged)
    └─ 仍按现有方式 fetch http://127.0.0.1:8000/api/health
         （Tauri WebView 与 Browser 共用同一代码路径）

frontend/src-tauri (P1 改动点)
    ├─ Cargo.toml          + serde derive
    └─ src/main.rs         + 5 个 Tauri commands
        ├─ get_api_base_url()  ← 默认 http://127.0.0.1:8000；env LUNARIS_API_BASE_URL 覆盖；env LUNARIS_PORT 改端口
        ├─ get_runtime_info()  ← runtime / 版本 / backend_management_mode / data_dir_override
        ├─ get_backend_status()← 固定 mode="external_dev"，附说明
        ├─ start_backend()     ← 占位：返回 ok=false + 文案
        └─ stop_backend()      ← 占位：返回 ok=false + 文案
```

**关键约束**：所有命令都是只读 / 无副作用（含占位的两个）。该约束在 P2 替换为真实 spawn / kill 时才被打破，那时也会同步更新 capabilities 与权限说明。

## IPC Contract

### `get_api_base_url() -> { url: string, source: "default" | "env:LUNARIS_API_BASE_URL" | "env:LUNARIS_PORT" }`

解析优先级（高到低）：

1. `LUNARIS_API_BASE_URL`（完整 URL）。
2. `LUNARIS_PORT`（仅端口，host 固定 `127.0.0.1`，scheme `http`）。
3. 默认 `http://127.0.0.1:8000`。

返回 `source` 字段用于前端展示「来源」徽标。

### `get_runtime_info() -> { runtime, tauri_version, app_version, backend_management_mode, data_dir_override }`

- `runtime`: 固定 `"tauri"`（Rust 侧自识别）。
- `tauri_version` / `app_version`: 取自 `CARGO_PKG_VERSION`（v2 二进制版本即 app 版本，简化）。
- `backend_management_mode`: P1 固定 `"external_dev"`，未来值域包括 `"sidecar"`、`"external_prod"`。
- `data_dir_override`: `env::var("LUNARIS_DATA_DIR")` 的可空映射，供后续切换数据目录用。

### `get_backend_status() -> { mode, note, api_base_url }`

P1 固定 `mode="external_dev"`，`note` 描述 P1 的契约，`api_base_url` 复用 `resolve_api_base_url`。

### `start_backend() / stop_backend() -> { ok: false, mode: "external_dev", message }`

占位实现。`message` 文案明确说明：
- `start_backend`：当前由 `scripts/dev-all.sh` 或开发者手动启动后端，Tauri 不会自动拉起 FastAPI。
- `stop_backend`：Tauri 不会主动停止后端，避免误杀手动启动的 uvicorn。

后续 P2 替换实现时，IPC 形状保持兼容：仍是 `ok` / `mode` / `message` 三段，仅 `mode` 切到 `"sidecar"`，`ok` 在成功时为 `true`。

## Why Not Wire the Frontend Now

`frontend/src/app/page.tsx` 是单文件 5000+ 行的大组件，在此动手会显著扩大本 change 的 review 面，且容易触碰红线「不要重写设置页 / 不要大改前端状态管理」。本 change 因此只保留 Rust 侧骨架，等 P1.5 再以「最小增量」补：

- 在设置页新增 2 个只读行：API Base URL 来源、后端管理模式。
- 仅在 `runtimeEnvironment === "Tauri"` 时调用 `invoke("get_api_base_url")` / `invoke("get_runtime_info")`，Browser 模式继续走当前的 fallback。

这种「Rust 先稳定，前端再小步接线」的做法跟项目红线契合，且让 P1 commit 易回滚。

## Configuration Source Precedence

```text
Frontend window.__LUNARIS_CONFIG__.apiBaseUrl   (现有，最高优先级；未来由 Tauri 注入)
  > Tauri invoke get_api_base_url               (本 change 提供，前端 P1.5 接线)
  > NEXT_PUBLIC_API_BASE_URL                    (现有 fallback)
  > "http://127.0.0.1:8000"                     (硬编码默认)
```

本 change 不改变前端取值顺序，只增加 Rust 侧一个可被未来调用的入口。

## Compatibility

- Tauri dev 启动：不受影响。
- 开发期手动启动 uvicorn：不受影响。
- `scripts/dev-all.sh`：不受影响。
- 现有 `/api/health` 健康检查：不受影响（前端仍 fetch）。
- Web 浏览器模式：不受影响。
- 编译：首次因 `serde` 增量编译约数秒到十几秒；不影响已构建二进制。

## Risks

- 误启停风险：通过把 `start_backend` / `stop_backend` 明确做成占位（`ok=false`）规避；不会触发任何系统调用。
- IPC 暴露面：5 个命令均只读 / 无副作用，capabilities 默认允许 main window 访问即可，不需要扩展权限。
- 依赖膨胀：仅新增 `serde`（事实上已被 tauri 间接依赖，不增加首次冷编时间）。

## Verification Plan

1. `cargo check`（由 `npm run tauri dev` 触发）通过。
2. `scripts/dev-all.sh` 启动后：backend、frontend、Tauri 三者均启动；设置页运行环境=Tauri、API Base URL、FastAPI 状态切换均正常。
3. 用户在 Tauri 窗口里仍按现状操作；新增的 IPC 命令暂时不被前端调用，纯属「在二进制里可被发现」。

## Future Work

- P1.5（独立 change）：前端在设置页接线 `invoke("get_api_base_url")` / `invoke("get_runtime_info")`，新增「来源」与「后端管理模式」两行只读 UI。
- P2：`tauri-prod-backend-pyinstaller` 替换占位实现，真正 spawn sidecar。
- P3：macOS 签名 / 公证。
- P4：正式图标 / 用户文档。
