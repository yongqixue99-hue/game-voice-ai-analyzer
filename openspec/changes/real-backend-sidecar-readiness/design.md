# real-backend-sidecar-readiness — 设计与审计

> 本文是 P3 的核心交付物：对真实业务后端（`backend/app`）能否被 PyInstaller 打成 Tauri sidecar 做就绪审计，并给出最小迁移设计。**本阶段不实现、不打包、不改业务代码。**

## 1. Goal

回答"真实后端能不能、怎么样、分几步进 sidecar"，输出：结构清单、依赖与打包风险、数据目录方案、配置/密钥方案、ASR 公网 URL 结论、PyInstaller 打包计划、hello→real 迁移路线、验收标准、范围外事项、风险权衡、任务清单。

## 2. Background

- P2 已用 `experiments/hello-backend` 打通 sidecar 全链路（PyInstaller onefile → Tauri externalBin → Rust spawn/kill/status → 前端按钮 → 真机验证）。
- hello-backend 极简：单文件、零业务依赖、`LUNARIS_PORT` 读端口、`/api/health` 返回 ok。
- 真实后端是多模块 FastAPI 应用，带 SQLite、文件存储、阿里云 ASR、LLM provider。直接套用 hello 的打包方式会撞上路径、依赖、ASR 回源三类问题。
- 已有前序设计 `tauri-prod-backend-launch-design`（高层方案：sidecar+PyInstaller、数据落 App Support、动态端口、keychain）。本 change 把它**落到真实后端代码层面**核实。

## 3. Current Backend Inventory

### 3.1 入口
- 启动方式：`uvicorn app.main:app --reload --port 8000`（见 `scripts/dev-all.sh`）。
- `backend/app/main.py`：构造 `FastAPI(...)`，`lifespan` 内 `settings.audio_storage_dir.mkdir(...)` + `init_db()`，挂 CORS（允许 localhost:3000 与 `tauri://localhost` 等），暴露 `/health` 与 `/api/health`，注册 6 个 router。
- **没有 `if __name__ == "__main__"` / 没有 `uvicorn.run(...)` 调用**。入口是"模块字符串 `app.main:app`"，由外部 uvicorn CLI 驱动。
  - ⇒ PyInstaller 需要一个**独立脚本入口**（见 §8.3 `desktop_entry.py`），不能直接冻结 `app.main`。

### 3.2 模块与路由
| 模块 | 职责 |
|---|---|
| `app/main.py` | FastAPI app、CORS、health、router 注册、lifespan |
| `app/config.py` | `Settings` dataclass + `get_settings()` + 手写 `.env` 解析 |
| `app/database.py` | SQLAlchemy engine/session、`init_db()`、轻量 schema 迁移（ALTER TABLE） |
| `app/models.py` | SQLAlchemy ORM 模型（Recording / TranscriptSegment / SpeakerLabel / RecordingSession / RecordingSessionChunk / RecordingAnalysis 等） |
| `app/recordings.py` | 上传/保存音频、`FileResponse` 提供 `/api/recordings/{id}/audio` |
| `app/recording_sessions.py` | 长录音分段会话 |
| `app/segments.py` | transcript segment、speaker label |
| `app/transcriptions.py` | 触发 ASR、写入 segment |
| `app/session_summaries.py` | 整场总结 |
| `app/analyses.py` | LLM 分析/总结 |
| `app/asr.py` | 阿里云 fun-asr provider（urllib 实现，异步文件转写 + 回源 URL） |
| `app/llm.py` | LLM provider（mock / dashscope / openai，urllib 实现） |

### 3.3 数据/文件接触点
- SQLite 文件：`DATABASE_URL` 默认 `sqlite:///{project_root}/backend/recordings.sqlite3`。
- 音频目录：`AUDIO_STORAGE_DIR` 默认 `{project_root}/storage/audio`，用 `FileResponse` 直出（**非** StaticFiles mount）。
- `project_root = Path(__file__).resolve().parents[2]`（= 仓库根）。**这是 frozen 下的头号阻塞点。**

## 4. Dependency Audit

