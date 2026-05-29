# tauri-prod-backend-control-plane-frontend-wire

## Why

P1（`tauri-prod-backend-control-plane`）已在 Rust 侧落地 5 个 Tauri commands，但前端尚未消费。本 change 以最小增量把控制面接到设置页：让用户在 Tauri 模式下能直接看到「API Base URL 来源 / 后端管理模式 / Tauri runtime 信息」，验证整条 IPC 链路真实可用，为 P2 sidecar 实现奠定可观测性。

## What Changes

- 新增 OpenSpec change：`tauri-prod-backend-control-plane-frontend-wire`。
- 前端 `frontend/src/app/page.tsx` 最小增量：
  - `Window.__TAURI_INTERNALS__` 类型补全 `invoke` 函数签名。
  - 新增三类只读类型与 `invokeTauri()` helper（在非 Tauri 环境直接返回 null，不抛错）。
  - 新增三个 state：`tauriApiBaseUrlInfo` / `tauriRuntimeInfo` / `tauriBackendStatus`。
  - 在已有的运行环境检测 effect 内追加：当 `runtimeEnvironment === "Tauri"` 时调用三个 IPC 命令拉取信息。
  - 设置页新增 3 个 `SettingRow`：API Base URL 来源 / 后端管理模式 / Tauri Runtime 信息（仅 Tauri 模式下渲染 Runtime 信息行）。
- 不调用 `start_backend` / `stop_backend`，UI 不出现「启动 / 停止后端」按钮，只显示「占位，生产版待实现」徽标，避免误导。
- 不重构页面、不动现有状态机、Browser 模式行为完全不变。

## Capabilities

### New Capabilities

- `tauri-prod-backend-control-plane-frontend-wire`：设置页消费 Tauri 控制面 IPC 的最小展示。

### Modified Capabilities

- 无。`tauri-shell-mvp` 的设置页 FastAPI 状态显示与切换逻辑保持原状。

## Impact

- Code：仅 `frontend/src/app/page.tsx` 增量修改，无新文件、无新依赖。
- Backend / DB / 业务逻辑 / `scripts/dev-all.sh`：**不变**。
- 依赖：**不引入** `@tauri-apps/api` npm 包；通过 `window.__TAURI_INTERNALS__.invoke` 直接调用，避免新增依赖与 SSR 兼容问题。
- 风险：极低；非 Tauri 环境下三个 state 保持 null，UI 渲染走 fallback 文案。
- 回滚：`git revert` 本提交即可。
