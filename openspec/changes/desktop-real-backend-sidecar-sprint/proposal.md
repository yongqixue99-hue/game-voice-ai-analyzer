# desktop-real-backend-sidecar-sprint

## Why

P3（`real-backend-sidecar-readiness`）已经把真实后端进 sidecar 的阻塞点查清并写成方案：①frozen 下 `__file__` 路径假设；②阿里云 ASR 公网回源 URL；③缺独立打包入口。hello-backend sidecar 链路在 P2 已跑通。

现在不再把 P4/P5/P6/P7 拆细，而是合并成一次冲刺，用**最短路径**验证真实 FastAPI 后端能否被 Tauri 当作 sidecar 启动。少写长文档，多做实现与验证。

## What Changes

- **P4 数据目录**：新增 `backend/app/paths.py`，`config.py` 接入 `LUNARIS_DATA_DIR`。无该 env 时 dev 行为完全不变；有该 env 时 db/audio/exports/logs 落到该根目录。不迁移现有数据。
- **P5 桌面入口**：新增 `backend/desktop_entry.py`，读取 `LUNARIS_DATA_DIR/HOST/PORT`（默认 `127.0.0.1:18080`），初始化数据目录，`uvicorn.run(app.main:app)`，`/api/health` 可访问。
- **P6 PyInstaller spike**：新增 `backend/build-desktop-backend.sh` + 保留 `.spec`，把 `desktop_entry.py` 打成当前平台可执行文件，修最小 hidden imports。产物（dist/build）不入库。
- **P7 Tauri 接入**（仅 P6 成功后）：保留 hello-backend sidecar 作 fallback，新增 real-backend sidecar 与 Rust 启停命令，设置页显示真实后端状态。
- ASR 公网 URL 本次只记录、不引入 OSS、不解决。

## Capabilities

### New Capabilities

- `desktop-real-backend-sidecar`：以 `LUNARIS_DATA_DIR` 为数据根、`desktop_entry.py` 为入口、PyInstaller 打包的真实后端 sidecar，可由 Tauri 启停（hello-backend 保留为 fallback）。

### Modified Capabilities

- 无业务能力变更。`config.py` 仅在 `LUNARIS_DATA_DIR` 存在时改变路径解析；现有 Web/Tauri dev 不受影响。

## Impact

- 后端：新增 `app/paths.py`、`desktop_entry.py`、`build-desktop-backend.sh`、`*.spec`；`config.py` 最小改动。
- 前端/Tauri：P7 成功时 `main.rs`、`tauri.conf.json`、设置页改动；否则不动。
- 不做：系统声音录制、混录、托盘、悬浮窗、开机启动、FunASR、OSS、安装包、签名、登录/支付，不大规模重构。
