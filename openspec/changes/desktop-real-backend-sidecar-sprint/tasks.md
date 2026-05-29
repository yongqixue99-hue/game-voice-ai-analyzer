# Tasks — desktop-real-backend-sidecar-sprint

## 0. 准备

- [x] 0.1 提交 P3 文档成果（commit `完成真实后端 sidecar readiness 分析`）。
- [x] 0.2 创建 change 三文档（proposal/design/tasks）。

## 1. P4 桌面数据目录

- [x] 1.1 新增 `backend/app/paths.py`：按 `DATABASE_URL`/`AUDIO_STORAGE_DIR` > `LUNARIS_DATA_DIR` > 源码相对路径解析。
- [x] 1.2 `config.py` 接入 `paths.py`；无 env 时 dev 行为不变。
- [x] 1.3 验证：无 env → 现状路径；有 `LUNARIS_DATA_DIR` → db/audio/exports/logs 落该目录。

## 2. P5 desktop_entry.py

- [x] 2.1 新增 `backend/desktop_entry.py`：读 env、建数据目录、`uvicorn.run(app.main:app)`、默认端口 18080。
- [x] 2.2 验证：`python backend/desktop_entry.py` 启动，`/api/health` 返回 ok。

## 3. P6 PyInstaller spike

- [x] 3.1 新增 `backend/build-desktop-backend.sh` + `lunaris-real-backend.spec`（最小 hidden imports）。
- [x] 3.2 打包当前平台真实后端可执行文件（aarch64-apple-darwin，~19MB）。
- [x] 3.3 验证：产物独立运行，`/api/health`、`/api/recordings`、`/openapi.json` 均 ok。
- [x] 3.4 确认 `.gitignore` 忽略 `backend/dist`、`backend/build`；`.spec` 入库。

## 4. P7 Tauri 接入（P6 已成功）

- [x] 4.1 保留 hello-backend sidecar；新增 real-backend sidecar 配置（externalBin）。
- [x] 4.2 Rust 支持启动真实后端 sidecar（start/stop/get_real_backend_status）。
- [x] 4.3 设置页显示真实后端状态/按钮（hello 与 real 两组控制并列）。
- [x] 4.4 关闭时停止真实后端 sidecar（RunEvent::Exit 清理两个 slot）。

## 5. 验收

- [x] 5.1 `npm run lint` 通过（0 error；并为 `src-tauri/target/**` 加 ignore）。
- [x] 5.2 `npm run build` 通过（TypeScript clean + static export）。
- [x] 5.3 backend `pytest` 通过（35 passed）。
- [x] 5.4 hello-backend sidecar 链路未破坏（cargo mock-runtime 测试通过）。
- [x] 5.5 输出完成报告（见本次会话末尾）。

## 6. 记录（不实现）

- [x] 6.1 阿里云 ASR 公网 URL 问题：桌面端 `127.0.0.1` 本地文件云端非实时 ASR 不可达；
      dev 仍用 localtunnel；正式版三选一（OSS 临时签名 URL / 本地 FunASR / 支持直接上传文件的 ASR provider）。
      本次不引入 OSS、不解决。
