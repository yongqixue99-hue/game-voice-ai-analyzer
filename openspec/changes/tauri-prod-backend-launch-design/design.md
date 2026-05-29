# tauri-prod-backend-launch-design 设计

## Goal

为 LUNARIS 桌面 App 设计「生产版后端启动方案」：用户双击安装包后无需任何手工操作即可使用全部功能；FastAPI 后端的进程生命周期、SQLite / 音频 / 配置 / 密钥的落盘位置、退出清理、崩溃恢复、macOS 打包风险都需在设计阶段写清楚。本设计**不写实现代码**。

## Background

- 当前阶段：Tauri Shell MVP 已通过本机验证（提交 `d44c4d2`），开发期一键启动脚本已上线（`scripts/dev-all.sh`，提交 `09dc401`）。
- 后端：FastAPI + SQLite，Python 3.11 venv，已有 `/api/health`。
- 前端：Next.js + React 19 + Tailwind，运行环境识别为 Browser / Tauri，API Base URL 支持运行时配置。
- 桌面：Tauri v2，`bundle.active=false`，`frontendDist=../out`（Next.js 静态导出尚未验证）。
- 已知约束：
  - 阿里云 ASR 需要公网音频 URL，本地文件 / localhost 不能直接被云端访问。
  - 不实现：系统声音录制、托盘、悬浮窗、开机启动、FunASR 本地部署。
  - macOS App Bundle 内部为只读，运行时数据必须写到用户域目录。

## Architecture Overview

下文反复出现的术语：

- **App Bundle**：打包后的 `.app` / `.dmg`，内容只读、被签名。
- **App Support Dir**：macOS 用户域可写目录，约定为 `~/Library/Application Support/LUNARIS/`。
- **Resources Dir**：App Bundle 内只读资源目录，存放静态前端 + sidecar 二进制 + 默认配置模板。

## Option A: Tauri sidecar + PyInstaller

### 做什么

1. 用 PyInstaller（或 Nuitka / shiv，先以 PyInstaller 为准）把 `backend/app` 打成单文件 / 单目录可执行 `lunaris-backend`。
2. 在 `tauri.conf.json` 的 `bundle.externalBin` 中声明 sidecar，构建时被复制进 App Bundle 的 Resources。
3. Tauri Rust 入口在 app 启动时 `Command::new_sidecar("lunaris-backend").spawn()`，传入端口、数据目录等环境变量。
4. 前端通过 IPC 从 Rust 侧拿到 `apiBaseUrl`（`http://127.0.0.1:<port>`）后发起请求。
5. App 退出（`RunEvent::ExitRequested`）时主动 kill sidecar；Rust 侧维护 child handle，避免孤儿进程。

### 进程 / 端口 / 健康检查 / 日志 / 退出

- **端口**：启动时用 `TcpListener::bind("127.0.0.1:0")` 让内核分配空闲端口，再把端口号通过 env / CLI 参数传给 sidecar；同时通过 IPC 暴露给前端。固定端口（如 8000）会与开发期或其他应用冲突。
- **健康检查**：Rust 启动 sidecar 后轮询 `/api/health`，超时（如 10s）则视为后端启动失败，弹出系统对话框并退出或允许用户进入「降级模式」（仅查看历史，不能录音 / ASR）。
- **日志**：sidecar 的 stdout/stderr 由 Rust 侧捕获并按行追加到 `App Support Dir/logs/backend-YYYYMMDD.log`，并做大小或日数上限的轮转。
- **退出清理**：监听 `RunEvent::Exit`（含 macOS Cmd+Q / 关闭最后窗口的事件）时优先发 SIGTERM 给 sidecar，等待 N 秒后 SIGKILL；macOS 还需处理 sleep / wake 不影响生命周期。
- **崩溃恢复**：Rust 侧监听 child 退出码；若非主动关闭，前端弹「后端已停止，是否重启？」并允许重启 sidecar。

### macOS 打包要点

