# 后端

游戏语音 AI 分析工具的 FastAPI 后端。

本项目配置为使用 Python 3.11 和 SQLite。音频上传与播放相关的最小闭环已按 `openspec/changes/audio-upload-playback/` 实现。

## 本地启动

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## 阿里云 ASR 配置

后端会读取项目根目录 `.env` 或 `backend/.env`，也可以直接使用 shell 环境变量。不要提交真实 `.env`。

```bash
ASR_PROVIDER=aliyun
DASHSCOPE_API_KEY=replace-with-your-dashscope-key
ALIYUN_ASR_MODEL=fun-asr
ALIYUN_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
PUBLIC_BASE_URL=http://127.0.0.1:8000
```

`PUBLIC_BASE_URL` 需要是阿里云可以访问的后端公网地址。本地开发可用 ngrok、localtunnel 或 Cloudflare Tunnel 暴露 `http://127.0.0.1:8000`，再把公网地址填入 `PUBLIC_BASE_URL`。

## AI 总结 LLM 配置

默认 `LLM_PROVIDER=mock`，用于不调用真实大模型的本地流程验证。要让“生成 AI 总结”调用阿里云百炼 / DashScope，请配置：

```bash
LLM_PROVIDER=mock
DASHSCOPE_LLM_MODEL=qwen-plus
DASHSCOPE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_REQUEST_TIMEOUT_SECONDS=60
```

真实调用时把 `LLM_PROVIDER` 改为 `dashscope`，并确保 `DASHSCOPE_API_KEY` 已配置：

```bash
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=replace-with-your-dashscope-key
DASHSCOPE_LLM_MODEL=qwen-plus
DASHSCOPE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

如果 `LLM_PROVIDER=dashscope` 但缺少 `DASHSCOPE_API_KEY`，接口会返回清晰错误，不会自动退回 mock。

## 数据与文件位置

- SQLite：`backend/recordings.sqlite3`
- 上传音频：`storage/audio/`

## 当前接口

- `POST /api/recordings/upload`：上传音频文件。
- `POST /api/recordings`：上传音频文件的兼容入口。
- `GET /api/recordings`：获取录音列表。
- `GET /api/recordings/{id}`：获取单条录音详情。
- `GET /api/recordings/{id}/audio`：访问录音音频文件。
- `GET /api/recordings/{id}/segments`：获取录音转写时间轴。
- `POST /api/recordings/{id}/segments/mock`：生成 mock 转写。
- `POST /api/recordings/{id}/transcribe`：调用当前 ASR provider 生成转写。
- `POST /api/recordings/{id}/analyze`：调用当前 LLM provider 生成 AI 总结。
- `GET /api/recordings/{id}/analysis`：获取已保存的 AI 总结。
