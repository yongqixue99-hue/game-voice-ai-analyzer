## 1. OpenSpec

- [x] 1.1 创建 `tauri-prod-backend-launch-design` change 目录。
- [x] 1.2 编写 `proposal.md`。
- [x] 1.3 编写 `design.md`，覆盖方案 A / B / C 对比与 15 个必答问题。
- [x] 1.4 编写根目录 `spec.md`。
- [x] 1.5 编写 capability spec：`specs/tauri-prod-backend-launch-design/spec.md`。
- [x] 1.6 编写本任务清单。

## 2. 方案对比

- [x] 2.1 方案 A：Tauri sidecar + PyInstaller。
- [x] 2.2 方案 B：本地 HTTP，开发/生产由 Tauri 管理后端进程。
- [x] 2.3 方案 C：取消本地 HTTP，迁移到 Tauri command / IPC。
- [x] 2.4 推荐方案与暂不实施理由。

## 3. 必答问题

- [x] 3.1 当前最适合方案？（A，但本 change 不实施）
- [x] 3.2 为什么不现在直接实现？
- [x] 3.3 以后实现第一步该做什么？（控制面骨架，方案 B 形态过渡）
- [x] 3.4 Python 后端如何打包？（PyInstaller，单目录优先；sidecar launcher）
- [x] 3.5 SQLite 放哪里？（App Support / db）
- [x] 3.6 用户音频放哪里？（App Support / audio）
- [x] 3.7 配置放哪里？（App Support / config.json）
- [x] 3.8 ASR 密钥如何存储？（macOS Keychain）
- [x] 3.9 端口如何选择？（127.0.0.1:0 动态）
- [x] 3.10 端口冲突如何处理？（重试 + 用户提示）
- [x] 3.11 退出时如何关闭后端？（SIGTERM → 5s → SIGKILL）
- [x] 3.12 后端崩溃时前端如何提示？（emit backend-crashed + 重启按钮）
- [x] 3.13 日志写哪里？（~/Library/Logs/LUNARIS）
- [x] 3.14 macOS 打包/签名/公证有哪些坑？（10 项已列出）
- [x] 3.15 哪些是后续任务，本阶段不做？（见 design.md §Out of Scope 与 §Phased Implementation P1-P5）

## 4. 文档同步

- [x] 4.1 更新 `docs/hand_off_status.md`：当前阶段、新增 OpenSpec change 路径、本阶段只做设计、下一步等待用户确认。

## 5. 验证

- [x] 5.1 不修改任何代码（仅新增 markdown 与索引）。
- [x] 5.2 现有 Web 入口、Tauri Shell MVP、`scripts/dev-all.sh` 不受影响。
- [x] 5.3 等待用户评审推荐方案与 P1-P5 路线图。

## 6. 后续 Change（不在本 change 内做）

- [ ] 6.1 P1：新建 change `tauri-prod-backend-control-plane`，仅做控制面骨架（端口分配 / spawn / 健康轮询 / IPC / 退出清理 / backend env 入口）。
- [ ] 6.2 P2：新建 change `tauri-prod-backend-pyinstaller`，PyInstaller 打包 + sidecar 集成。
- [ ] 6.3 P3：新建 change `tauri-prod-backend-codesign`，macOS 签名 / 公证 / Gatekeeper。
- [ ] 6.4 P4：新建 change `tauri-prod-icon-and-docs`，正式图标 + 用户文档。
- [ ] 6.5 P5：远景，自动更新 / 跨平台 / 商店分发，按需评估。
