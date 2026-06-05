# 项目交接文档

> 本文档用于 Claude Code / Codex / ChatGPT 等不同助手之间的交接。
> 每完成一个阶段性任务都需要同步更新本文档（见 §12 规则）。

## 1. 项目基本信息

- 项目名称：LUNARIS（游戏语音录音 / 转写 / AI 总结桌面应用）
- 项目路径：`/Users/xueyongqi/project/project-2`
- 当前阶段：桌面内部 Beta 候选，正在验证第一版原生麦克风录音。
- 当前主要目标：确认桌面麦克风录音 -> WAV 上传 -> Win FunASR -> DashScope 总结链路，然后进入游戏自测 Alpha。
- 当前推荐开发方式：Codex / Claude Code 在真实终端中工作；不要依赖沙箱环境验证端口监听。

## 2. 产品目标

LUNARIS 旨在成为一个面向游戏 / 多人语音场景的桌面级语音分析工具，覆盖：

- 游戏语音录音 / 上传。
- ASR 转写（支持 mock / aliyun / funasr_http）。
- 说话人标签修正 / 玩家识别（当前支持手动重命名，自动识别规划中）。
- AI 总结（单段总结 + 整场总结）。
- 时间轴点击跳转（可点击转写片段定位音频位置）。
- 历史记录与导出。
- 桌面端壳（Tauri 优先，Electron 仅作兜底）。

当前最重要的产品缺口是：桌面端原生音频采集。上传音频已可用；Tauri WebView 内置网页录音在 macOS 上不可依赖。
第一版 Tauri/Rust 原生麦克风录音已经接入，仍需真实窗口手测 macOS 麦克风授权与录音上传。

## 3. 当前技术栈

- 前端：Next.js 16.2.6 + React 19 + TypeScript 5 + Tailwind 4。
  - UI 结构：侧边栏导航 + 控制台 / 历史记录 / 会话 / 设置。
  - 运行环境检测：Browser / Tauri 双模式。
- 后端：FastAPI（Python 3.11，`backend/.venv/`）+ SQLite。
  - 健康检查：`GET /api/health`（保留 `/health` 兼容）。
  - 桌面 sidecar 默认端口：`127.0.0.1:18080`。
  - Web dev 后端默认端口：`127.0.0.1:8000`。
- 桌面端：Tauri v2（`@tauri-apps/cli` 2.11.2）+ Rust 1.95。
  - 启动入口：`cd frontend && npm run tauri dev`。
  - Tauri dev 会启动 Next dev，并自动拉起真实 FastAPI sidecar。
  - 二进制名：`lunaris-desktop`。
- 数据存储：
  - Web dev SQLite：`backend/recordings.sqlite3`。
  - 桌面数据目录：`~/Library/Application Support/com.lunaris.voice-analyzer/data/`。
  - 桌面配置：`~/Library/Application Support/com.lunaris.voice-analyzer/data/config/.env`。
- 桌面方案：当前是 Tauri，**不是 Electron**；Electron 仅是兜底，不要重做。

## 4. 已完成工作

### Web / 后端主链路

- 音频上传与播放。
- ASR provider 抽象：`mock` / `aliyun` / `funasr_http`。
- 阿里云 ASR provider 保留，用于有公网音频 URL 的场景。
- FunASR HTTP provider 已接入真实 Win 3070 服务。
- 转写时间轴展示与点击跳转。
- 转写文本编辑与说话人重命名。
- AI 总结（mock / DashScope / OpenAI provider 结构）。
- 当前桌面配置下 AI 总结使用 `dashscope` / `qwen-plus`。
- 长录音 session / chunk 数据模型、分段处理、整场总结和导出能力已具备 Web 侧实现基础。

### 桌面 / Sidecar

- Tauri 项目结构：`frontend/src-tauri/`。
- 真实 FastAPI 后端已通过 PyInstaller 打成 `lunaris-real-backend` sidecar。
- Tauri 启动时会自动拉起真实 sidecar，不再需要用户手动点“启动真实后端”。
- 前端在 Tauri 模式下会把 API base 指向真实 sidecar：`http://127.0.0.1:18080`。
- 关闭 Tauri 时会尝试清理由 Tauri 启动的 sidecar。
- 桌面数据目录支持 `config/.env`，frozen sidecar 不依赖仓库根 `.env`。
- 第一版原生麦克风录音已接入：
  - Tauri/Rust 使用 `cpal` 采集麦克风。
  - `hound` 写 WAV 到桌面数据目录临时位置。
  - Tauri command 上传 WAV 到现有 `/api/recordings/upload`。
  - 前端新增 Tauri-only “桌面麦克风”卡片，上传成功后刷新历史并可触发自动分析。
  - 不包含系统声音、游戏声音、队友语音或混录。

### FunASR / LLM 实测

