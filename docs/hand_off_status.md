# 项目交接文档

> 本文档用于 Claude Code / Codex / ChatGPT 等不同助手之间的交接。
> 每完成一个阶段性任务都需要同步更新本文档（见 §12 规则）。

## 1. 项目基本信息

- 项目名称：LUNARIS（游戏语音录音 / 转写 / AI 总结桌面应用）
- 项目路径：`/Users/xueyongqi/project/project-2`
- 当前阶段：Tauri Shell MVP 已验证 + 开发期一键启动脚本已上线；当前进入「生产版后端启动方案设计」阶段（仅设计，不实现）
- 当前主要目标：在不动业务逻辑的前提下，优化开发期一键启动体验，并规划生产打包方案
- 当前推荐开发方式：Claude Code 命令行（真实终端），不要在 Claude 桌面端沙箱里跑 dev server

## 2. 产品目标

LUNARIS 旨在成为一个面向游戏 / 多人语音场景的桌面级语音分析工具，覆盖：

- 游戏语音录音 / 上传（浏览器 MediaRecorder + 文件上传）
- ASR 转写（支持多 provider，含阿里云）
- 说话人分离 / 玩家识别（规划中，后续阶段实现）
- AI 总结（单段总结 + 整场总结）
- 时间轴点击跳转（可点击转写片段定位音频位置）
- 历史记录与导出
- 桌面端壳（Tauri 优先，Electron 仅作兜底）

## 3. 当前技术栈

- 前端：Next.js 16.2.6 + React 19 + TypeScript 5 + Tailwind 4
  - UI 结构：侧边栏导航 + 多路由页面（录音 / 历史 / 详情 / 设置等）
  - 运行环境检测：Browser / Tauri 双模式
- 后端：FastAPI（Python 3.11，`backend/.venv/`）+ SQLite
  - 健康检查：`GET /api/health`（保留 `/health` 兼容）
- 桌面端：Tauri v2（`@tauri-apps/cli` 2.11.2）+ Rust 1.95
  - 启动入口：`npm run tauri dev`（在 `frontend/` 目录）
  - 加载 devUrl：`http://localhost:3000`
  - 二进制名：`lunaris-desktop`
- 数据存储：
  - SQLite 数据库：`backend/` 内（不入库，已 gitignore）
  - 音频文件：`backend/storage/audio/`（已 gitignore，仅保留 `.gitkeep`）
- 桌面方案：当前是 Tauri，**不是 Electron**；Electron 仅是兜底，不要重做

## 4. 已完成工作

### Web MVP 已完成

- 浏览器录音（MediaRecorder）
- 音频上传
- 音频转写（ASR）
- ASR provider 抽象，含阿里云 provider（具体 mock / 真实状态以代码与 OpenSpec `real-asr-aliyun` 为准）
- AI 总结（单段）
- 长录音自动分段（`recording-session-auto-chunking`）
- 整场总结
- 可点击时间轴转写（`transcription-timeline-clickable-transcript`）
- 历史记录与导出
- SQLite 存储

### Tauri Shell MVP 已完成

- Tauri 项目结构：`frontend/src-tauri/`
- 配置：`frontend/src-tauri/tauri.conf.json`（devUrl=`http://localhost:3000`，frontendDist=`../out`）
- Cargo：`frontend/src-tauri/Cargo.toml`（tauri = "2"，无额外 features）
- Rust 入口：`frontend/src-tauri/src/main.rs`
- 权限：`frontend/src-tauri/capabilities/default.json`
- 脚本：`frontend/package.json` 中的 `"tauri": "tauri"`
- 设置页：运行环境（Browser/Tauri）显示
- 设置页：FastAPI 健康检查状态（已连接 / 未连接 / 检查中）
- 设置页：API Base URL 显示
- Tauri 窗口加载 `http://localhost:3000` 通过本机人工验证
- 占位图标：`frontend/src-tauri/icons/icon.png`（32×32 透明 PNG，仅供 dev 编译，正式版需替换）

