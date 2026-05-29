## 1. OpenSpec

- [x] 1.1 创建 change 目录与 4 份文档。

## 2. 前端实现

- [x] 2.1 `window.__TAURI_INTERNALS__` 类型补全 `invoke` 签名。
- [x] 2.2 新增 `TauriApiBaseUrlInfo` / `TauriRuntimeInfo` / `TauriBackendStatus` 类型。
- [x] 2.3 新增 `apiBaseUrlSourceLabel` 映射。
- [x] 2.4 新增 `invokeTauri<T>(cmd)` helper（吞错返回 null）。
- [x] 2.5 新增三个 useState：`tauriApiBaseUrlInfo` / `tauriRuntimeInfo` / `tauriBackendStatus`。
- [x] 2.6 在现有 runtime 检测 useEffect 内追加 Tauri 模式下的三个 invoke。
- [x] 2.7 设置页新增「API Base URL 来源」`SettingRow`。
- [x] 2.8 设置页新增「后端管理模式」`SettingRow`，含占位徽标。
- [x] 2.9 设置页新增「Tauri Runtime 信息」`SettingRow`，仅 Tauri 模式渲染。
- [x] 2.10 不调用 `start_backend` / `stop_backend`，不暴露按钮。

## 3. 验证

- [x] 3.1 `scripts/dev-all.sh` 起来后 Tauri / Browser 均可访问设置页。
- [x] 3.2 `npm run lint` 无新增 error。
- [ ] 3.3 用户人工确认 Tauri 窗口设置页 3 个新行渲染正常。
- [ ] 3.4 用户人工确认 Browser 模式下设置页不报错且显示 fallback 文案。

## 4. 文档

- [x] 4.1 更新 `docs/hand_off_status.md`。

## 5. 后续 Change

- [ ] 5.1 P2：`tauri-prod-backend-pyinstaller`，用最小 hello-world FastAPI 验证 PyInstaller + sidecar 链路；替换占位实现。
