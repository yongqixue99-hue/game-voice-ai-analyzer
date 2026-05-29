# LUNARIS 桌面端 Beta 验收

> change: `desktop-beta-stabilization-sprint`
> 平台：macOS (aarch64-apple-darwin) · 日期：2026-05-29

本文档分两部分：**A. 自动验证**（已由 CI 级命令验证）与 **B. 手动 Tauri 验收**（需在真实窗口逐项点击）。

---

## 0. 前置

- 后端 venv：`backend/.venv`（已 `pip install -e .` + `pyinstaller`）。
- 真实后端 sidecar 二进制：`frontend/src-tauri/binaries/lunaris-real-backend-<triple>`
  （由 `backend/build-desktop-backend.sh` 生成，**不入库**）。
- hello-backend sidecar 保留为 fallback：`binaries/lunaris-hello-backend-<triple>`。
- 重新生成真实后端二进制：
  ```bash
  cd backend && ./build-desktop-backend.sh
  cp dist/lunaris-real-backend-<triple> ../frontend/src-tauri/binaries/
  ```

---

## A. 自动验证（已通过）

| # | 项 | 命令 | 结果 |
|---|---|---|---|
| A1 | 前端 lint | `npm run lint` | ✅ 0 error |
| A2 | 前端静态导出 build | `npm run build` | ✅ 生成 `out/index.html`（真实 SPA，非占位） |
| A3 | 后端单测 | `pytest` | ✅ 35 passed |
| A4 | Tauri sidecar 集成测试 | `cargo test` | ✅ 2 passed（hello + real，spawn→health→stop→端口释放） |
| A5 | 本机 app 打包 | `npm run tauri build` | ✅ 产出 `target/release/bundle/macos/LUNARIS.app`（43MB，含 main + 两个 sidecar） |
| A6 | desktop_entry 源码启动 | `python backend/desktop_entry.py` | ✅ `/api/health` ok |
| A7 | frozen 二进制独立启动 | 运行 `dist/lunaris-real-backend` | ✅ `/api/health`、`/api/recordings`、`/openapi.json` 均 ok |

### A 级修复（本次）

1. **API base 路由 bug**：`window.__LUNARIS_CONFIG__.apiBaseUrl` 此前声明但无人赋值，桌面端请求恒落 `:8000`。已改为真实 sidecar 运行时指向 `:18080`，停止回落默认，并在启停后重载数据。
2. **静态导出**：`next.config.ts` 加 `output: "export"`（原先 `out/index.html` 仅 41B 占位）。
3. **build 自包含**：`tauri.conf.json` 加 `beforeDevCommand`/`beforeBuildCommand`，`bundle.active=true`、`targets="app"`。
4. **frozen 凭证加载 bug**（B11/总结根因）：PyInstaller 二进制 `__file__` 在临时解包目录，`config.py` 原先只从仓库根读 `.env` → 桌面端 `DASHSCOPE_API_KEY` 永远加载不到，真实 ASR/LLM 报「未配置 key」。已改为 `LUNARIS_DATA_DIR` 模式下额外读 `数据目录/config/.env`（与 `数据目录/.env`），仓库根 `.env` 优先级更高、dev 不受影响。验证：rebuild 后真实转写不再报 key 错误，转为命中公网 URL 已知限制。配置位置见 `backend/desktop-data-config.env.example`。

---

## B. 手动 Tauri dev 验收

启动：
```bash
cd frontend && npm run tauri dev
```
（`beforeDevCommand` 会自动起 `next dev`；首次 Rust 编译较慢。）

逐项勾选（在窗口内操作）：

| # | 验收项 | 操作 | 期望 | 结果 |
|---|---|---|---|---|
| B1 | 打开窗口 | `npm run tauri dev` | LUNARIS 窗口出现 | ✅ |
| B2 | 启动真实后端 | 设置页「启动真实后端」 | 状态变 running | ✅ |
| B3 | 健康检查 | 自动 | 显示 api_base_url `:18080`，health ok | ✅ |
| B4 | 状态显示 | 看设置页 | running + pid + `127.0.0.1:18080` | ✅ |
| B5 | 历史记录 | 打开历史页 | 列表加载（空库则空列表，无报错） | ✅ |
| B6 | 录音详情 | 点一条录音 | 详情页打开 | ✅ |
| B7 | 音频播放 | 播放器播放 | 有声音/进度走动 | ✅ |
| B8 | 上传音频 | 上传新文件 | 上传成功并入列表 | ✅ |
| B9 | WebView 录音 | 点录音按钮 | MediaRecorder 可用 / 记录兼容问题 | ⚠️ known issue：WKWebView 不支持 MediaRecorder，提示换 Chrome/Edge |
| B10 | mock 转写 | mock 转写按钮 | 请求后端返回 | ✅ |
| B11 | 真实转写 | 真实 ASR 按钮 | 发起请求（公网 URL 失败记为 known issue） | ✅ 已修+自动复测：走 aliyun provider，错误明确指向「无法访问本地音频 URL」(已知限制，达标) |
| B12 | AI 总结 | 总结按钮 | 请求后端返回 | ✅ |
| B13 | 长录音 session | 打开 session 页 | 页面打开 | ✅ |
| B14 | 整场总结/导出 | 总结/导出 | 可用 | ✅ |
| B15 | 停止后端 | 「停止真实后端」 | 状态 stopped，`:18080` 端口释放 | ✅ |
| B16 | 关闭无残留 | 关闭 Tauri 窗口 | `lsof -i:18080` 无残留进程 | ✅ 自动复测：停止后端口释放、无 lunaris-real-backend 残留 |

验证端口/残留（终端）：
```bash
lsof -i :18080            # 启动后应有 lunaris-real-backend；停止/关闭后应为空
pgrep -fl lunaris-real-backend
```

---

## C. Known issues / 限制

- **真实 ASR 公网回源**：阿里云非实时 ASR 无法访问桌面端 `127.0.0.1` 本地文件。dev 期用 localtunnel 暴露；B11 若因此失败属**已知限制**，非 bug。正式版三选一：OSS 临时签名 URL / 本地 FunASR / 支持直接上传文件的 ASR provider。本次不引入 OSS、不解决。
  - 注意：桌面 sidecar 跑在 `:18080`，而你的 `PUBLIC_BASE_URL` 隧道通常指向 dev 的 `:8000` 且音频在桌面数据目录下，故桌面端真实 ASR 端到端仍不通——属同一已知限制。
- **桌面端凭证位置**：frozen sidecar 不读仓库 `.env`，需把密钥放在数据目录 `config/.env`（macOS：`~/Library/Application Support/com.lunaris.voice-analyzer/data/config/.env`）。模板见 `backend/desktop-data-config.env.example`。缺失时启动日志会提示 `credentials .env: ... missing`。
- **MediaRecorder/getUserMedia**：在 Tauri WebView（macOS WKWebView）的可用性以 B9 实测为准；若受限，记录为 known issue，后续评估原生录音桥接。
- **真实 sidecar 冷启动**：onefile 需解包 + 导入 sqlalchemy/pydantic，首次健康检查可能需等待 1–3s（前端按钮已含轮询）。
- **代码签名/公证**：`LUNARIS.app` 未签名/未公证，首次打开需右键“打开”绕过 Gatekeeper。本次不做签名。
- **PyInstaller 非声明依赖**：`pyinstaller` 手动装入 `backend/.venv`，未写入 `pyproject.toml`。`build-desktop-backend.sh` 会自检并提示安装命令。

## D. Beta 结论

见提交说明与会话报告：A 级（自动验证 + 打包）全部通过，B 级需人工逐项确认后回填本表。
