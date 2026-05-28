# desktop-app-architecture-research

## Why

项目已经完成 Web MVP 主链路和桌面风格 UI，下一阶段准备进入桌面端。此前研究偏向 Electron，但产品方向已经调整：应用未来可能长期后台运行、录音、分段处理并显示迷你录音窗，用户更在意安装包体积、内存占用和长期产品质感。

因此需要更新桌面端架构研究，将第一正式路线调整为 Tauri 优先，并明确如何在不重构现有前后端主链路的前提下复用 Next.js UI 和 FastAPI 本地服务。

## What Changes

- 将桌面端推荐路线从 Electron 优先调整为 Tauri 优先。
- 重新比较 Tauri 与 Electron 对本项目的适配度。
- 明确 Tauri 第一版如何复用当前 Next.js 前端。
- 明确 Tauri 开发模式加载 localhost、生产模式优先加载 Next.js 静态导出资源。
- 明确如果 Next.js 不能静态导出，需要本地前端 server 或前端改造 spike。
- 明确 FastAPI 继续作为本地 API 服务，第一版可手动启动，后续再由 Tauri sidecar/子进程管理。
- 明确桌面端 SQLite、音频文件、导出文件、日志和配置目录应迁移到系统 app data 目录。
- 明确 API Key 和 provider 配置不写死、不提交 git，第一版可用本地配置/环境变量，后续使用系统 keychain。
- 明确阿里云 ASR 的公网音频 URL 风险：桌面本地文件不能直接被云端访问，正式版需要 OSS 或本地 FunASR。
- 明确系统声音、混录、托盘、迷你录音窗和 FunASR Local 的分阶段路线。

## Capabilities

### New Capabilities

- `desktop-app-architecture-research`: 定义 Tauri 优先桌面端技术选型、架构边界、前端复用、FastAPI 本地服务、数据目录、配置密钥、音频采集、本地 ASR 和打包路线。

### Modified Capabilities

- 无。本阶段只更新研究和规划文档，不修改现有上传、录音、ASR、总结、历史记录、详情页或设置页能力要求。

## Impact

- OpenSpec：更新 `desktop-app-architecture-research` change 文档。
- 前端：不改代码；后续桌面端继续复用当前 Next.js UI。
- 后端：不改代码；后续桌面端继续保留 FastAPI 本地 API 服务。
- 桌面端：本阶段不创建 Tauri 项目、不写 Tauri 代码、不打包。
- 风险：Tauri 与 Python/FastAPI sidecar、Next 静态导出、云端 ASR 公网 URL、系统声音采集和跨平台数据目录都需要在后续 change 中逐步验证。
