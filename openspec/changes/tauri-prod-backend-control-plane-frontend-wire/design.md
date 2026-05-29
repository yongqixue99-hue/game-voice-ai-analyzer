# tauri-prod-backend-control-plane-frontend-wire 设计

## Goal

把 P1 提供的 Rust 侧 5 个 Tauri commands 中的只读三个（`get_api_base_url` / `get_runtime_info` / `get_backend_status`）接到设置页，让用户能在 Tauri 模式下肉眼验证控制面工作；不引入新依赖，不重构 `page.tsx`，Browser 模式行为零变化。

## Non-Goals

- 不调用 `start_backend` / `stop_backend`（仍为占位，UI 不暴露按钮）。
- 不引入 `@tauri-apps/api` npm 包。
- 不重构设置页布局；不动其它页面；不动业务逻辑、ASR、SQLite。
- 不引入新的全局状态管理或 React Query 等库。

## Architecture

```text
page.tsx (单文件，最小增量)
  ├─ window.__TAURI_INTERNALS__.invoke (类型补全，运行时已存在)
  ├─ invokeTauri<T>(cmd) helper：非 Tauri / 失败 → 返回 null（吞错）
  ├─ 三个 useState：tauriApiBaseUrlInfo / tauriRuntimeInfo / tauriBackendStatus
  ├─ 现有 detectRuntimeEnvironment effect 内追加 if Tauri: invoke × 3
  └─ 设置页新增 3 个 SettingRow
```

## Why Direct `window.__TAURI_INTERNALS__` Instead of `@tauri-apps/api`

- 避免新增 npm 依赖、避免 SSR / 静态导出阶段触发包内 `if (typeof window === ...)` 之外的路径。
- Tauri v2 在窗口加载时已注入 `window.__TAURI_INTERNALS__.invoke`，签名稳定。
- helper 在 `invoke` 不存在或抛错时返回 null，让 UI 走 fallback 文案，不会破坏 Browser 模式。

## IPC Consumption Contract

| Command | 调用时机 | 失败兜底 |
| --- | --- | --- |
| `get_api_base_url` | 仅 Tauri 模式，进入设置页前已执行（在已有 useEffect 内追加） | state 保持 null，UI 显示「查询中」 |
| `get_runtime_info` | 同上 | state 保持 null，Runtime 信息行不渲染 |
| `get_backend_status` | 同上 | state 保持 null，UI 显示「查询中 / 占位，生产版待实现」 |

## UI Additions

设置页在「运行环境」行下追加三行：

1. **API Base URL 来源**
   - Tauri：StatusPill 显示中文标签（`默认值` / `环境变量 LUNARIS_API_BASE_URL` / `环境变量 LUNARIS_PORT`）；description 给出来源说明。
   - Browser：StatusPill 显示「Browser 默认」；description 说明 Browser 不通过 Tauri 解析。

2. **后端管理模式**
   - Tauri：StatusPill 显示 `tauriBackendStatus.mode`（当前固定 `external_dev`）；附「占位，生产版待实现」徽标；description 显示来自 Rust 的 `note` 文案。
   - Browser：StatusPill 显示 `manual-dev`；附同样的「占位」徽标。

3. **Tauri Runtime 信息**（仅 Tauri 模式渲染）
   - StatusPill: `runtime`、`v{app_version}`。
   - description: `runtime=… · app=… · tauri=…`，若 `LUNARIS_DATA_DIR` 存在则附加 `· LUNARIS_DATA_DIR=…`。

不动现有的：
- 「API Base URL」（已显示具体 URL）
- 「FastAPI 状态」+「重新检查」按钮
- 「隐私与桌面端能力」行

## Browser Compatibility

- `detectRuntimeEnvironment()` 已能识别 Browser；`invokeTauri` 在 Browser 中遇到 `invoke === undefined` 立刻返回 null。
- 三个 state 保持 null，UI 走 fallback：API Base URL 来源显示「Browser 默认」，后端管理模式显示「manual-dev」，Runtime 信息行不渲染。
- 不会触发任何 `console.error` 或网络请求。

## Verification Plan

1. `scripts/dev-all.sh` 起来后：
   - Tauri 窗口设置页应显示 API Base URL 来源 = `默认值`。
   - 设置 `LUNARIS_PORT=9001 ./scripts/dev-all.sh`（自测）应显示 `环境变量 LUNARIS_PORT`，但**注意**：当前 backend uvicorn 仍硬编码 8000，Tauri 控制面会显示 9001 而后端实际在 8000——这是已知差异，会导致 `/api/health` 不通；属于预期行为，本 change 不引入跨进程联动。
2. Browser 直接打开 `http://localhost:3000` 不报错；设置页显示 Browser 默认值。
3. 后端启停，FastAPI 状态切换不受影响。

## Risks

- 唯一风险点：`page.tsx` 是 5000+ 行单文件，diff 必须保持小。本 change 改动行数控制在 ~80 行：类型 + helper + state + effect 内 3 行 + UI 3 块。
- 不影响：现有大组件 props、状态机、缓存逻辑、API 调用等。

## Future Work

- P2：`tauri-prod-backend-pyinstaller`。等真正能 spawn sidecar 时，再考虑在 UI 加「重启后端」「打开日志目录」等动作；本 change 不做。
