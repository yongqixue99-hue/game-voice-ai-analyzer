## 1. OpenSpec 文档更新

- [x] 1.1 更新 `proposal.md`，将桌面端路线调整为 Tauri 优先。
- [x] 1.2 更新 `design.md`，覆盖 Tauri 架构、Next.js 复用、FastAPI 本地服务、数据目录、密钥存储、ASR URL 风险、音频采集和 FunASR 路线。
- [x] 1.3 更新根目录 `spec.md`，便于人工阅读完整研究结论。
- [x] 1.4 更新 `specs/desktop-app-architecture-research/spec.md`，满足 OpenSpec capability spec 要求。
- [x] 1.5 更新 `tasks.md`，记录本次研究调整已完成。

## 2. Tauri 优先研究

- [x] 2.1 重新比较 Tauri 与 Electron。
- [x] 2.2 明确推荐路线为 Tauri 优先、Electron 作为兜底。
- [x] 2.3 研究当前 Next.js 前端在 Tauri 中的开发和生产加载方式。
- [x] 2.4 研究 Next.js 不能静态导出时的处理路径。
- [x] 2.5 研究 FastAPI 手动启动、Tauri 后续 sidecar/子进程管理和 Python 打包复杂度。
- [x] 2.6 研究 Windows/macOS/Linux 桌面数据目录策略。
- [x] 2.7 研究 API Key、provider 配置、本地配置文件和系统 keychain 路线。
- [x] 2.8 明确阿里云 ASR 公网音频 URL 风险和 OSS/FunASR 替代路线。
- [x] 2.9 规划 Windows 系统声音、麦克风 + 系统声音混录、托盘和迷你录音窗路线。
- [x] 2.10 规划 FunASR Local Provider 通过 HTTP 连接 Win 3070 服务。

## 3. 下一阶段建议

- [x] 3.1 定义 `tauri-shell-mvp` 第一版功能范围。
- [x] 3.2 明确第一版不做系统声音录制、托盘、悬浮窗、FunASR 本地部署、桌面打包和主链路重构。
- [x] 3.3 给出下一步进入 `tauri-shell-mvp` 的实施顺序。
