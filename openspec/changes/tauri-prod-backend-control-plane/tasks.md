## 1. OpenSpec

- [x] 1.1 创建 `tauri-prod-backend-control-plane` change 目录。
- [x] 1.2 编写 `proposal.md`。
- [x] 1.3 编写 `design.md`，含 IPC 契约、为何前端暂不接线、风险与回滚。
- [x] 1.4 编写 `spec.md`。
- [x] 1.5 编写 capability spec：`specs/tauri-prod-backend-control-plane/spec.md`。

## 2. Rust 实现

- [x] 2.1 在 `frontend/src-tauri/Cargo.toml` 增加 `serde` derive 依赖。
- [x] 2.2 在 `frontend/src-tauri/src/main.rs` 实现 `resolve_api_base_url` 辅助。
- [x] 2.3 新增 `get_api_base_url` Tauri command。
- [x] 2.4 新增 `get_runtime_info` Tauri command。
- [x] 2.5 新增 `get_backend_status` Tauri command（固定 mode=external_dev）。
- [x] 2.6 新增 `start_backend` 占位 command（ok=false，明确文案）。
- [x] 2.7 新增 `stop_backend` 占位 command（ok=false，明确文案）。
- [x] 2.8 在 `tauri::Builder::default()` 注册 invoke_handler。
- [x] 2.9 不修改 `capabilities/default.json`、`tauri.conf.json`、前端、backend、scripts。

## 3. 验证

- [x] 3.1 `scripts/dev-all.sh` 启动 backend + frontend + tauri 三者均成功。
- [x] 3.2 后端 `/api/health` 返回 200。
- [x] 3.3 前端 `http://localhost:3000` 200。
- [x] 3.4 Tauri 二进制 `lunaris-desktop` 进程运行；窗口由用户人工确认正常。
- [x] 3.5 Ctrl+C / SIGTERM 通过 `scripts/dev-all.sh` 仍可一键清理。

## 4. 文档

- [x] 4.1 更新 `docs/hand_off_status.md`：当前阶段、OpenSpec 路径、commit、下一步建议（P1.5 前端接线 → P2 PyInstaller）。

## 5. 后续 Change（不在本 change 内做）

- [ ] 5.1 P1.5：`tauri-prod-backend-control-plane-frontend-wire`，在设置页接线新 IPC，显示「API Base URL 来源」「后端管理模式」两个只读字段。
- [ ] 5.2 P2：`tauri-prod-backend-pyinstaller`，替换 `start_backend` / `stop_backend` 为真正的 sidecar spawn / kill。
- [ ] 5.3 P3：macOS 签名 / 公证。
- [ ] 5.4 P4：正式图标 + 用户文档。