- sidecar 可执行必须按 macOS 命名规则带平台后缀（Tauri v2 需要 `lunaris-backend-x86_64-apple-darwin` / `aarch64-apple-darwin`）。
- 必须对 sidecar 可执行单独 `codesign --options=runtime`，再对整个 `.app` 重新签名。
- 公证（notarization）会校验所有可执行的硬化运行时，PyInstaller 默认产物常因 `_codesign` 漏签嵌入的 `.dylib` 导致失败，需要遍历 `Frameworks/`、`Resources/` 内的 `.so` / `.dylib` 全部签名。
- 需要 `entitlements`：`com.apple.security.cs.allow-unsigned-executable-memory`（PyInstaller / 某些 ASR SDK 用 JIT）、`com.apple.security.network.client`（网络）、麦克风权限 `com.apple.security.device.audio-input`。
- 体积：PyInstaller 单文件版启动慢（首次会自解压到 tmp），生产建议用单目录版（Onedir），但要注意 sidecar 模型只支持单文件，可改为 sidecar 仅作为 launcher，再 spawn 真实 onedir 二进制；这是本设计要写明的取舍。

### 优点

- 用户体验最好：双击即用，零外部依赖。
- 复用现有 FastAPI 全部代码，业务逻辑零迁移。
- 未来跨平台（Windows / Linux）也能复用同一思路。

### 缺点 / 难点

- PyInstaller 与 macOS 签名 / 公证踩坑成本高。
- 体积大（含 Python 解释器 + 依赖，预计 100-300MB）。
- ASR 等可能依赖 C 扩展（`numpy`、`pydantic_core`、`aiohttp`），都要在打包配置里显式 hidden imports / dylib 收集。
- 如果未来引入本地 ASR / 模型权重，要解决「资源放 Resources 还是 Application Support」的分发与升级策略。
- arm64 / x86_64 双架构要么各打一份，要么 `lipo` 合并 universal binary，CI 复杂度上升。

### 当前项目适配成本

- 中-高。需要新增 PyInstaller spec、CI 打包步骤、macOS 签名/公证流程，以及 Rust 侧 sidecar 启停代码。
- 不需要改业务代码，但需要给 backend 增加「从环境变量读取端口、数据目录、配置目录」的入口。

### 是否推荐

**推荐作为最终目标方案**，但**不在本 change 实现**。

## Option B: 本地 HTTP，开发/生产都由 Tauri 管理后端进程

### 做什么

- 不打包 Python，假设用户机器上已经安装了 Python 3.11 及依赖（或 App 安装时引导用户安装一个独立的 Python runtime，或附带 `embeddable python`）。
- Tauri Rust 在 app 启动时 `Command::new("python") -m uvicorn ...` 或调用 `.venv/bin/uvicorn`。
- 前端继续访问 `http://127.0.0.1:<port>`，端口通过 IPC 注入。

### 优点

- 实现成本低于 A，不需要 PyInstaller。
- 开发期与生产期的执行路径几乎一致，便于复现问题。

### 缺点

- 对终端用户不可接受：不能要求消费者预装 Python 与依赖。
- 即使附带 embeddable python，仍然要解决依赖打包、原生扩展签名问题，最终复杂度其实**接近方案 A**，却没有 sidecar 模型那么干净的生命周期/签名集成路径。
- 无法跨设备稳定分发。

### 与 MVP 的兼容性

- 兼容（开发期就是这种模式）。但**不能作为最终生产方案**。

### 与方案 A 的区别

- A 把 Python 当作内嵌资源，分发可控；B 把 Python 当作外部依赖，分发不可控。
- A 复杂度集中在打包/签名；B 复杂度散落在用户机器，几乎不可调试。

### 是否推荐

**仅作为 A 落地之前的过渡形态**：在 A 的实现 change 完成签名/公证之前，可以用 B 跑通「Tauri 启动 → spawn 后端 → IPC 注入端口 → 健康检查 → 退出清理」这一控制面，把 PyInstaller 风险隔离开。

## Option C: 取消本地 HTTP，迁移到 Tauri command / IPC

### 做什么

- 前端不再发 HTTP，全部走 `@tauri-apps/api/core` 的 `invoke`。
- Rust 端实现录音 / 上传 / SQLite / 文件管理；ASR / LLM 由 Rust 调云端 SDK 或通过 `reqwest` 直连。
- FastAPI 在桌面端被废弃；Web 入口需要分叉维护或废弃。

### 优点

- 启动最快，无本地端口、无健康检查、无 sidecar。
- 无需 PyInstaller、无需 Python 打包。
- 可以拿到更好的桌面 IPC 安全模型（capabilities）。

