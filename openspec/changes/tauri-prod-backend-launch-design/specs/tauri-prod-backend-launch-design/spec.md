# tauri-prod-backend-launch-design 能力规格

## Goal

新增能力 `tauri-prod-backend-launch-design`：以设计文档形式约束 LUNARIS 桌面 App 生产版的后端启动、进程生命周期、数据落盘、macOS 打包风险与分阶段实施路线，作为后续实现 change 的输入。

## Requirements

1. 必须产出 `proposal.md`、`design.md`、`spec.md`、`tasks.md` 四份文档。
2. 必须给出方案 A / B / C 的对比分析，并指明推荐方案。
3. 必须为 SQLite、音频、派生缓存、配置、密钥、日志六类数据明确 macOS 落盘位置；Windows / Linux 至少占位。
4. 必须规定生产期端口绑定地址为 `127.0.0.1`，且端口动态分配。
5. 必须规定退出时优雅关闭后端的语义（SIGTERM → 等待 → SIGKILL）。
6. 必须列出 macOS 打包、签名、公证至少 5 项已知坑。
7. 必须明确「本阶段不做」的事项。
8. 必须不引入任何代码改动。
9. 必须更新 `docs/hand_off_status.md` 反映当前阶段。
10. 必须不破坏现有 Web 浏览器入口、Tauri Shell MVP、`scripts/dev-all.sh`。

## Out of Scope

实施工作（PyInstaller spec、Rust sidecar、签名脚本、CI 打包）由后续独立 change 承接，不在本能力中。