- Win 3070 FunASR Base URL：`http://192.168.1.5:10095`。
- Health：`GET /health`。
- Models：`GET /v1/models`。
- Transcribe：`POST /v1/audio/transcriptions`。
- multipart 字段：
  - `file`: 音频文件。
  - `model`: `sensevoice`。
- 真实 MP3 上传 + FunASR 转写 + DashScope 总结已在桌面窗口中跑通。
- 当前 Win FunASR 响应只有整段 `text`，无句级时间戳；LUNARIS 会落成 1 个 `source=funasr_http` 片段，时间范围使用上传时探测到的音频时长。
- 本地 WebM 样例直连 Win 服务曾返回 500；在 Win 服务确认 WebM 解码前，优先用 MP3/WAV/M4A 测试。

## 5. OpenSpec / Markdown 文档位置

- OpenSpec 根：`openspec/`
  - `openspec/project.md`
  - `openspec/roadmap.md`
- 当前最相关的 changes：
  - `openspec/changes/funasr-provider-stabilization-and-beta-handoff/`
  - `openspec/changes/desktop-native-microphone-recording/`
  - `openspec/changes/multi-asr-provider-sprint/`
  - `openspec/changes/desktop-beta-stabilization-sprint/`
  - `openspec/changes/desktop-real-backend-sidecar-sprint/`
  - `openspec/changes/real-backend-sidecar-readiness/`
  - `openspec/changes/recording-session-auto-chunking/`
  - `openspec/changes/auto-transcribe-and-summary/`
  - `openspec/changes/browser-recording-basic/`
- 项目文档：
  - `docs/asr-providers.md`
  - `docs/funasr-http-provider-handoff.md`
  - `docs/desktop-beta-status.md`
  - `docs/desktop-beta-known-issues.md`
  - `docs/desktop-beta-test.md`
  - `docs/manual-e2e-test.md`
  - `docs/real-backend-sidecar-readiness.md`
  - `docs/hand_off_status.md`（本文件）

## 6. Git 状态与重要提交

- 当前分支：`main`
- 已提交的重要节点：
  - `b450123` 完成 Web MVP 与 Tauri shell MVP 初版。
  - `d44c4d2` 修复 Tauri 启动链路：补齐 icons/icon.png 占位资源。
  - `143dab5` 新增项目交接文档。
  - `09dc401` 新增开发环境一键启动脚本。
  - `673dc3c` 新增 Tauri 生产后端启动方案设计。
  - `5d8e023` 新增 Tauri 后端控制面骨架。
  - `8f0bf32` 完善 FunASR HTTP Provider 工程闭环。
  - `0f75d09` 收口 FunASR 桌面闭环与路线图。
- 当前未提交工作：
  - OpenSpec change：`desktop-native-microphone-recording`。
  - Tauri/Rust 原生麦克风录音第一版。
  - 前端 Tauri-only “桌面麦克风”卡片。
  - macOS `NSMicrophoneUsageDescription`。
  - 桌面 Beta 文档更新。
- 注意：仓库根 `.env` 和桌面数据目录 `config/.env` 已本地配置为 Win FunASR + DashScope，不应提交。

## 7. 当前验证结果

最近一次人工/命令验证：

- `GET http://127.0.0.1:18080/api/health` → OK。
- `GET http://127.0.0.1:18080/api/asr/status`：
  - `provider=funasr_http`。
  - `base_url=http://192.168.1.5:10095`。
  - `transcribe_path=/v1/audio/transcriptions`。
  - `model=sensevoice`。
- 当前复测 `reachable=false` / `timed out`；先前 Win 3070 服务曾返回 `device=cuda`，`models_loaded=["sensevoice"]` 并完成真实转写。继续真实 ASR 前需要确认 Windows FunASR 服务仍在运行且局域网可达。
- 真实 MP3 后端上传 + FunASR 转写曾成功。
- 桌面窗口内 AI 总结显示 `dashscope` / `qwen-plus`。
- 后端测试：`49 passed`。
- 前端 lint：通过。
- 前端 build：通过。
- Tauri `cargo check`：通过（含原生麦克风依赖）。
- Tauri `cargo test -- --test-threads=1`：`2 passed`。
- Tauri dev 当前可启动，并自动启动真实 sidecar。
- 原生麦克风真实录音：待在 Tauri 窗口手动验证权限、停止、上传和历史记录。

## 8. 常用启动命令

### 桌面 dev（当前推荐）

```bash
cd /Users/xueyongqi/project/project-2/frontend
npm run tauri dev
```

行为：

- Tauri dev 会启动 Next dev。
- Tauri 主进程会自动拉起真实 FastAPI sidecar。
- 前端会切到 `http://127.0.0.1:18080`。

检查：

```bash
curl http://127.0.0.1:18080/api/health
curl http://127.0.0.1:18080/api/asr/status
```

