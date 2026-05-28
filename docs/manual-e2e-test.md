# MVP 手动端到端验收指南

本文用于手动验收当前 Web MVP 主链路：上传/播放、阿里云 ASR、AI 总结、转写编辑、浏览器录音、分段长录音、整场总结和 Markdown/TXT 导出。

## 1. 环境变量配置

后端会读取项目根目录 `.env` 或 `backend/.env`。不要提交真实 `.env`。

最小配置示例：

```bash
ASR_PROVIDER=aliyun
DASHSCOPE_API_KEY=replace-with-your-dashscope-key
ALIYUN_ASR_MODEL=fun-asr
ALIYUN_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
PUBLIC_BASE_URL=http://127.0.0.1:8000

LLM_PROVIDER=mock
DASHSCOPE_LLM_MODEL=qwen-plus
DASHSCOPE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_REQUEST_TIMEOUT_SECONDS=60
```

真实调用阿里云百炼大模型时：

```bash
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=replace-with-your-dashscope-key
DASHSCOPE_LLM_MODEL=qwen-plus
```

说明：

- `DASHSCOPE_API_KEY` 同时用于阿里云 ASR 和 DashScope LLM。
- `LLM_PROVIDER=mock` 时，AI 总结和整场总结走 mock provider，页面会显示 `mock` 和 mock 模型名。
- `LLM_PROVIDER=dashscope` 但未配置 key 时，后端应返回清晰错误，不应自动 fallback 到 mock。
- 修改 `.env` 后需要重启后端。

## 2. 启动后端

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

检查：

```bash
curl http://127.0.0.1:8000/health
```

期望返回：

```json
{"status":"ok"}
```

## 3. 启动前端

新开终端：

```bash
cd frontend
npm install
npm run dev
```

打开：

```text
http://localhost:3000
```

如果后端不是 `http://127.0.0.1:8000`，在前端启动前配置：

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## 4. 配置 PUBLIC_BASE_URL

阿里云 ASR 需要能从公网访问音频 URL。`PUBLIC_BASE_URL=http://127.0.0.1:8000` 只适合本地页面播放，不适合阿里云拉取文件。

使用 ngrok：

```bash
ngrok http 8000
```

把 ngrok 输出的 HTTPS 地址写入 `.env`：

```bash
PUBLIC_BASE_URL=https://your-id.ngrok-free.app
```

使用 localtunnel：

```bash
npx localtunnel --port 8000
```

把输出的 HTTPS 地址写入 `.env`：

```bash
PUBLIC_BASE_URL=https://your-name.loca.lt
```

改完后重启 FastAPI。若仍看到 `FILE_DOWNLOAD_FAILED`，通常是公网地址不可访问、隧道已断开、或阿里云无法拉取该 URL。

## 5. 上传音频测试流程

1. 打开首页。
2. 关闭“上传/录音完成后自动分析”。
3. 选择一个 `.mp3`、`.wav`、`.m4a` 或 `.webm` 文件。
4. 点击“上传”。
5. 验收：
   - 录音列表出现新录音。
   - 卡片显示文件名、上传时间、状态和大小。
   - audio 播放器可以播放。
   - 刷新页面后录音仍然存在。

## 6. ASR 和 AI 总结测试流程

手动转写：

1. 在录音卡片点击“真实转写（阿里云）”。
2. 等待转写完成。
3. 验收：
   - 时间轴出现 segments。
   - 时间轴显示来源：阿里云 ASR。
   - 点击 segment，播放器跳到对应时间。
   - 播放时当前 segment 高亮。

手动 AI 总结：

1. 点击“生成 AI 总结”。
2. 验收：
   - 页面显示 provider / model。
   - `LLM_PROVIDER=mock` 时显示 mock。
   - `LLM_PROVIDER=dashscope` 时显示 dashscope / qwen-plus。
   - 刷新页面后总结仍然存在。

失败验收：

- 未配置 `DASHSCOPE_API_KEY` 时，应显示缺少 key 的错误。
- `PUBLIC_BASE_URL` 是 localhost/127.0.0.1 时，应提示阿里云无法访问本地音频 URL。
- ASR 失败后，不应继续自动生成 AI 总结。
- AI 总结失败后，已生成的转写应保留。

## 7. 转写编辑和说话人重命名

编辑 segment：

1. 在任意 segment 点击“编辑”。
2. 修改文本并保存。
3. 刷新页面。
4. 验收：
   - 修改后的文本仍然存在。
   - segment 显示“已编辑”。
   - 已有 AI 总结显示“可能不是最新结果”的过期提示。
   - 重新点击“生成 AI 总结”后，过期提示消失。

重命名 speaker/channel：

