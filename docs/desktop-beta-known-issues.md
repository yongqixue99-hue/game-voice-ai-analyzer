# LUNARIS 桌面端 Known Issues

> 适用版本：内部 Beta 候选（本机 macOS，未签名/未公证）
> 关联：`docs/desktop-beta-test.md`、`docs/desktop-beta-status.md`

本文件只记录**已知限制**，区别于 bug。下列各项均为当前刻意不在本阶段解决的范围。

---

## 1. macOS WKWebView 中 MediaRecorder 不可用

- **现象**：Tauri 桌面壳用 macOS WKWebView 渲染。WebView 内点网页录音时提示
  「当前浏览器不支持网页录音，请换用 Chrome/Edge」——`MediaRecorder` / `getUserMedia`
  在 WKWebView 中不可用或不稳定。
- **影响**：桌面端**内置网页录音**不可用。
- **临时方案**：改用**上传音频**链路（已验证可用）。
- **后续方案**：用 Tauri/Rust 原生录音或桌面音频采集桥接替代网页 `MediaRecorder`。
- **不在本阶段做**：原生录音桥接。

## 2. 阿里云非实时 ASR 需要公网音频 URL

- **现象**：真实转写走阿里云 provider 时，云端需要一个**可公网下载**的音频 URL；
  桌面端音频是本地文件，`PUBLIC_BASE_URL` 指向 `127.0.0.1` 时云端无法下载，
  报「阿里云无法访问本地音频 URL…」或任务侧 `FILE_DOWNLOAD_FAILED`。
- **影响**：桌面端真实 ASR **端到端不通**；按钮调用、provider 选择、错误链路本身是对的。
- **重要**：这是 ASR 供给侧限制，**不是桌面壳失败**。冒烟脚本据此把它判为
  `KNOWN`（已知限制），不计入失败。
- **附注**：桌面 sidecar 跑在 `:18080`，而隧道通常指向 dev `:8000` 且音频在桌面数据目录，
  故即便配了隧道也未必端到端通——同属此限制。
- **临时方案**：开发期用 localtunnel / ngrok / Cloudflare Tunnel 暴露后端。
- **后续方案（三选一）**：
  1. **OSS 临时签名 URL**：上传到对象存储，生成带签名的临时公网 URL 交给阿里云。
  2. **FunASR HTTP Provider**：本机/局域网跑 FunASR 推理服务，后端走 HTTP provider，
     不依赖公网回源。
  3. **支持文件直传的 ASR provider**：换用允许直接 POST 音频文件、无需公网 URL 的服务。
- **不在本阶段做**：不引入 OSS 实现、不本地部署 FunASR。

## 3. 生产构建与签名未完成

- **现象**：`LUNARIS.app` 可由 `npm run tauri build` 产出，但**未做代码签名 / 公证**，
  且仅当前平台（`aarch64-apple-darwin`）。
- **影响**：当前是**本机内部 Beta**，不是正式发布版；首次打开需右键「打开」绕过 Gatekeeper。
- **后续方案**：申请 Developer ID 证书做 codesign + notarize；按需出 Intel / 通用二进制。
- **不在本阶段做**：签名、公证、正式安装包。

---

## 附：凭证位置（非 bug，配置须知）

frozen sidecar 不读仓库 `.env`（`__file__` 在临时解包目录）。桌面端密钥需放数据目录：

```
~/Library/Application Support/com.lunaris.voice-analyzer/data/config/.env
```

模板见 `backend/desktop-data-config.env.example`。缺失时启动日志会打印
`credentials .env: ... missing — real ASR/LLM keys unset`。