### 缺点 / 迁移成本

- 业务逻辑必须从 Python 迁到 Rust（或 Node，但又得引入 Node runtime，回到方案 A 的形态）。
- 现有 `backend/app` 全部代码作废，工作量极大。
- 单元测试、ASR provider 抽象、SQLite 模型、audio chunking 都要重写。
- Web 模式（浏览器使用）要么废弃，要么变成「Web 用 FastAPI、桌面用 Rust」的双实现，长期维护成本最高。

### 对现有 FastAPI 代码的影响

- **几乎全部需要重写**。

### 为什么当前阶段不推荐

- 与 §10 红线「不大规模重构 / 不重写已有 MVP」直接冲突。
- 当前业务尚未稳定，迁移会同时引入「平台变更 + 业务变更」两类风险。
- 对长期 Web 入口不友好。

### 是否推荐

**不推荐**。最多作为「未来某个版本要不要彻底桌面化」的远景讨论项，不在本设计的实施范围。

## Recommendation

**最终目标方案：A（Tauri sidecar + PyInstaller）。**

**实施路径：先做 A 的控制面，最后再做打包面**。具体见 §「Phased Implementation」。本 change 不进入实施。

## Storage Strategy

所有路径均以 macOS 为准，Windows / Linux 占位。

| 类别 | 位置 | 说明 |
| --- | --- | --- |
| SQLite 数据库 | `~/Library/Application Support/LUNARIS/db/lunaris.sqlite3` | 用户数据，跟随用户域备份；升级期间需要做 schema migration |
| 用户音频（录音/上传） | `~/Library/Application Support/LUNARIS/audio/` | 大文件，放用户域而非 iCloud Documents |
| 派生音频（chunk / 转码） | `~/Library/Caches/LUNARIS/audio-cache/` | 系统可在磁盘紧张时清理；丢失不影响业务 |
| 应用配置（用户偏好） | `~/Library/Application Support/LUNARIS/config.json` | 包含 ASR provider 选择、UI 偏好等非密文 |
| 密钥 / Token | macOS Keychain（service=`com.lunaris.voice-analyzer`） | **不要**写明文进 config.json；通过 Tauri `keyring` 风格 plugin 或自研 IPC 命令访问 |
| 日志 | `~/Library/Logs/LUNARIS/` 或 `App Support/logs/` | 选其一并文档化；保留 7 日轮转 |
| 默认配置模板 / 初始 SQL | App Bundle 的 Resources（只读） | 首次启动时复制到 App Support Dir |

backend 必须新增「从环境变量读取数据目录」的入口（例如 `LUNARIS_DATA_DIR`、`LUNARIS_AUDIO_DIR`、`LUNARIS_CONFIG_PATH`、`LUNARIS_DB_URL`）。Rust 侧根据 `tauri::api::path::app_data_dir()` 等解析后注入。**本 change 不实现这些环境变量**，仅在 spec 中要求。

## Port Strategy

- 选择策略：Rust 侧 `TcpListener::bind("127.0.0.1:0")` 取空闲端口，立即关闭后把端口号传给 sidecar（短暂的 TOCTOU 风险可接受，因为 127.0.0.1 范围内极少高频抢占）。
- 绑定地址：**仅 127.0.0.1**，不要 `0.0.0.0`，避免暴露到局域网。
- 冲突处理：失败重试 3 次；3 次都失败时 → 弹错误对话框 → 提示用户检查防火墙 / 安全软件 → 退出。
- 端口暴露给前端：通过 Tauri IPC 命令 `get_api_base_url()`，前端在启动时同步获取并写入运行时配置（已有运行时 API Base URL 优先级机制，可直接复用）。

## Lifecycle & Failure Modes

- **启动**：Rust → spawn sidecar → 轮询 `/api/health`（间隔 200ms，超时 10s）→ 通过则 emit `backend-ready` 事件，前端收到后开始正常请求。
- **健康检查失败**：emit `backend-failed`，前端进入降级 UI（只读历史 / 引导查看日志）。
- **退出**：监听 `RunEvent::ExitRequested` → 取消默认退出 → 主动 SIGTERM sidecar → 等待最多 5s → SIGKILL → 真正退出 app。
- **崩溃**：监听 child 退出事件，若非主动关闭则 emit `backend-crashed`，前端给「重启后端」按钮；自动重启限速（3 次/分钟）。
- **休眠 / 唤醒（macOS）**：sleep 不杀 sidecar，wake 后由前端的健康检查心跳重新拉起前端连接状态；本设计不要求自动重启。