## 5. OpenSpec / Markdown 文档位置

- OpenSpec 根：`openspec/`
  - `openspec/project.md`、`openspec/roadmap.md`
- 已归档 / 已完成的 changes（节选）：
  - `openspec/changes/tauri-shell-mvp/`
    - `proposal.md` / `design.md` / `spec.md` / `tasks.md`
    - `specs/tauri-shell-mvp/spec.md`
  - `openspec/changes/desktop-app-architecture-research/`
  - `openspec/changes/real-asr-aliyun/`
  - `openspec/changes/auto-transcribe-and-summary/`
  - `openspec/changes/audio-upload-playback/`
  - `openspec/changes/browser-recording-basic/`
  - `openspec/changes/transcription-timeline-clickable-transcript/`
  - `openspec/changes/recording-session-auto-chunking/`
  - `openspec/changes/mvp-stabilization-and-e2e-check/`
- 项目文档：
  - `docs/tauri-shell-mvp.md`（三终端开发启动说明）
  - `docs/manual-e2e-test.md`
  - `docs/hand_off_status.md`（本文件）
  - `openspec/changes/tauri-prod-backend-launch-design/`（生产版后端启动方案设计，仅文档）
    - `proposal.md` / `design.md` / `spec.md` / `tasks.md`
    - `specs/tauri-prod-backend-launch-design/spec.md`
- 设计稿：`design/LUNARIS-desktop-ui-handoff.md`
- 代码内说明：`frontend/README.md`、`frontend/AGENTS.md`、`frontend/CLAUDE.md`、`backend/README.md`

## 6. Git 状态与重要提交

- 当前分支：`main`
- 重要提交：
  - `b450123` 完成 Web MVP 与 Tauri shell MVP 初版（Codex / Claude 桌面端阶段）
  - `d44c4d2` 修复 Tauri 启动链路：补齐 icons/icon.png 占位资源（Claude Code 真实终端首次完整验证）
  - `143dab5` 新增项目交接文档
  - `09dc401` 新增开发环境一键启动脚本
  - 本次提交：新增 Tauri 生产后端启动方案设计（hash 提交后补充）

## 7. 当前验证结果

均在真实终端（macOS, darwin 25.5.0）通过：

- 后端 uvicorn 在 `:8000` 可运行
- `GET http://127.0.0.1:8000/api/health` → `{"status":"ok","service":"fastapi","version":"0.1.0"}`
- 前端 Next dev 在 `:3000` 可运行（200 OK）
- Tauri dev 可启动（首次冷编译约 11 分钟，340 crates；增量编译数秒）
- Tauri 窗口可加载 Web UI（非空白页）
- 侧边栏导航可点击切换
- 设置页运行环境识别为 `Tauri`
- 设置页显示 API Base URL
- FastAPI 状态切换验证：
  - 后端启动 → 已连接 ✅
  - kill uvicorn → 未连接 ✅
  - 重启 uvicorn → 恢复已连接 ✅
- 前端 lint：0 errors（仅 1 个 `target/debug` 内部生成文件 warning，与项目代码无关）

## 8. 常用启动命令

### 一键启动（推荐用于本地开发）

```bash
cd /Users/xueyongqi/project/project-2
./scripts/dev-all.sh
```

`scripts/dev-all.sh` 会按顺序拉起 backend（uvicorn :8000）、frontend（next dev :3000）、tauri dev，
日志合并到当前终端并带彩色前缀 `[backend] / [frontend] / [tauri]`。
在前台运行时按 `Ctrl+C` 会统一清理三个子进程及其后代（包括 cargo / lunaris-desktop），不留残留。
启动前会自动检查：`backend/.venv`、`frontend/node_modules`、`cargo`、端口 3000/8000 是否被占用，
有任何前置缺失会提示并退出。

该脚本仅用于开发环境，不是生产打包方案；现有手动三终端启动方式继续可用，互不影响。

### 手动三终端启动（保留）

后端：

