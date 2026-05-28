# Tauri Shell MVP 开发运行说明

本阶段只验证最小 Tauri 桌面壳，不打包生产应用，不启动 Python sidecar，不实现系统声音、托盘或悬浮窗。

## 前置要求

- Node.js 与 npm。
- Python 3.11 和后端虚拟环境。
- Rust 工具链：`rustc`、`cargo`。
- Tauri 依赖的系统 WebView 运行环境。

如果本机没有 Rust，请先安装 Rust 工具链后再运行 Tauri：

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## 开发启动

终端 1：启动 FastAPI

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

终端 2：启动 Next.js

```bash
cd frontend
npm run dev
```

终端 3：启动 Tauri Shell

```bash
cd frontend
npm run tauri dev
```

Tauri 开发模式会加载：

```text
http://localhost:3000
```

FastAPI 默认地址：

```text
http://127.0.0.1:8000
```

健康检查：

```text
GET http://127.0.0.1:8000/api/health
```

## 设置页运行状态

设置页会显示：

- 运行环境：`Browser` 或 `Tauri`
- FastAPI 状态：`检查中` / `已连接` / `未连接`
- API Base URL

如果后端没有启动，页面应显示：

```text
后端未连接，请先启动 FastAPI 服务
```

## 手动验证清单

在 Tauri WebView 中需要手动确认：

1. 页面能打开。
2. 侧边栏导航可用。
3. 设置页显示运行环境和后端状态。
4. 历史记录页能加载。
5. 录音详情页能打开。
6. 音频播放器能播放。
7. 文件上传是否可用。
8. 浏览器录音按钮是否可用。
9. ASR 和 AI 总结按钮能否正常请求后端。

如果 `MediaRecorder` 在 Tauri WebView 中不可用，不要视为业务功能失败，先记录兼容问题，再进入后续 Tauri WebView 音频兼容性研究。

## 已知限制

- 当前 Tauri Shell 不自动启动 FastAPI。
- 当前 Tauri Shell 不打包 Python 后端。
- 当前 Tauri Shell 不处理生产构建。
- `frontendDist` 暂指向 `../out`，需要后续 `next-static-export-spike` 验证 Next.js 静态导出。
- 阿里云 ASR 在桌面端仍需要公网音频 URL；本地文件或 localhost URL 不能被云端直接访问。
- 不实现系统声音录制、麦克风和系统声音混录、托盘、悬浮窗、开机启动、FunASR 本地部署。