### Web dev（仍可用）

后端：

```bash
cd /Users/xueyongqi/project/project-2/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bash
cd /Users/xueyongqi/project/project-2/frontend
npm run dev
```

### 重新打包真实 sidecar

当修改了 `backend/app/**` 或 `backend/desktop_entry.py` 后，需要重新打包并同步：

```bash
cd /Users/xueyongqi/project/project-2/backend
./build-desktop-backend.sh
cp dist/lunaris-real-backend-aarch64-apple-darwin ../frontend/src-tauri/binaries/
```

## 9. 已知限制

- Tauri WebView 内置 `MediaRecorder/getUserMedia` 在 macOS WKWebView 中不可依赖；桌面 App 已新增 Tauri/Rust 原生麦克风入口。
- 原生麦克风第一版还需真实窗口手测 macOS 权限与录音上传。
- 当前还不能直接采集系统声音、游戏声音、Discord/游戏内队友语音。
- 当前还没有麦克风 + 系统声音混录。
- Win FunASR 当前返回整段 `text`，没有句级时间戳；时间轴粒度较粗。
- WebM 输入在当前 Win FunASR 服务上可能失败；优先用 MP3/WAV/M4A。
- 生产发布未完成代码签名 / 公证。
- 配置仍依赖数据目录 `config/.env`，后续应做设置页写配置和密钥存储。
- 不要把 `.env`、数据库、音频、PyInstaller build/dist、Tauri target 产物提交进 Git。

## 10. 禁止事项 / 开发红线

- 不要重新初始化项目。
- 不要重写 Tauri。
- 不要从 Electron 重做。
- 不要大规模重构。
- 不要删除 OpenSpec / Markdown 文档。
- 不要随意改上传、ASR、总结、时间轴、历史记录、导出等主链路。
- 不要提交真实 API Key、`.env`、数据库、音频、build/dist、二进制产物。
- 修改后端 sidecar 代码后，必须重新打包 `lunaris-real-backend` 并复制到 `frontend/src-tauri/binaries/` 才能在桌面端生效。
- 每次任务前先 `git status`。
- 每次阶段任务完成后更新本文档。

## 11. 下一阶段建议任务

### 阶段 0：收口当前 FunASR + sidecar 自动启动变更（已完成）

目标：把当前可用链路固化为干净提交。

- 更新文档和路线图。
- 跑完整验证：后端 pytest、前端 lint/build、Tauri cargo test、ASR provider smoke、桌面 sidecar 启动检查。
- 确认 `.env`、数据目录配置、数据库、音频、PyInstaller 产物不入库。
- 已提交：`0f75d09 收口 FunASR 桌面闭环与路线图`。

### 阶段 1：桌面原生麦克风录音（第一版已接入，待手测）

目标：让用户可以在 LUNARIS 桌面应用内录制自己的麦克风，不依赖 WebView `MediaRecorder`。

- OpenSpec change 已创建：`desktop-native-microphone-recording`。
- Rust 方案：`cpal` 采集，`hound` 写 WAV，Tauri command 上传。
- macOS 麦克风权限说明已加入 `frontend/src-tauri/Info.plist`。
- 前端新增 Tauri-only “桌面麦克风”卡片。
- 待手动验收：录 30 秒语音 -> 自动或手动 FunASR 转写 -> DashScope 总结。

### 阶段 2：游戏自测 Alpha

目标：边打游戏边录自己的麦克风，验证长时间稳定性。

- 验证 10-30 分钟录音不丢文件。
- 验证长录音 chunk 自动转写/总结。
- 验证失败 chunk 可重试。
- 验证整场总结和导出。
- 根据真实使用体验修复文案、状态、错误提示。

### 阶段 3：系统声音 / 队伍语音采集

目标：支持真正的游戏语音复盘。

- 新建 OpenSpec change：建议命名 `desktop-system-audio-capture`.
- 分平台调研 macOS / Windows 系统声音采集方案。
- 先定义最小可接受形态：外部虚拟声卡指南，还是内置采集。
- 再做麦克风 + 系统声音混录。
- 验收：能同时捕获自己麦克风和队友/游戏语音。

### 阶段 4：可分发 Beta

目标：让非开发者也能使用。

- 设置页配置 FunASR 地址、模型、LLM provider。
- 密钥存储从 `.env` 过渡到系统 keychain 或更安全的本地配置。
- 替换正式图标。
- `tauri build` 产出 app。
- macOS 代码签名 / 公证。
- 用户文档：安装、首次权限、FunASR 地址配置、常见错误排查。

## 12. 每次任务更新规则

每次阶段任务完成后，必须更新本文档以下小节：

- §1 当前阶段。
- §4 已完成工作。
- §6 Git 状态与重要提交。
- §7 当前验证结果。
- §9 已知限制。
- §11 下一阶段建议任务。
