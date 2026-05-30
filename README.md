# LUNARIS · 游戏语音 AI 分析工具

把一局游戏的语音录下来，自动转写成带说话人和时间轴的文字，再用大模型生成一份复盘总结。

LUNARIS 由三部分组成：一个 **FastAPI + SQLite** 后端、一个 **Next.js + React** 前端，以及把两者打包成本机应用的 **Tauri 桌面壳**。语音识别（ASR）和 AI 总结都做了 provider 抽象，本地用 mock 就能跑通完整链路，无需任何外部服务或密钥。

> 当前定位：**内部桌面 Beta 候选**（本机 macOS aarch64，未签名 / 未公证）。核心链路已在真实后端 sidecar 上跑通，详见 `docs/desktop-beta-status.md`。

---

## 功能概览

- **音频上传与播放**：上传录音，前端时间轴播放、点击跳转。
- **语音转写**：统一输出「说话人 / 起止时间 / 文本 / 来源」的转写片段，支持转写编辑。
- **AI 总结**：把转写交给大模型，生成复盘要点，可导出。
- **录制会话**：支持分段录制与会话级总结。
- **多 ASR Provider**：`mock` / `aliyun` / `funasr_http` 自由切换，设置页实时显示当前 provider 与连接状态。
- **桌面端**：Tauri 把前端 + Python 后端打包为单个 `LUNARIS.app`，进程生命周期自管理。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 16、React 19、TypeScript、Tailwind CSS 4 |
| 桌面壳 | Tauri 2（Rust） |
| 后端 | Python 3.11、FastAPI、SQLAlchemy、Uvicorn、SQLite |
| ASR | mock / 阿里云 DashScope / FunASR HTTP |
| LLM | mock / 阿里云 DashScope（通义千问） |

---

## 目录结构

```
backend/    FastAPI 后端（app/ 为接口与业务，tests/ 为测试，含桌面打包脚本）
frontend/   Next.js 前端 + src-tauri/ 桌面壳
scripts/    dev-all.sh 一键启动、冒烟检查等脚本
docs/       Beta 状态、ASR provider、端到端测试等文档
openspec/   变更规格（spec-driven 开发记录）
storage/    上传音频存放目录（音频文件不入库）
```

---

## 快速开始

前置依赖：**Python 3.11**、**Node.js 20+**、**Rust 工具链**（仅桌面端需要）。

### 1. 后端

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload   # 默认 http://127.0.0.1:8000
```

默认 `ASR_PROVIDER=mock`、`LLM_PROVIDER=mock`，不调用任何外部服务即可跑通完整链路。

### 2. 前端

```bash
cd frontend
npm install
npm run dev                     # 默认 http://127.0.0.1:3000
```

### 3. 一键启动（后端 + 前端 + Tauri dev）

```bash
./scripts/dev-all.sh            # Ctrl+C 一并清理三个子进程
```

---

## 配置

后端读取项目根目录 `.env` 或 `backend/.env`（桌面端为数据目录下的 `config/.env`）。
**请勿提交真实 `.env`**，仓库只包含 `.env.example` 示例。

切换 ASR / LLM provider 后重启后端即可生效。完整说明见 [`docs/asr-providers.md`](docs/asr-providers.md) 与 [`backend/README.md`](backend/README.md)。

```env
# ASR：mock（默认，无需外部服务）/ aliyun（需公网音频 URL）/ funasr_http（本地直传）
ASR_PROVIDER=mock

# 用阿里云时：
# ASR_PROVIDER=aliyun
# DASHSCOPE_API_KEY=替换为你的密钥
# PUBLIC_BASE_URL=https://你的公网可达地址

# AI 总结：mock（默认）/ dashscope（真实大模型）
LLM_PROVIDER=mock
```

---

## 主要接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/recordings/upload` | 上传音频文件 |
| GET | `/api/recordings` | 录音列表 |
| GET | `/api/recordings/{id}` | 录音详情 |
| GET | `/api/recordings/{id}/audio` | 访问音频文件 |
| GET | `/api/recordings/{id}/segments` | 转写时间轴 |
| POST | `/api/recordings/{id}/transcribe` | 调用当前 ASR provider 转写 |
| POST | `/api/recordings/{id}/analyze` | 调用当前 LLM provider 生成总结 |
| GET | `/api/recordings/{id}/analysis` | 获取已保存的总结 |

---

## 测试

```bash
cd backend && source .venv/bin/activate && pytest
```

桌面端 Beta 冒烟检查：`./scripts/desktop_beta_smoke_check.sh`。

---

## 文档

- [`docs/desktop-beta-status.md`](docs/desktop-beta-status.md) — 桌面端 Beta 当前状态
- [`docs/asr-providers.md`](docs/asr-providers.md) — 三种 ASR provider 详解
- [`docs/manual-e2e-test.md`](docs/manual-e2e-test.md) — 手动端到端测试流程
- [`docs/desktop-beta-known-issues.md`](docs/desktop-beta-known-issues.md) — 已知限制
