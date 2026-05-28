# desktop-app-architecture-research

## Goal

更新桌面端技术架构研究，将第一正式路线调整为 Tauri 优先，并明确如何复用当前 Next.js 前端、保留 FastAPI 本地服务、规划桌面数据目录、配置密钥、云端 ASR 公网 URL、系统声音、混录、托盘、迷你录音窗和 FunASR Local Provider。

## Background

当前 Web MVP 已完成上传、播放、阿里云 ASR、转写时间轴、转写编辑、说话人重命名、浏览器录音、自动分析、长录音分段、整场总结、导出和桌面风格 UI。

此前研究偏向 Electron，但新的产品判断是：应用未来可能长期后台运行、录音、分段处理和显示迷你录音窗，因此更在意安装包体积、内存占用和长期产品质感。为了避免后期从 Electron 迁移到 Tauri 的成本，桌面端第一正式路线现在优先研究 Tauri。

## Desktop App Goals

1. 第一版桌面端可以打开应用窗口。
2. 第一版优先加载当前桌面风格 Web UI。
3. FastAPI 后端继续作为本地 API 服务。
4. Tauri 壳负责检测或后续管理本地后端进程。
5. 桌面端使用本地 SQLite 和本地音频文件目录。
6. 保持现有上传、浏览器录音、ASR、AI 总结、分段长录音、整场总结和导出能力可复用。
7. Tauri 路线要为后续托盘、迷你录音窗、系统能力和更低资源占用留出空间。

## Tauri vs Electron Comparison

### Tauri

优势：

- 更轻量，长期后台运行时更符合产品目标。
- 使用系统 WebView，不内置完整 Chromium，安装包体积和内存占用通常更低。
- Rust shell 更适合逐步接入原生窗口、托盘、目录、权限、sidecar 和系统能力。
- 越早采用 Tauri，越能避免 Electron 后期迁移成本。

风险：

- WebView 行为不是完全统一的 Chromium，需要实测当前录音和播放能力。
- 管理 Python/FastAPI sidecar 需要额外设计。
- 团队需要维护 Tauri/Rust 工程栈。
- Next.js 生产加载方式需要静态导出 spike。

### Electron

优势：

- Chromium 内置，当前 Web UI 兼容性最确定。
- Node 主进程生态成熟，管理本地 Python 子进程相对直接。
- 对 Next.js 开发体验友好。

风险：

- 包体和内存占用更高。
- 长期后台运行、常驻录音、迷你窗场景更容易形成资源压力。
- 如果后续再迁移 Tauri，会迁移窗口、进程管理、配置、托盘和打包链路。

## Recommended Route

推荐路线：Tauri 优先，Electron 作为风险兜底。

桌面端第一正式路线应基于 Tauri；如果 Tauri 在关键 WebView 能力、Next 加载或 Python sidecar 上出现不可接受阻塞，再短期回退 Electron。

## Recommended Architecture

```text
Tauri App
  ├─ Rust shell
  │   ├─ 创建主窗口
  │   ├─ 后续创建迷你录音窗
  │   ├─ 获取 app data 路径
  │   ├─ 读取本地配置
  │   ├─ 后续读写系统 keychain
  │   ├─ 检测 FastAPI 端口
  │   └─ 后续启动 FastAPI sidecar
  │
  └─ WebView Renderer
      └─ 当前 Next.js 桌面风格 UI
          └─ 调用本地 FastAPI API

FastAPI Local Backend
  ├─ SQLite
  ├─ storage/audio
  ├─ ASR Provider: aliyun / mock / future funasr-http
  ├─ LLM Provider: dashscope / openai / mock
  └─ session/chunk/summary/export

App Data Directory
  ├─ config/app-config.json
  ├─ data/app.db
  ├─ storage/audio
  ├─ storage/exports
  └─ logs
```

## Frontend Reuse Plan

1. 复用当前 `frontend/` Next.js UI。
2. 不重写桌面 UI。
3. 开发模式：
   - Tauri WebView 加载 `http://localhost:3000`。
   - Next.js 使用 `npm run dev`。
4. 生产模式优先验证：
   - Next.js `output: "export"` 静态导出。
   - Tauri 加载导出的静态资源。
5. 如果静态导出失败：
   - 先列出阻塞点。
   - 优先小改前端以适配静态导出。
   - 若仍不可行，再考虑 Tauri 启动本地 Next server。
6. 桌面模式需要运行时 API Base URL 注入，不应只依赖构建时 `NEXT_PUBLIC_API_BASE_URL`。

## Backend Packaging Plan

1. FastAPI 继续作为本地 API 服务。
2. 第一版 Tauri shell MVP 允许手动启动 FastAPI。
3. Tauri 启动后检测后端连接状态。
4. 后续通过 Tauri sidecar 或 shell plugin 启动 Python/FastAPI。
5. FastAPI 可后续用 PyInstaller 打包为平台可执行文件。
6. Python 打包需要单独 spike，不应阻塞 shell MVP。

