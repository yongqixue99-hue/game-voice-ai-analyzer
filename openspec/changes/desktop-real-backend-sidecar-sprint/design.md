# Design — desktop-real-backend-sidecar-sprint

> 最短路径设计。完整审计见 P3 `real-backend-sidecar-readiness/design.md`，本文不重复。

## 目标

让 Tauri 能启动真实 FastAPI 后端（`backend/app`）作为 sidecar，而不破坏现有 hello-backend 链路、不破坏 Web/Tauri dev。

## 范围

P4+P5+P6+P7 合并推进。P7 以 P6 成功为前提。

## 数据目录策略（P4）

解析优先级（保证 dev 不变）：

1. 显式 env：`DATABASE_URL` / `AUDIO_STORAGE_DIR`（最高优先，原样沿用）。
2. `LUNARIS_DATA_DIR`：作为数据根，派生
   - `lunaris.sqlite3`（DB）
   - `audio/`（音频）
   - `exports/` `logs/` `config/`（建目录）
3. 都没有：源码树相对路径（现状：`backend/recordings.sqlite3`、`storage/audio`）。

新增 `backend/app/paths.py` 集中解析；`config.py` 调用它。不迁移旧库与旧音频。

## 桌面入口（P5）

`backend/desktop_entry.py`：

- 读 `LUNARIS_DATA_DIR` / `LUNARIS_HOST`(默认 127.0.0.1) / `LUNARIS_PORT`(默认 18080，避开 dev 8000)。
- 初始化数据目录（mkdir db/audio/exports/logs/config）。
- `from app.main import app` + `uvicorn.run(app, host, port, log_level="info")`。
- frozen（PyInstaller）下把 `backend/` 加入 `sys.path`，源码运行时也兼容。

## PyInstaller（P6）

- `backend/build-desktop-backend.sh`：用带 pyinstaller 的解释器，调用 `.spec` 或 `pyinstaller` CLI。
- hidden imports 最小集：`sqlalchemy.dialects.sqlite`、`uvicorn.lifespan.{on,off}`、`uvicorn.protocols.http.h11_impl`、`uvicorn.loops.asyncio`、`pydantic`/`pydantic_core`（`--collect-all pydantic`）、`python-multipart`（`multipart`）、`--collect-submodules app`。
- 产物落 `backend/dist`、`backend/build`，均已 gitignore；`.spec` 入库。
- 失败不大改，记录原因与下一步。

## Tauri 接入（P7，条件性）

- 保留 `externalBin: binaries/lunaris-hello-backend`，新增 `binaries/lunaris-real-backend`。
- Rust 增加 real-backend 启停（端口 18080），或扩展现有命令支持 mode。
- 设置页显示真实后端状态/按钮，不大改 UI。
- 关闭时 SIGTERM 停止（沿用现有 onefile 孤儿进程处理）。

## 风险

- pydantic_core / sqlite dialect / uvicorn 动态导入若漏 hidden import → 打包后启动即崩；靠 spec 显式补。
- onefile 冷启动慢 + 子进程孤儿化（P2 已遇），沿用 SIGTERM 方案。
- 真实后端依赖比 hello 重（sqlalchemy/pydantic_core/multipart），二进制体积与冷启动更大。
- ASR 公网 URL 未解决：桌面端 127.0.0.1 云端访问不到，本次不处理。

## 验收标准

1. 无 `LUNARIS_DATA_DIR` 时 dev 行为不变。
2. 有 `LUNARIS_DATA_DIR` 时 db/audio/exports/logs 落该目录。
3. `python backend/desktop_entry.py` 启动真实后端，`/api/health` 返回 ok。
4. PyInstaller 能尝试打包；成功则产物独立运行 `/api/health` ok，失败则记录原因。
5. P6 成功则 Tauri 能启动真实 sidecar；hello-backend 链路未破坏。
6. `npm run lint`/`build` 通过；backend `pytest` 通过。

## 当前结果

见 `tasks.md` 勾选状态与本次会话末尾的完成报告。
