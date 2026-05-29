# real-backend-sidecar-readiness

## Why

P2（`tauri-prod-backend-pyinstaller`）已经用一个 hello-world FastAPI（`experiments/hello-backend`）打通了完整 sidecar 链路：PyInstaller 打包 → Tauri externalBin → Rust `start_backend`/`stop_backend`/`get_backend_status` → 前端设置页按钮 → 真机运行验证通过。

但 hello-backend 只是 spike。真实业务后端（`backend/app`）能否同样被 PyInstaller 打成 sidecar，还有若干**结构性阻塞点**尚未确认，最关键的是：

- 后端用 `Path(__file__).resolve().parents[2]` 推导 `project_root`，再据此拼出 SQLite 与 `storage/audio` 路径。PyInstaller 冻结后 `__file__` 落在临时解包目录，数据会写到错误位置并在退出时丢失。
- 阿里云 fun-asr 是**异步文件转写**：它通过 `PUBLIC_BASE_URL` 回源拉取 `/api/recordings/{id}/audio`。云端访问不到桌面端的 `127.0.0.1`，开发期靠 localtunnel，打包后没有现成公网地址。
- 真实依赖、hidden imports、端口、日志、密钥落盘都还没有针对打包场景核对过。

本 change **只做就绪审计（readiness audit）与迁移设计**，不打包真实后端、不替换 hello-backend sidecar、不动 Tauri 现有链路、不动业务代码。目的是把"真实后端能不能、怎么样、分几步进 sidecar"写成可评审的方案，作为 P4–P8 的输入。

## What Changes

- 新增 OpenSpec change：`real-backend-sidecar-readiness`。
- 输出真实后端结构清单（入口、模块、路由、依赖）。
- 输出依赖审计与 PyInstaller 打包风险（hidden imports、pydantic_core、sqlite dialect、uvicorn[standard] 动态导入）。
- 输出桌面端数据目录方案（db / audio / exports / logs / config）。
- 输出配置与密钥方案（dev `.env` → 桌面端 config 文件/keychain）。
- 明确阿里云 ASR 公网 URL 风险与正式方案候选（OSS 签名 URL / 本地 FunASR / 支持上传的 provider）。
- 输出真实后端 PyInstaller 打包计划与独立入口 `backend/desktop_entry.py` 设计（本次不实现）。
- 输出从 hello-backend sidecar 平滑迁移到 real-backend sidecar 的分阶段路线（P3–P8）。
- 新增只读检查脚本 `scripts/check_backend_packaging_readiness.py`（不修改任何东西）。
- 新增可读审计文档 `docs/real-backend-sidecar-readiness.md`。
- 补充 `.gitignore`，预防真实后端 PyInstaller 产物入库。

## Capabilities

### New Capabilities

- `real-backend-sidecar-readiness`：真实业务后端的 sidecar 打包就绪审计、数据/配置/密钥落盘设计、ASR 公网 URL 风险结论、PyInstaller 打包计划、分阶段迁移路线。

### Modified Capabilities

- 无。本阶段不改任何业务能力、不改 Tauri sidecar、不改前端 UI。

## Impact

- Docs：新增 OpenSpec change（proposal/design/spec/tasks）+ `docs/real-backend-sidecar-readiness.md`。
- Scripts：新增 1 个**只读** readiness 检查脚本。
- Code：**不改业务代码**（Python / Rust / 前端均不动）。允许仅 `.gitignore` 追加忽略规则。
- DB / storage / ASR / LLM provider：**不变**。
- 现有 Web dev、Tauri dev、hello-backend sidecar 链路、`scripts/dev-all.sh`：**不受影响**。
- Risks：本阶段不引入运行风险；真正风险在 P4 之后（数据目录重构、frozen 路径、ASR 公网 URL）。
