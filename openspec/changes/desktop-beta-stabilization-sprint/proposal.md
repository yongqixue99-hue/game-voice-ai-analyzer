# desktop-beta-stabilization-sprint

## Why

`desktop-real-backend-sidecar-sprint` 已让 Tauri 能启动真实 FastAPI sidecar，但只验证到二进制层（cargo mock-runtime 测试 + frozen 二进制 curl）。还没有在真实 `npm run tauri dev` 窗口里跑通完整用户链路，也没尝试过 `tauri build`。

本次不加大功能，目标是让桌面端进入 **Beta 稳定**：dev 窗口稳定、真实 sidecar 可从设置页启停、核心功能在 WebView 中可用、尝试出本机 app，并把验收过程写成文档。

## What Changes

- **修复 API base 路由**：`window.__LUNARIS_CONFIG__.apiBaseUrl` 此前声明但无人赋值，前端在 Tauri 下始终请求 `:8000`。改为真实 sidecar 运行时把 runtime API base 指向其 URL（`:18080`），停止后回落默认；启停后重载 health/历史/session。
- **修复静态导出**：`next.config.ts` 加 `output: "export"`，让 `npm run build` 真正产出 `out/`（Tauri `frontendDist` 依赖它，原先只有 41B 占位 index.html）。
- **修复 build 链路**：`tauri.conf.json` 加 `beforeDevCommand`/`beforeBuildCommand`，`bundle.active=true`、`targets="app"`，使 `tauri dev`/`build` 自包含。
- **新增** `docs/desktop-beta-test.md`：手动验收清单 + 通过/known issues。
- 记录 `tauri build` 结果（成功产物或失败原因）。

## Capabilities

### New Capabilities

- 无新业务能力。

### Modified Capabilities

- `desktop-real-backend-sidecar`：前端在桌面运行时正确路由到真实 sidecar；新增静态导出与 build 触发配置，使其可被打包为本机 app。

## Impact

- 前端：`next.config.ts`、`src/app/page.tsx`（API base 路由）。
- Tauri：`tauri.conf.json`（before*Command、bundle）。
- 文档：`docs/desktop-beta-test.md`、本 change 三文档。
- 不做：系统声音录制、混录、托盘、悬浮窗、开机启动、FunASR、OSS、登录/支付，不大规模重构前后端/UI。