### 4.1 声明 vs 实际
`backend/pyproject.toml` 声明的运行时依赖：
```
fastapi, python-multipart, sqlalchemy, uvicorn[standard]   （dev: httpx, pytest）
```
对 `backend/app/*.py` 的 import 实测（去掉本地包/标准库后）只有：
```
fastapi, pydantic, sqlalchemy           # 第三方
urllib(.request/.parse/.error), json, mimetypes, logging, os, re, time, uuid, datetime, pathlib, dataclasses, typing, collections, contextlib   # 全部标准库
```
**关键结论：**
- ASR 与 LLM 的 HTTP 调用**全部用标准库 `urllib`**，没有 `requests`/`httpx`/`openai`/`dashscope` SDK。⇒ 打包时**无需 bundle 任何 ASR/LLM SDK**，少一大类 hidden import 与体积。
- `httpx` 只在测试用（dev 依赖），生产不需要。
- 没有 `subprocess`/`ffmpeg`/`pydub`/`numpy`/`torch`/`soundfile` —— **纯 Python 音频透传**（原样存、原样发），不依赖任何外部二进制。

### 4.2 实际需进包的第三方传递依赖（取自 `backend/.venv`）
```
fastapi, starlette, pydantic, pydantic_core(*编译扩展), sqlalchemy,
uvicorn, click, h11, anyio, sniffio, idna, typing_extensions,
annotated_types, typing_inspection, python_multipart
```
uvicorn[standard] 额外带：`uvloop, httptools, watchfiles, websockets, python-dotenv(dotenv), pyyaml` —— **生产 sidecar 可不要**（无需 reload/uvloop/ws），见 §8.2。

### 4.3 PyInstaller 风险点（针对真实后端）
1. **pydantic v2 → `pydantic_core` 是编译的 Rust 扩展**。PyInstaller 有官方 hook，通常能收，但需在 spike 中验证 `.so` 被正确打入。
2. **SQLAlchemy sqlite 方言按字符串延迟导入**：`create_engine("sqlite:///...")` 触发 `sqlalchemy.dialects.sqlite` + DBAPI（stdlib `sqlite3`）。需 hidden import `sqlalchemy.dialects.sqlite`（PyInstaller 的 sqlalchemy hook 一般已覆盖，需验证）。
3. **uvicorn 动态导入**：lifespan / 协议 / loop 实现按字符串加载，与 hello-backend 同款，需要：
   `uvicorn.lifespan.on`, `uvicorn.lifespan.off`, `uvicorn.protocols.http.h11_impl`, `uvicorn.loops.asyncio`（生产可不带 websockets 协议）。
4. **FastAPI/Starlette 的多部分上传**：依赖 `python-multipart`（已声明），需确认其顶层包名 `multipart` 被收入。
5. **router 是静态 `from .xxx import router`**：app 依赖图静态可达，PyInstaller 能跟到大部分业务模块；但仍建议在 spec 用 `--collect-submodules app` 兜底。
6. **相对路径假设**（§5）：`__file__`/CWD 在 frozen 下不可靠，必须改为数据目录注入。
7. **mimetypes**：依赖系统 mime 数据库；打包后行为基本一致（stdlib），低风险。

## 5. Data Directory Plan

### 5.1 目标目录（按平台）
| 平台 | 根目录 |
|---|---|
| macOS | `~/Library/Application Support/LUNARIS/` |
| Windows | `%APPDATA%/LUNARIS/` |
| Linux | `~/.local/share/LUNARIS/` |

子目录：
```
LUNARIS/
  db/        recordings.sqlite3
  audio/     上传/录音音频
  exports/   导出（预留）
  logs/      后端日志
  config/    config.json（非密钥配置）
```

### 5.2 注入方式（最小改动）
- Tauri 端**已经**有 `LUNARIS_DATA_DIR`（`main.rs::get_runtime_info` 已读取并上报）。P5 让 `start_backend` 把它注入 sidecar 环境。
- 后端 `config.py` 的 `get_settings()` 增加一层"数据根目录解析"（P4）：
  - 若存在 `LUNARIS_DATA_DIR` → db=`$ROOT/db/recordings.sqlite3`、audio=`$ROOT/audio`、logs=`$ROOT/logs`。
  - 否则保持现状（`project_root` 相对路径）——**保证 Web dev 不受影响**。
  - 仍尊重既有的显式 `DATABASE_URL` / `AUDIO_STORAGE_DIR` 覆盖。
