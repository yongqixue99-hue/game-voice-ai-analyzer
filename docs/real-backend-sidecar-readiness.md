# 真实后端 Sidecar 打包就绪审计（P3）

> 配套 OpenSpec change：`openspec/changes/real-backend-sidecar-readiness/`（完整设计见其中 `design.md`）。
> 本阶段**只做审计与设计**，不打包真实后端、不替换 hello-backend sidecar、不改业务代码。
> 自助核对：`backend/.venv/bin/python scripts/check_backend_packaging_readiness.py`（只读）。

## 一句话结论

真实后端**结构上适合**打成 sidecar（依赖很轻、纯 urllib、无外部二进制），但有 **3 个必须先解决的阻塞点**：①frozen 下的相对路径假设；②阿里云 ASR 的公网回源 URL；③一个独立打包入口。建议按 P4→P8 分步推进，先不动现有链路。

## 后端结构清单

- 入口：`uvicorn app.main:app`（无 `__main__`，无 `uvicorn.run`）。
- 模块：`main / config / database / models / recordings / recording_sessions / segments / transcriptions / session_summaries / analyses / asr / llm`，6 个 router。
- 数据接触点：SQLite `sqlite:///{project_root}/backend/recordings.sqlite3`；音频 `{project_root}/storage/audio`（`FileResponse` 直出）；`project_root = Path(__file__).parents[2]`。

## 依赖与打包风险

- **真实第三方运行时依赖只有**：`fastapi / pydantic(+pydantic_core) / sqlalchemy / uvicorn`（+ uvicorn[standard] 附带项，生产可精简）。
- ASR/LLM **全部用标准库 `urllib`**，无 `requests/httpx/openai/dashscope` SDK；无 `ffmpeg/pydub/numpy/torch`（纯 Python 音频透传）。
- PyInstaller 风险：`pydantic_core` 编译扩展、`sqlalchemy.dialects.sqlite` 字符串延迟导入、`uvicorn` 协议/loop/lifespan 动态导入、`__file__` 路径假设。

## 数据目录方案

桌面端统一数据根（macOS `~/Library/Application Support/LUNARIS/`，Win `%APPDATA%/LUNARIS/`，Linux `~/.local/share/LUNARIS/`），下设 `db/ audio/ exports/ logs/ config/`。
解析优先级：**显式 env（DATABASE_URL/AUDIO_STORAGE_DIR）> LUNARIS_DATA_DIR > 源码树相对路径**（保证 Web dev 不变）。Tauri 端已有 `LUNARIS_DATA_DIR`，P5 注入即可。

## 配置 / 密钥

- dev：维持 `.env`（手写解析，无 python-dotenv 依赖）。
- 桌面端：非密钥 → `config/config.json`；密钥 → 后续 OS keychain，过渡期落 `config/` 并收紧权限。
- 硬约束：key 不入代码、不入 git（现状已满足，仅 `.env.example` 入库）、前端不持完整 key。

## 阿里云 ASR 公网 URL 风险（重点）

阿里云 fun-asr 是**异步文件转写**：给云端一个 `{PUBLIC_BASE_URL}/api/recordings/{id}/audio` 让其**回源下载**。桌面端 `127.0.0.1` 云端访问不到——开发期靠 localtunnel（脚本已探测到当前为 `*.loca.lt`，也是 P2 那条 `FILE_DOWNLOAD_FAILED/502` 的根因）。
正式方案三选一（后续决策，本次不引入 OSS）：**OSS 临时签名 URL** / **本地 FunASR** / **支持直接文件上传的 ASR provider**。

## PyInstaller 打包计划（设计，不实现）

- 新增独立入口 `backend/desktop_entry.py`：静态 `from app.main import app` + `uvicorn.run(app, loop="asyncio", ...)`，端口/host 沿用 `LUNARIS_PORT`/`LUNARIS_HOST`。
- 生产精简（不带 reload/uvloop/watchfiles/websockets）。
- spec 要点：hidden imports（见脚本输出）+ `--collect-submodules app` + `--collect-all pydantic`。
- onefile vs onedir 在 P6 spike 对比（onefile 冷启动慢且子进程孤儿化，P2 已遇）。

## hello → real 迁移路线

| 阶段 | 内容 |
|---|---|
| **P3（本次）** | 就绪审计 + 迁移设计 |
| P4 | 数据目录重构（`config.py` 支持 `LUNARIS_DATA_DIR`，dev 不变） |
| P5 | `backend/desktop_entry.py` + 数据目录注入 |
| P6 | 真实后端 PyInstaller spike（在 `experiments/`） |
| P7 | Tauri externalBin 由 hello-backend 切换为 real-backend |
| P8 | 生产 build + ASR 公网 URL 正式方案 |

## 需要你决策的开放问题

1. ASR 正式方案选哪条（OSS 签名 URL / 本地 FunASR / 上传式 provider）？
2. 旧的仓库内 `recordings.sqlite3` 与 `storage/audio` 是否迁移到新数据目录、如何迁移？
3. onefile 还是 onedir？
4. keychain 何时接入（P5 过渡期落 config 文件可接受否）？