## Local Data Directory Plan

桌面端数据不得写入源码目录。

推荐：

- Windows：`%APPDATA%/LUNARIS`
- macOS：`~/Library/Application Support/LUNARIS`
- Linux：XDG app data/config 目录

目录结构：

```text
LUNARIS/
  config/app-config.json
  data/app.db
  storage/audio/
  storage/exports/
  logs/
```

FastAPI 通过环境变量读取：

- `APP_DATA_DIR`
- `DATABASE_URL`
- `AUDIO_STORAGE_DIR`
- `EXPORT_DIR`

## API Key / Config Storage Plan

1. API Key 不写死到代码。
2. `.env` 不提交 git。
3. 前端不保存明文 API Key。
4. 第一版开发阶段可继续用后端 `.env` 或系统环境变量。
5. 本地配置文件只保存非敏感 provider 偏好和端口等配置。
6. 正式版应使用系统 keychain：
   - macOS Keychain。
   - Windows Credential Manager。
   - Linux Secret Service。
7. Tauri/Rust 层读取密钥后注入 FastAPI 环境变量。

## Aliyun ASR Public Audio URL Constraint

桌面端本地音频文件不能直接被阿里云 DashScope ASR 访问。

必须明确：

- `127.0.0.1`、`localhost` 和本地文件路径不能作为正式云端 ASR URL。
- 开发期可以用 localtunnel、ngrok 或 Cloudflare Tunnel。
- 正式版需要 OSS/Object Storage 临时上传和签名 URL，或改用本地 FunASR。
- 这是桌面端云端 ASR 的核心风险。

## Audio Capture Roadmap

第一版：

- 继续复用浏览器麦克风录音。
- 验证 Tauri WebView 对 MediaRecorder、audio 播放和文件上传的兼容性。

后续：

- Windows 系统声音：研究 WASAPI loopback、ffmpeg、原生插件或虚拟声卡。
- macOS 系统声音：研究虚拟声卡、ScreenCaptureKit 和权限说明。
- 麦克风 + 系统声音混录：需要混音层，不进入 shell MVP。
- 托盘和迷你录音窗：Tauri 适合后续做，但第一版不做。

## FunASR Local Provider Roadmap

1. 不把 FunASR 大模型直接塞进 Tauri 第一版。
2. 后续新增 `funasr-http` ASR Provider。
3. Win 3070 机器运行独立 FunASR HTTP 服务。
4. 桌面配置保存 `FUNASR_BASE_URL`。
5. FastAPI 调用 FunASR HTTP 服务，转换为统一 transcript segments。
6. HTTP Provider 稳定后，再评估 sidecar 或安装向导。

## Build / Packaging Roadmap

1. `tauri-shell-mvp`：最小 Tauri 壳，开发模式加载 Next localhost，检测 FastAPI。
2. `next-static-export-spike`：验证 Next.js 静态导出。
3. `desktop-runtime-config`：前端支持运行时 API Base URL。
4. `desktop-data-dir-migration`：后端支持桌面 app data 目录。
5. `tauri-backend-sidecar-spike`：验证打包 FastAPI 后端并由 Tauri 启动。
6. `desktop-config-keychain`：provider 配置和 API Key 安全存储。
7. 后续单独做系统声音、混录、托盘、迷你窗、FunASR HTTP Provider。

## Tauri Shell MVP 第一版范围

第一版只做：

1. 创建最小 Tauri shell。
2. 开发模式加载 `http://localhost:3000`。
3. 检测 `http://127.0.0.1:8000` FastAPI 是否可访问。
4. 在 UI 中显示后端连接状态。
5. 保持当前 Web UI 主链路可用。

## First Version Out of Scope

- 不实现系统声音录制。
- 不实现麦克风 + 系统声音混录。
- 不实现托盘。
- 不实现真正悬浮窗。
- 不实现开机启动。
- 不打包 Python 后端。
- 不实现 FunASR 本地部署。
- 不引入 OSS。
- 不重构当前前端/后端主链路。

## Risks / Trade-offs

- Tauri WebView 兼容性需要实测。
- Next.js 静态导出可能失败。
- Python/FastAPI sidecar 打包复杂。
- 阿里云 ASR 仍需要公网音频 URL 或 OSS。
- API Key 安全存储需要平台能力。
- 系统声音和混录跨平台难度高。
- Tauri/Rust 工程栈会增加学习和维护成本。

## Next Implementation Steps

下一步建议创建 `tauri-shell-mvp` change：

1. 初始化最小 Tauri shell。
2. 不创建打包流程。
3. 开发模式加载当前 Next.js dev server。
4. 检测本地 FastAPI 健康状态。
5. 增加运行时 API Base URL 最小注入方案。
6. 验证上传、播放、浏览器录音、ASR 按钮、AI 总结页面能在 Tauri WebView 中打开。
7. 不实现系统声音、托盘、悬浮窗、FunASR 本地部署。