- **不在本 change 实现**；这里只定义解析优先级：`显式 env > LUNARIS_DATA_DIR > 源码树相对路径`。

### 5.3 数据迁移
- 旧的仓库内 `backend/recordings.sqlite3` 与 `storage/audio` 是否迁移到新数据目录 —— **不在本 change 处理**，留待专门决策（见末尾"需要决策"）。

## 6. Config / Secrets Plan

- **开发环境**：维持现状。`config.load_env_file` 从 `项目根/.env` 与 `backend/.env` 读取（手写解析，不依赖 python-dotenv）。
- **桌面端生产**：
  - 非密钥配置 → `LUNARIS/config/config.json`（端口、provider 选择、轮询参数等）。
  - 密钥（`DASHSCOPE_API_KEY` / `OPENAI_API_KEY`）→ **后续接 OS keychain**（macOS Keychain / Windows Credential Manager），过渡期可放 `config/`（仅本机、文件权限收紧）。
- **硬约束**：
  - API Key 不写进代码、不进 git（现状已满足：全部 `os.getenv`，无 `.env` 入库，仅 `.env.example`）。
  - 前端不持有完整 key；前端只通过本地后端调用，key 留在后端进程。
- 解析优先级建议：`keychain（后续） > config.json > 环境变量/.env`。

## 7. ASR Public URL Risk

**这是真实后端进 sidecar 的最大功能风险，必须显式标注。**

- 现状（`asr.py`）：阿里云 fun-asr 是**异步文件转写**——提交任务时给阿里云一个 `file_url = {PUBLIC_BASE_URL}/api/recordings/{id}/audio`，由**阿里云云端反向回源**下载音频再转写。
- 桌面端即使后端在本机运行，`PUBLIC_BASE_URL` 默认 `http://127.0.0.1:8000`，**阿里云云端访问不到用户机器的 127.0.0.1**。开发期靠 localtunnel（P2 日志里的 `*.loca.lt`）才暂时可用，而它正是那条 `FILE_DOWNLOAD_FAILED / 502` 的根因（隧道地址不可达/过期）。
- ⇒ **打包成桌面 App 后，ASR 不能依赖 localtunnel**。正式方案需三选一（后续 change 决策）：
  1. **OSS 临时签名 URL**：音频先传对象存储，给阿里云一个有时效的签名 URL（本 change 明确**不引入 OSS**，仅记录为候选）。
  2. **本地 FunASR**：本机模型推理，无需公网回源（体积/性能成本高）。
  3. **支持直接文件上传的 ASR provider**：传文件体而非回源 URL。
- 开发期可继续 localtunnel，但**不是正式方案**。本 change 不改 ASR，只锁定结论。

## 8. PyInstaller Packaging Plan（设计，不实现）

### 8.1 不重用 hello 的 onefile？
- hello-backend 用 onefile（bootloader fork 出 server 子进程，P2 已发现需 SIGTERM 才能优雅停）。真实后端建议优先评估 **onedir**：启动更快、无临时解包、`__file__` 行为更接近源码树；代价是产物是目录（Tauri externalBin 期望单文件，需在 P6/P7 评估打包/压缩策略）。两者都在 P6 spike 比较。

### 8.2 生产精简
- 用 `uvicorn.run(app, loop="asyncio", ...)` 而非 `[standard]` 全家桶；`--reload`/uvloop/watchfiles/websockets 在生产 sidecar 不需要，能排除以减体积、减 hidden import 面。

### 8.3 独立入口 `backend/desktop_entry.py`（设计草案，本次不写）
```python
# 仅设计示意，本 change 不实现
import os
from app.main import app  # 静态导入，PyInstaller 可跟踪
import uvicorn

def main() -> None:
    host = os.environ.get("LUNARIS_HOST", "127.0.0.1")
    port = int(os.environ.get("LUNARIS_PORT", "0")) or 8000
    uvicorn.run(app, host=host, port=port, log_level="warning")

if __name__ == "__main__":
    main()
```
- 与 hello-backend 的端口/host 约定一致（`LUNARIS_PORT`/`LUNARIS_HOST`），便于 Rust 端复用现有 `start_backend` 注入逻辑。
- 数据目录解析（§5.2）应在 import app 之前确保 `LUNARIS_DATA_DIR` 已在环境里。