```bash
cd /Users/xueyongqi/project/project-2/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

前端：

```bash
cd /Users/xueyongqi/project/project-2/frontend
npm run dev
```

Tauri：

```bash
cd /Users/xueyongqi/project/project-2/frontend
npm run tauri dev
```

检查：

```bash
cd /Users/xueyongqi/project/project-2/frontend
npm run lint
```

Git：

```bash
cd /Users/xueyongqi/project/project-2
git status
git log --oneline -5
```

## 9. 已知限制

- 当前 Tauri dev 依赖手动启动后端和前端（三终端）
- Tauri 目前只是桌面壳，不负责自动启动 FastAPI
- 当前没有打包 Python 后端
- 当前没有生产安装包（`bundle.active = false`）
- `frontend/src-tauri/icons/icon.png` 是 32×32 透明占位 PNG，正式版需要替换为多尺寸图标（含 `.icns` / `.ico`）
- 阿里云 ASR 在桌面端仍需要公网音频 URL；本地文件 / localhost URL 不能被云端直接访问
- 不实现：系统声音录制、混录、托盘、悬浮窗、开机启动、FunASR 本地部署
- Claude 桌面端沙箱无法监听端口，无法验证 dev server，必须用 Claude Code 命令行
- macOS 系统：darwin 25.5.0；Node v26；Python 3.11（venv）；Rust 1.95

## 10. 禁止事项 / 开发红线

- 不要重新初始化项目
- 不要重写 Tauri
- 不要从 Electron 重做
- 不要大规模重构
- 不要删除 OpenSpec / Markdown 文档
- 不要随意改业务逻辑（录音、上传、ASR、总结、时间轴、历史记录、导出等）
- 不要修改数据库结构，除非任务明确要求
- 不要把音频文件、`node_modules`、`.next`、`src-tauri/target`、`.venv`、`src-tauri/gen/` 等提交进 Git
- 每次任务前先 `git status`
- 每次任务完成后更新本文档 `docs/hand_off_status.md`

## 11. 下一阶段建议任务

### 下一阶段目标：开发环境一键启动与桌面端启动链路优化

当前需要同时开三个终端（uvicorn / Next dev / Tauri dev）。下一步**先不要做复杂打包**，也不要急着把 Python 后端塞进 Tauri。先做低风险的开发体验优化。

### 下一阶段目标：生产版后端启动方案（仅设计，等用户评审）

`openspec/changes/tauri-prod-backend-launch-design/` 已产出方案对比与路线图。**本阶段只做设计文档，不写实现代码**。等用户确认推荐方案（方案 A：sidecar + PyInstaller）与 P1-P5 分阶段路线后，再为 P1 单独新建实现 change（建议命名 `tauri-prod-backend-control-plane`）。

#### 优先级 A：~~开发期一键启动脚本~~ ✅ 已完成（`scripts/dev-all.sh`）

#### 优先级 B：~~Tauri 生产版后端启动方案（仅设计）~~ ✅ 已完成文档草案，等待用户评审

- 写设计文档说明：
  - 如何让 Tauri 自动拉起 FastAPI
  - PyInstaller / Tauri sidecar / 本地 HTTP 服务的取舍
  - 打包时如何处理 Python 解释器、依赖、模型、ASR provider 配置、SQLite 路径、音频存储目录
  - macOS 签名 / 公证可能影响

#### 优先级 C：正式打包

- 替换正式多尺寸图标（`.icns` / `.ico` / 各 PNG 尺寸）
- `tauri build` 生产打包
- macOS `.app` / `.dmg` 安装包本地验证

## 12. 每次任务更新规则

每次 Claude Code（或其他助手）完成任务后，必须更新本文档以下小节：

- §1 当前阶段
- §4 已完成工作
- §6 Git 状态与重要提交（追加新 commit hash 与说明）
- §7 当前验证结果
- §9 已知限制（如有新增）
- §11 下一阶段建议任务

如果任务产生了新命令、新脚本、新配置，必须同步写进 §8 常用启动命令；如果触碰了红线或新增了红线，须更新 §10。
