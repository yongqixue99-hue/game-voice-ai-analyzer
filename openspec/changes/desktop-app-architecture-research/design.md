# desktop-app-architecture-research 设计方案

## Context

当前项目已经具备稳定 Web MVP 主链路：

```text
音频上传/浏览器录音 -> FastAPI 保存音频与元数据 -> ASR 转写 -> 可点击时间轴 -> 转写编辑 -> AI 总结 -> 长录音 session/chunks -> 整场总结 -> 导出
```

前端已经是桌面风格 Next.js Web UI，后端是 FastAPI + SQLite + 本地文件系统。现在桌面端路线从 Electron 优先调整为 Tauri 优先，核心原因是长期后台运行、录音、分段处理、迷你录音窗和产品质感更依赖轻量、低内存、原生壳能力。

参考资料：

- Tauri 架构、WebView 和 Rust shell：[Tauri Concepts](https://v2.tauri.app/concept/)
- Tauri sidecar / external binary：[Tauri Sidecar](https://v2.tauri.app/develop/sidecar/)
- Tauri shell command 能力：[Tauri Shell Plugin](https://v2.tauri.app/plugin/shell/)
- Next.js 静态导出能力与限制：[Next.js Static Exports](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)
- FastAPI 部署说明：[FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- Python 打包参考：[PyInstaller Documentation](https://pyinstaller.org/en/stable/)

## Goals / Non-Goals

**Goals:**

- 判断 Tauri 是否适合作为本项目桌面端第一正式路线。
- 明确 Tauri vs Electron 的取舍。
- 明确当前 Next.js 前端如何复用。
- 明确 Tauri 开发模式和生产模式如何加载前端。
- 明确 FastAPI 后端如何继续作为本地服务。
- 明确 Tauri 是否先手动连接后端，后续如何启动 Python 子进程/sidecar。
- 明确桌面端 SQLite、音频、导出、日志、配置和 API Key 的存储策略。
- 明确阿里云 ASR 公网音频 URL 约束。
- 明确系统声音、混录、托盘、迷你录音窗和 FunASR Local Provider 路线。
- 给出下一步 `tauri-shell-mvp` 的实施边界。

**Non-Goals:**

- 不写 Tauri 代码。
- 不创建 Tauri 项目。
- 不打包桌面应用。
- 不改现有前端 UI。
- 不改后端主链路。
- 不实现系统声音录制。
- 不实现托盘。
- 不实现真正悬浮窗。
- 不实现 FunASR 本地部署。
- 不实现登录、支付、会员系统。

## Decisions

### 1. 第一正式路线推荐 Tauri 优先

推荐：桌面端第一正式路线调整为 Tauri 优先。

理由：

- 本应用未来可能长时间后台运行、录音、分段处理和展示迷你录音窗，Tauri 的轻量壳和较低内存占用更符合长期产品形态。
- 当前 UI 已经是 Web 技术栈，Tauri 仍可通过系统 WebView 承载现有 Next.js 前端。
- 越晚从 Electron 迁移到 Tauri，桌面进程、配置、音频采集、托盘、更新和打包脚本的迁移成本越高。
- Tauri 的 Rust shell 更适合后续逐步接入更受控的本地能力，例如目录管理、系统托盘、窗口控制、sidecar 进程和权限边界。

Electron 优点仍然存在：

- Chromium 内置，Web 兼容性最一致。
- Node 主进程生态成熟，管理 Python 子进程更直接。
- 对现有 Web UI 的开发体验更顺滑。

Electron 不作为第一正式路线的原因：

- 安装包体积和内存占用通常更高。
- 如果未来长期后台运行和迷你窗成为核心体验，Electron 的资源成本更容易成为产品负担。
- 项目早期就能接受 Tauri 的工程复杂度时，优先 Tauri 可以减少后续迁移。

结论：Tauri 优先，Electron 保留为备选和风险兜底。

### 2. 继续复用当前 Next.js 前端

推荐：复用当前 `frontend/` Next.js 前端，不重新写桌面 UI。

开发模式：

```text
Tauri dev -> WebView 加载 http://localhost:3000
Next.js dev server -> npm run dev
FastAPI -> 手动启动或脚本启动
```

生产模式优先路线：

1. 尝试 Next.js 静态导出：
   - 使用 `next build` + `output: "export"`。
   - Tauri 加载导出的静态资源。
   - 当前项目大量逻辑在客户端调用 FastAPI，理论上较适合静态导出。
   - 需要验证资源路径、路由、环境变量、音频 URL 和导出后的相对路径。

2. 如果 Next.js 不能静态导出：
   - 方案 A：调整前端，去除阻碍静态导出的 Next 特性。
   - 方案 B：Tauri 生产模式启动本地 Next server sidecar，再加载 localhost。
   - 方案 C：将前端迁移为 Vite/React 静态构建，但这属于更大改造，不应在第一版直接做。

建议：

- 下一阶段 `tauri-shell-mvp` 先走开发模式加载 `localhost:3000`。
- 单独创建 `next-static-export-spike` 验证生产模式是否可静态导出。
- 不在 shell MVP 中同时解决 Tauri、Next 静态导出和 Python 打包三个问题。

### 3. FastAPI 继续作为本地 API 服务

推荐：FastAPI 后端继续保留为本地 API 服务，不把业务逻辑搬进 Tauri/Rust。

理由：

- 当前上传、ASR、AI 总结、session/chunk、SQLite、导出都在 FastAPI 中。
- Python 更适合继续承载 ASR provider、LLM provider、音频处理和未来 FunASR HTTP provider。
- Tauri shell 专注桌面壳、窗口、路径、进程、系统能力，不直接承载业务主链路。

第一版：

- 允许用户/开发脚本手动启动 FastAPI。
- Tauri 启动后检测 `127.0.0.1:8000` 或配置端口是否可访问。
- 若不可访问，UI 显示“后端未启动”状态和启动说明。

后续：

- 使用 Tauri sidecar/external binary 管理 FastAPI 打包产物。
- 或使用 Tauri shell plugin 启动开发环境 Python/uvicorn 命令。
- Tauri 负责健康检查、日志、退出清理、端口冲突处理。

Python 后端打包复杂度：

- 可用 PyInstaller 将 FastAPI 后端打成平台可执行文件。
- 需要分别在 Windows/macOS/Linux 构建。
- 需要处理 Python 依赖、动态库、证书、SQLite 路径、日志路径、杀毒误报、签名、公证和升级。

因此：Tauri shell MVP 不打包 Python 后端，只做连接检测。

### 4. 桌面数据目录必须迁移到系统 app data

打包后 SQLite、音频文件和导出文件不得继续写入源码目录。

推荐目录：

- Windows：`%APPDATA%/LUNARIS`
- macOS：`~/Library/Application Support/LUNARIS`
- Linux：XDG app data/config 目录，例如 `~/.local/share/LUNARIS` 和 `~/.config/LUNARIS`

建议结构：

```text
LUNARIS/
  config/
    app-config.json
  data/
    app.db
  storage/
    audio/
    exports/
  logs/
    backend.log
    app.log
```

后端通过环境变量读取：

```text
APP_DATA_DIR=<app-data>
DATABASE_URL=sqlite:///<app-data>/data/app.db
AUDIO_STORAGE_DIR=<app-data>/storage/audio
EXPORT_DIR=<app-data>/storage/exports
```

Tauri 负责获取平台 app data 路径，并在启动后端时传入环境变量。

### 5. API Key 与 provider 配置

原则：

- API Key 不写死到代码。
- `.env` 不提交 git。
- `.env` 不应作为正式产品密钥存储方案。
- 前端 localStorage 不保存明文 API Key。
- 不把密钥写入日志。

第一版可行方案：

- 开发阶段继续使用后端 `.env` 或系统环境变量。
- Tauri 设置页展示 provider 配置状态，但不承诺前端直接写密钥。
- 本地配置文件只保存非敏感 provider 偏好，例如 `asrProvider`、`llmProvider`、模型名、端口、数据目录。

后续正式方案：

- 使用系统 keychain / credential store 保存密钥：
  - macOS Keychain。
  - Windows Credential Manager。
  - Linux Secret Service。
- Tauri/Rust 层读写密钥，启动 FastAPI 时注入环境变量。
- FastAPI 只从环境变量或安全 IPC 获取密钥，不暴露给前端。

### 6. 阿里云 ASR 公网 URL 风险

这是桌面端最重要的产品风险之一。

当前阿里云 DashScope 非实时 ASR 需要云端服务通过 URL 拉取音频文件。桌面端本地路径或 `127.0.0.1` URL 不能被阿里云访问。

开发期：

- 可以继续使用 localtunnel、ngrok、Cloudflare Tunnel 暴露本地 FastAPI 音频 URL。
- 这适合开发验证，不适合作为正式用户体验。

正式版可选路线：

1. OSS/Object Storage 临时上传：
   - FastAPI 上传音频到 OSS。
   - 生成短时签名 URL。
   - 阿里云 ASR 拉取签名 URL。
   - 任务完成后删除临时对象。

2. 本地 ASR：
   - 引入 FunASR Local / FunASR HTTP provider。
   - 避免公网 URL 和云端拉取音频。

必须在文档和 UI 中明确：

- 桌面端使用阿里云 ASR 时，本地音频不能直接被云端访问。
- 没有公网 URL 或 OSS 时，阿里云 ASR 可能失败。

### 7. 端口冲突处理

Tauri shell 不能固定假设 FastAPI 永远在 `8000`。

建议：

1. 第一版检测默认端口 `8000`。
2. 如果不可访问，显示后端未启动。
3. 后续托管后端时：
   - 优先使用默认端口。
   - 若端口被占用，扫描可用端口或请求系统分配端口。
   - 将实际 `apiBaseUrl` 注入前端运行时配置。

前端改造方向：

- 现有 `NEXT_PUBLIC_API_BASE_URL` 是构建时变量。
- 桌面模式需要支持 Tauri 注入运行时配置，例如 `window.__LUNARIS_CONFIG__.apiBaseUrl` 或从本地 config endpoint 读取。
- 该改造应在 `tauri-shell-mvp` 或紧随其后的 change 中做最小实现。

### 8. 音频采集路线

第一版：

- 继续使用当前浏览器 `MediaRecorder` 录制麦克风。
- Tauri WebView 是否完全兼容需要实测，但这是最小复用路线。

Windows 系统声音：

- 后续单独研究：
  - WASAPI loopback。
  - Rust/原生插件。
  - ffmpeg + wasapi/dshow。
  - 虚拟声卡。

macOS 系统声音：

- 后续单独研究：
  - 虚拟声卡，如 BlackHole。
  - ScreenCaptureKit/系统权限可行性。
  - 商业化前需要非常谨慎处理权限说明。

麦克风 + 系统声音混录：

- 需要混音层：
  - 原生采集两路音频后混音。
  - ffmpeg filter。
  - 虚拟声卡把系统声音和麦克风混成一路输入。
- 不纳入 Tauri shell MVP。

托盘与迷你录音窗：

- Tauri 适合后续实现系统托盘、隐藏主窗口、打开小窗口、窗口置顶等能力。
- 但第一版不做，避免 UI shell 与音频采集同时复杂化。

### 9. FunASR Local Provider 路线

不把 FunASR 大模型直接塞进 Tauri 第一版。

推荐路线：

1. 后端新增 `funasr-http` provider。
2. Win 3070 机器单独运行 FunASR HTTP 服务。
3. Tauri 设置页或本地配置保存 `FUNASR_BASE_URL`。
4. FastAPI 调用 FunASR HTTP 服务，返回统一 transcript segments。
5. 后续再研究是否把 FunASR 服务作为可选 sidecar 或安装向导。

原因：

- FunASR 模型、CUDA、GPU 驱动、Python 依赖和跨平台打包复杂度很高。
- 将本地 ASR 作为 HTTP Provider 接入，可以先验证效果和体验，再决定是否内置。

## Recommended Architecture

```text
Tauri App
  ├─ Rust shell
  │   ├─ 创建主窗口
  │   ├─ 后续创建迷你录音窗口
  │   ├─ 获取 app data 路径
  │   ├─ 读取本地非敏感配置
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
  ├─ transcript_segments / analyses / sessions
  ├─ ASR Provider: aliyun / mock / future funasr-http
  └─ LLM Provider: dashscope / openai / mock

App Data Directory
  ├─ config/app-config.json
  ├─ data/app.db
  ├─ storage/audio
  ├─ storage/exports
  └─ logs
```

## Migration Plan

1. 当前 change：更新 Tauri 优先架构研究，不写代码。
2. `tauri-shell-mvp`：
   - 新建最小 Tauri shell。
   - 开发模式加载 `http://localhost:3000`。
   - 检测 `http://127.0.0.1:8000` FastAPI。
   - 显示后端连接状态。
   - 不创建 Python sidecar，不打包。
3. `next-static-export-spike`：
   - 验证当前 Next.js 是否能静态导出。
   - 如果失败，列出阻塞点和最小前端调整方案。
4. `desktop-runtime-config`：
   - 前端支持运行时 API Base URL。
5. `desktop-data-dir-migration`：
   - 后端支持桌面 app data 目录。
6. `tauri-backend-sidecar-spike`：
   - 用 PyInstaller 或等价工具打包 FastAPI。
   - Tauri 启动 sidecar 并健康检查。
7. 后续独立研究系统声音、混录、托盘、迷你窗和 FunASR HTTP Provider。

## Risks / Trade-offs

- [Risk] Tauri WebView 与 Chromium 行为不完全一致，MediaRecorder 支持需实测 → MVP 先验证麦克风录音、audio 播放和文件上传。
- [Risk] Next.js 静态导出可能受限 → 单独做 static export spike，不和 shell MVP 混在一起。
- [Risk] Tauri 管理 Python/FastAPI sidecar 比 Electron Node 子进程复杂 → 第一版先手动启动后端，后续做 sidecar spike。
- [Risk] Python 后端打包复杂 → 先不阻塞 Tauri shell；按平台分阶段打包。
- [Risk] 阿里云 ASR 无法访问桌面本地音频 → 开发期 tunnel，正式版 OSS 或本地 FunASR。
- [Risk] API Key 安全存储涉及平台差异 → 第一版环境变量/本地配置，正式版 keychain。
- [Risk] 系统声音采集和混录跨平台差异大 → 不进入 shell MVP，单独立项。
- [Risk] Tauri 生态对部分桌面能力需要 Rust/插件开发 → 保持第一版范围足够小。

## Open Questions

- 当前 Next.js 应用是否能无痛静态导出。
- Tauri WebView 在目标平台上对 `MediaRecorder` 的兼容性如何。
- 第一版是否只发布开发者预览，要求用户手动启动 FastAPI。
- API Key 第一版是否允许本地 `.env`，还是直接实现 keychain。
- 正式版阿里云 ASR 走 OSS，还是优先推进 FunASR HTTP provider。