### 8.4 spec 草案要点（P6）
- `hiddenimports`: `sqlalchemy.dialects.sqlite`, `uvicorn.lifespan.on/off`, `uvicorn.protocols.http.h11_impl`, `uvicorn.loops.asyncio`。
- `--collect-submodules app`（兜底业务模块）、`--collect-all pydantic`（验证 pydantic_core）。
- 验证：打包产物能 `init_db()` 写到注入的数据目录、能上传与回放音频、`/api/health` 正常。

## 9. Sidecar Migration Plan（hello → real）

| 阶段 | change | 内容 | 本 change 是否做 |
|---|---|---|---|
| **P3** | `real-backend-sidecar-readiness` | 就绪审计 + 迁移设计（本文） | ✅ 本次 |
| P4 | desktop data directory refactor | `config.py` 支持 `LUNARIS_DATA_DIR` 解析（dev 行为不变） | ❌ |
| P5 | real backend desktop entry | 新增 `backend/desktop_entry.py` + 数据目录注入；可选只读 `/api/system/config` 用于核验 | ❌ |
| P6 | real backend PyInstaller spike | 在 `experiments/` 打包真实后端，验证 hidden imports / pydantic_core / sqlite / 数据目录 | ❌ |
| P7 | Tauri sidecar 替换 | externalBin 从 hello-backend 换成 real-backend，沿用现有 spawn/kill/status | ❌ |
| P8 | production build spike | 端到端打包 + ASR 公网 URL 正式方案落地 | ❌ |

平滑性保证：每一步都保持 Web dev 与现有 Tauri+hello sidecar 链路可用；real backend 就绪并验证后，P7 才切换 externalBin（一行配置 + 二进制名），Rust/前端逻辑不变。

## 10. Acceptance Criteria

1. 已创建 `real-backend-sidecar-readiness` OpenSpec change（proposal/design/spec/tasks）。
2. 已输出真实后端结构清单（§3）。
3. 已输出依赖清单与打包风险（§4）。
4. 已输出数据目录方案（§5）。
5. 已输出配置与密钥方案（§6）。
6. 已明确阿里云 ASR 公网 URL 风险与候选方案（§7）。
7. 已输出 PyInstaller 真实后端打包计划与独立入口设计（§8）。
8. 已输出 hello→real sidecar 迁移步骤（§9）。
9. **未**直接打包真实后端、**未**修改 Tauri 现有 hello-backend 链路、**未**破坏 Web/Tauri dev、**未**提交敏感文件。
10. 新增的检查脚本为**只读**，不修改任何文件/数据库/环境。

## 11. Out of Scope

不做：直接 PyInstaller 打包真实后端；替换 hello sidecar；改 Tauri sidecar 指向；迁移数据库；迁移 `storage/audio`；重构 ASR/LLM provider；改前端 UI；系统声音录制；托盘；悬浮窗；生产安装包；引入 OSS；提交任何 API Key / `.env`。

## 12. Risks / Trade-offs

| 风险 | 说明 | 缓解 |
|---|---|---|
| frozen 路径 | `parents[2]` 在 PyInstaller 下指向临时解包目录，数据写错位置/丢失 | P4 数据目录解析层，注入 `LUNARIS_DATA_DIR` |
| ASR 回源 | 阿里云云端访问不到本机 127.0.0.1，localtunnel 非正式方案 | P8 决策 OSS 签名 URL / 本地 FunASR / 上传式 provider |
| pydantic_core | 编译扩展可能未被正确收入 | P6 spike 用 `--collect-all pydantic` 验证 |
| onefile vs onedir | onefile 冷启动慢 + 子进程孤儿化（P2 已遇）；onedir 是目录不便做 externalBin | P6 两者对比 |
| 端口 8000 硬默认 | 桌面端多实例/占用冲突 | 沿用 `LUNARIS_PORT`，生产动态端口 |
| 密钥落盘 | 过渡期 key 落 config 文件有泄露面 | 收紧文件权限，后续接 keychain；前端不持 key |

## 13. Task List

见 `tasks.md`。