1. 在“说话人名称”区域，把 `Channel 0` 或 `Speaker 1` 改成“主持人”等名称。
2. 点击“保存名称”。
3. 刷新页面。
4. 验收：
   - 所有对应 segments 显示新名称。
   - 已有 AI 总结提示可能过期。

## 8. 浏览器录音测试流程

1. 点击“开始录音”。
2. 允许浏览器麦克风权限。
3. 说几句话。
4. 点击“暂停”。
5. 点击“继续”。
6. 点击“停止并上传”。
7. 验收：
   - 状态依次变化：请求权限中、录音中、已暂停、录音中、停止中/上传中、上传完成。
   - 录音时长持续更新。
   - 停止后录音列表出现新录音。
   - 新录音可以播放。
   - 开启自动分析时，新录音上传后自动转写并自动总结。

失败验收：

- 拒绝麦克风权限时，应显示“无法访问麦克风，请检查浏览器权限。”。
- 浏览器不支持 MediaRecorder 时，应显示“不支持网页录音”的提示。

## 9. 分段长录音测试流程

建议先用 30 秒分段。

1. 在“长录音会话”区域选择“30 秒（开发测试）”。
2. 点击“开始长录音”。
3. 允许麦克风权限。
4. 持续说话超过 70 秒。
5. 观察 chunks 列表。
6. 点击“停止长录音”。
7. 验收：
   - 页面显示 session 总时长和当前 chunk 序号。
   - 到达 30 秒后自动出现 Chunk 1。
   - 继续录制时出现 Chunk 2、Chunk 3。
   - 每个 chunk 显示录音、上传、转写、总结状态。
   - 某个 chunk 失败时，后续 chunk 仍可继续出现。
   - 失败 chunk 有“重试分析”按钮。
   - 停止后，最后不足 30 秒的 chunk 也会上传。
   - 刷新页面后，历史 session 和 chunks 仍然存在。

## 10. 整场总结和导出测试流程

前提：一个 session 下至少有一个 chunk 已完成转写。建议多个 chunks 都完成 AI 总结。

1. 在 session 卡片的“整场总结”区域点击“生成整场总结”。
2. 验收：
   - 生成中显示“正在生成整场总结...”。
   - 成功后展示标题、整体总结、重点信息、时间线、分段摘要和备注。
   - 页面显示 provider / model。
   - 刷新页面后整场总结仍然存在。
   - 点击时间线或分段摘要，播放器跳转到对应 chunk 的相对时间。
3. 点击“复制 Markdown”。
4. 点击“下载 Markdown”。
5. 点击“下载 TXT”。
6. 验收：
   - Markdown 内容包含标题、整体总结、重点信息、时间线、分段摘要、备注和生成信息。
   - TXT 能正常下载。

过期提示：

1. 重新生成某个 chunk 的 AI 总结，或编辑某个 chunk 的转写。
2. 验收整场总结区域显示：

```text
部分分段内容已更新，整场总结可能不是最新结果，请重新生成。
```

## 11. 常见问题排查

### 页面一直显示加载中

- 确认后端已启动：`curl http://127.0.0.1:8000/health`。
- 确认前端 API 地址：页面加载错误中会显示当前后端地址。
- 如果后端端口不是 8000，设置 `NEXT_PUBLIC_API_BASE_URL` 后重启前端。

### 阿里云 ASR 报 FILE_DOWNLOAD_FAILED

- 检查 `PUBLIC_BASE_URL` 是否为公网 HTTPS 地址。
- 在浏览器直接打开 `${PUBLIC_BASE_URL}/health`。
- 在浏览器直接打开录音音频 URL，确认能下载或播放。
- ngrok/localtunnel 免费隧道可能会断，断开后需要重新配置并重启后端。

### 生成 AI 总结后仍显示 mock

- 检查 `.env` 中 `LLM_PROVIDER` 是否为 `dashscope`。
- 检查 `DASHSCOPE_API_KEY` 是否存在。
- 修改 `.env` 后必须重启后端。
- 页面会显示 provider / model，优先看这里判断实际 provider。

### 浏览器录音无法开始

- Chrome/Edge 对麦克风权限要求更稳定，优先使用这两个浏览器。
- localhost 通常可以使用麦克风；非 localhost 需要 HTTPS。
- 检查浏览器地址栏左侧权限设置。

### 长录音没有 chunk

- 确认已选择 30 秒、1 分钟、3 分钟或 5 分钟。
- 录制时间必须超过一个分段时长才会自动出现完整 chunk。
- 点击停止后应上传最后不足分段时长的 chunk。

### 整场总结提示没有 chunks 或没有转写

- 先确认 session 下有 chunk。
- 至少一个 chunk 需要完成转写。
- 如果使用真实 LLM，确认 `LLM_PROVIDER` 和 key 配置正确。

