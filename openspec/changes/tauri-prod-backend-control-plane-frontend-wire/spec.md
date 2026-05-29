# tauri-prod-backend-control-plane-frontend-wire

## Goal

把 P1 的三个只读 Tauri commands 接到设置页，最小增量、零新依赖、不重构。

## Requirements

1. MUST 仅修改 `frontend/src/app/page.tsx`；MUST NOT 引入新文件、新 npm 依赖。
2. MUST 通过 `window.__TAURI_INTERNALS__.invoke` 调用 IPC，MUST NOT 引入 `@tauri-apps/api`。
3. MUST 仅在 `runtimeEnvironment === "Tauri"` 时调用 IPC；Browser 模式 MUST 不报错、不发额外请求。
4. MUST 新增 3 个 `SettingRow`：「API Base URL 来源」「后端管理模式」「Tauri Runtime 信息」（最后一行仅 Tauri 模式渲染）。
5. MUST NOT 调用 `start_backend` / `stop_backend`，UI MUST NOT 出现启停按钮。
6. MUST 显示「占位，生产版待实现」标识，避免误导。
7. MUST 不破坏现有「运行环境 / API Base URL / FastAPI 状态 / 重新检查」行为。
8. MUST 不修改 backend、SQLite、ASR、`scripts/dev-all.sh`、`tauri.conf.json`、Rust 代码。

## Acceptance

- `npm run lint` 通过（不引入新 errors）。
- `scripts/dev-all.sh` 启动正常，三件套均可用。
- Tauri 窗口设置页 3 个新行渲染正常并显示 Rust 控制面返回的字段。
- Browser `http://localhost:3000` 设置页 3 个新行渲染 fallback 文案，控制台无错误。
- FastAPI 启停切换的「已连接 / 未连接」逻辑保持不变。

## Out of Scope

- 任何 PyInstaller / sidecar / 生产构建工作。
- 后端进程启停按钮 / 日志目录入口。
- `page.tsx` 拆分 / 设置页 UI 重构。