## Logging

- backend stdout/stderr 由 Rust 捕获，逐行写入按日轮转的日志文件。
- 前端错误（uncaught / fetch 失败）通过 `console.error` + Tauri `tauri-plugin-log` 写入同一目录的 `frontend-YYYYMMDD.log`。
- 设置页提供「打开日志目录」按钮（`tauri-plugin-shell` 的 `open()`），便于用户自助排查。
- 不上报远程，至少在 v1。

## macOS Packaging Pitfalls

1. PyInstaller 产物的硬化运行时签名问题（多 `.dylib` / `.so` 漏签）。
2. 公证要求所有嵌入可执行都签名，且 entitlements 一致；打 universal binary 时 `lipo` 合并的二进制要重新签。
3. 麦克风权限：必须在 `Info.plist` 加 `NSMicrophoneUsageDescription`。
4. 网络权限：发布到 Mac App Store 要 sandbox + entitlements；非 MAS 分发只需公证。
5. arm64 / x86_64：先只发 arm64，等稳定再做 universal，避免 CI 时间翻倍。
6. Gatekeeper 首次启动会阻断未公证的 `.app`，开发自测时可用 `xattr -dr com.apple.quarantine`。
7. PyInstaller 的 `_PYI_APPLICATION_HOME_DIR` 在 `.app` 内为只读，需要把所有写路径都引导到 App Support，否则首次写日志就崩溃。
8. SQLite + iCloud / TimeMachine：把 db 放 App Support 而不是 Documents，避免 iCloud 同步冲突。
9. 升级 / 卸载：升级保留 App Support 数据，卸载留给用户手动清理（Mac 无系统级卸载器）；本 change 不做卸载器。
10. Sparkle / 自动更新：本设计不引入；后续单独 change。

## Phased Implementation（仅说明，不在本 change 内做）

1. **P1：控制面骨架（基于方案 B 的过渡形态）**
   - backend 增加 `LUNARIS_DATA_DIR` / `LUNARIS_DB_URL` / 端口可配置入口（仅入口，默认值不变）。
   - Rust 端写 spawn / 端口分配 / 健康轮询 / 退出清理 / IPC `get_api_base_url`。
   - 用本机 venv 当作 sidecar 验证整��生命周期。
2. **P2：PyInstaller 打包与 sidecar 集成**
   - 编写 `pyinstaller.spec`，输出 `lunaris-backend-aarch64-apple-darwin`。
   - 在 `tauri.conf.json` 的 `bundle.externalBin` 注册 sidecar。
   - 解决 hidden imports、dylib 收集、首次启动复制默认资源。
3. **P3：macOS 签名 / 公证 / Gatekeeper 通过**
   - 准备 Developer ID 证书、entitlements、`Info.plist` 麦克风权限。
   - 打通 `tauri build` → codesign → notarytool → staple 链路。
4. **P4：替换正式图标 + 用户文档**
5. **P5（远景）**：自动更新、Windows / Linux 适配、Mac App Store 提交（如需要）。

## Out of Scope（明确不做）

- 任何代码改动（包括 backend 环境变量入口）。
- PyInstaller 实际打包与脚本。
- Tauri sidecar 的 Rust 实现。
- 自动更新、托盘、悬浮窗、系统声音录制、FunASR 本地部署。
- Windows / Linux 打包细节（仅在 §Storage 中占位）。
- 卸载器、漫游同步、远程日志上报。

## Open Questions

- 是否需要一个独立的 `LUNARIS_PROFILE`（多账号 / 多角色数据隔离）？默认否，待用户反馈。
- 模型 / ASR 缓存（如果以后引入本地 ASR）放 Resources 还是 App Support？方向是 App Support，但首次下载体验需要单独 change。
- ASR provider 密钥的 Keychain 集成是用 `tauri-plugin-stronghold` 还是社区 `keyring` plugin？等 P1 阶段对比。
