# tauri-prod-backend-launch-design

## Goal

为 LUNARIS 桌面 App 的生产版本设计后端启动方案：用户安装后无需手工操作即可使用全部功能，FastAPI 后端的进程生命周期、数据 / 音频 / 配置 / 密钥 / 日志的落盘位置、退出清理、崩溃恢复与 macOS 打包风险均有明确方案。本 change 仅产出设计文档，不产生任何代码改动。

## Background

Tauri Shell MVP 与开发期一键启动脚本均已完成；前端运行环境识别、API Base URL 运行时配置、`/api/health` 健康检查端点已就绪。生产打包尚未启动，且打包后默认数据路径会落到只读 App Bundle 内，必须先确定方案再实施。

## Requirements

1. 本 change MUST 只产出文档，MUST NOT 修改任何业务代码、Rust 代码、Python 代码、数据库 schema 或现有启动脚本。
2. MUST 对比至少三种方案：
   - A：Tauri sidecar + PyInstaller。
   - B：本地 HTTP，开发/生产由 Tauri 统一管理后端进程（不打包 Python）。
   - C：取消本地 HTTP，迁移到 Tauri command / IPC。
3. MUST 明确推荐方案，并说明为什么暂不在本 change 实施。
4. MUST 定义 SQLite、用户音频、派生缓存、配置、密钥、日志的落盘位置（至少给出 macOS 路径，Windows / Linux 占位）。
5. MUST 定义生产期端口选择策略与冲突处理（绑定地址 MUST 为 `127.0.0.1`）。
6. MUST 定义后端健康检查、退出清理、崩溃恢复的契约。
7. MUST 列出 macOS 打包、签名、公证已知坑。
8. MUST 给出分阶段实施路线图，并明确「本阶段不做」的事项。
9. SHOULD 列出仍需调研或决策的 open questions。
10. MUST 兼容现有 Web 浏览器入口；不得要求废弃 FastAPI。

## Architecture (Production Target)

```text
.app launch
  └─ Tauri Rust main
      ├─ bind 127.0.0.1:0  → 取空闲端口 P
      ├─ resolve data dirs via tauri::api::path::app_data_dir()
      ├─ spawn sidecar lunaris-backend
      │    env: LUNARIS_PORT=P,
      │         LUNARIS_DATA_DIR=~/Library/Application Support/LUNARIS,
      │         LUNARIS_DB_URL=sqlite:///.../db/lunaris.sqlite3,
      │         LUNARIS_AUDIO_DIR=.../audio,
      │         LUNARIS_LOG_DIR=~/Library/Logs/LUNARIS
      ├─ poll http://127.0.0.1:P/api/health (200ms, timeout 10s)
      ├─ emit backend-ready  → 前端 invoke get_api_base_url → 写入运行时配置
      ├─ on RunEvent::ExitRequested → SIGTERM sidecar → wait 5s → SIGKILL → exit
      └─ on child exit (unexpected) → emit backend-crashed → UI 提示重启
```

## Storage Contract

| 类别 | macOS 路径 | 说明 |
| --- | --- | --- |
| 数据库 | `~/Library/Application Support/LUNARIS/db/lunaris.sqlite3` | 用户数据 |
| 用户音频 | `~/Library/Application Support/LUNARIS/audio/` | 录音 / 上传原文件 |
| 派生缓存 | `~/Library/Caches/LUNARIS/audio-cache/` | 可被系统清理 |
| 应用配置 | `~/Library/Application Support/LUNARIS/config.json` | 非密文偏好 |
| 密钥 / Token | macOS Keychain，service=`com.lunaris.voice-analyzer` | 禁止明文落盘 |
| 日志 | `~/Library/Logs/LUNARIS/` | 7 日轮转 |
| 默认资源 | App Bundle Resources（只读） | 首次启动复制到 App Support |

## Out of Scope

- 任何代码改动。
- PyInstaller spec / Rust sidecar 实现 / 签名脚本。
- 自动更新、托盘、悬浮窗、系统声音录制、本地模型部署。
- Windows / Linux 详细方案。
- 卸载器、远程日志上报、多账号 profile。

## Acceptance

- `proposal.md` / `design.md` / `tasks.md` / `spec.md` 文件齐全。
- 设计文档覆盖任务书中列出的 15 个必答问题。
- `docs/hand_off_status.md` 已同步当前阶段与下一步任务。
- 无代码改动。
