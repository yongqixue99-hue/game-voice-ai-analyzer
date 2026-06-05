# LUNARIS 桌面端 Known Issues

> 适用版本：内部 Beta 候选（本机 macOS，未签名/未公证）
> 关联：`docs/desktop-beta-status.md`、`docs/funasr-http-provider-handoff.md`

本文件只记录**已知限制**，区别于 bug。

---

## 1. macOS WKWebView 中 MediaRecorder 不可用或不稳定

- **现象**：Tauri 桌面壳用 macOS WKWebView 渲染。WebView 内置网页录音不能作为稳定桌面录音方案。
- **影响**：桌面端不能依赖现有 Web `MediaRecorder` 录音按钮完成游戏录音。
- **当前方案**：桌面 App 使用 Tauri/Rust 原生“桌面麦克风”入口，录完后复用现有上传、FunASR 转写、AI 总结链路。
- **剩余验证**：仍需在真实 Tauri 窗口确认 macOS 麦克风权限弹窗、录音文件和上传结果。

## 2. 系统声音 / 游戏声音 / 队友语音采集未实现

- **现象**：当前第一版原生录音只采集用户自己的麦克风；尚不能直接采集系统输出音频。
- **影响**：不能直接录到游戏声音、Discord/YY/游戏内队友语音。
- **当前可测范围**：上传音频复盘；原生麦克风验证通过后，可测试“只录自己说话”的游戏场景。
- **后续方案**：
  1. 先稳定原生麦克风录音。
  2. 再评估系统声音采集。
  3. 最后做麦克风 + 系统声音混录。

## 3. Win FunASR 当前只返回整段文本

- **现象**：`POST /v1/audio/transcriptions` 当前返回 `{"text": "..."}`，没有 `segments` 或 `sentence_info`。
- **影响**：LUNARIS 会生成 1 个整段 segment，时间范围为 `[0, 音频时长]`。AI 总结可用，但时间轴无法细分到句子。
- **后续方案**：如果 Win FunASR 服务能返回句级时间戳，优先只调整 `backend/app/asr.py::parse_funasr_response`，不要重构主链路。

## 4. WebM 输入在当前 Win FunASR 服务上可能失败

- **现象**：本地 WebM 样例直连 Win FunASR 服务曾返回 HTTP 500。
- **影响**：WebView/浏览器录音生成的 `.webm` 可能不能直接被当前 Win 服务识别。
- **临时方案**：内部测试优先使用 MP3 / WAV / M4A。
- **后续方案**：确认 Win 服务 ffmpeg/解码能力，或在 LUNARIS 后端增加音频转码链路。转码会引入外部依赖，需单独 OpenSpec change。

## 5. 阿里云非实时 ASR 仍需要公网音频 URL

- **现象**：`ASR_PROVIDER=aliyun` 时，阿里云云端需要公网可下载的音频 URL。
- **影响**：桌面本地音频不能直接走阿里云 ASR，除非使用 OSS 签名 URL、隧道或其他公网托管方式。
- **当前状态**：这不再阻塞桌面真实 ASR，因为当前推荐路径是 `ASR_PROVIDER=funasr_http`。
- **后续定位**：阿里云 provider 继续保留，适用于云端部署或未来 OSS 签名 URL 路线。

## 6. 配置仍是过渡形态

- **现象**：桌面端 provider / FunASR 地址 / LLM provider 目前通过数据目录 `config/.env` 配置。
- **位置**：

```text
~/Library/Application Support/com.lunaris.voice-analyzer/data/config/.env
```

- **影响**：非开发用户不应手动编辑 `.env`。
- **后续方案**：设置页提供 FunASR URL、model、LLM provider、key 状态配置；密钥最终应进入系统 keychain 或安全本地存储。

## 7. 生产构建与签名未完成

- **现象**：可以构建 `.app`，但未做正式图标、代码签名、公证和安装文档。
- **影响**：当前是本机内部 Beta，不是可分发版本。
- **后续方案**：完成核心录音能力后，再做正式图标、Developer ID 签名、公证和安装包验证。
