# 项目路线图

## 当前进度

截至 2026-05-31，LUNARIS 已经从 Web MVP 进入桌面内部 Beta 候选阶段。

当前已跑通的主链路：

```text
Tauri 桌面 App
-> 自动拉起真实 FastAPI sidecar (:18080)
-> 上传音频
-> 局域网 Win 3070 FunASR HTTP 转写
-> DashScope qwen-plus AI 总结
-> 历史记录 / 播放 / 编辑 / 导出
```

当前推荐配置：

```env
ASR_PROVIDER=funasr
FUNASR_HTTP_BASE_URL=http://192.168.1.5:10095
FUNASR_HTTP_HEALTH_PATH=/health
FUNASR_HTTP_TRANSCRIBE_PATH=/v1/audio/transcriptions
FUNASR_HTTP_MODEL=sensevoice
LLM_PROVIDER=dashscope
DASHSCOPE_LLM_MODEL=qwen-plus
```

这条链路已经证明：桌面端本地音频不需要公网 URL，也能完成真实 ASR + 云端 LLM 总结。

## 路线原则

- 继续保持现有上传、ASR、总结、时间轴、历史记录主链路稳定。
- 新能力优先复用现有 recording / transcript_segments / analyses 数据结构。
- 不为了录音能力重写后端主链路。
- 不先做真正实时流式 ASR；先做稳定的文件级 / 分段级处理。
- 不先堆 UI；优先补齐桌面端真实使用所需的音频采集能力。
- 桌面端优先 Tauri，不切 Electron。
- 系统声音 / 游戏内语音 / 队伍语音采集放在麦克风录音稳定之后。
- 所有新能力继续通过 OpenSpec change 驱动，先写 proposal/design/tasks，再实现。

## 阶段 0：收口当前桌面 FunASR Beta

目标：把当前可用链路固化成干净、可交接、可回滚的状态。

范围：

- 更新 `docs/hand_off_status.md`、`docs/desktop-beta-status.md`、`docs/desktop-beta-known-issues.md`。
- 记录 Win 3070 FunASR 实测结果。
- 记录 Tauri 自动启动真实 sidecar 行为。
- 确认桌面数据目录 `config/.env` 用 `ASR_PROVIDER=funasr`。
- 重建并同步 `lunaris-real-backend` sidecar。
- 跑验证：
  - backend pytest
  - frontend lint/build
  - Tauri cargo test
  - ASR provider smoke
  - 桌面 sidecar health/status
- 提交当前变更。

完成标准：

- `npm run tauri dev` 打开窗口后，不手动启动后端也能访问 `:18080/api/health`。
- 上传 MP3 能生成 `source=funasr_http` 转写。
- AI 总结显示 `dashscope / qwen-plus`。
- `.env`、数据库、音频、PyInstaller build/dist、Tauri target 产物不入库。

## 阶段 1：桌面原生麦克风录音

建议新建 change：`desktop-native-microphone-recording`

目标：让用户可以在 LUNARIS 桌面 App 内录制自己的麦克风，绕开 macOS WKWebView `MediaRecorder` 限制。

范围：

- 调研并选择 Tauri/Rust 音频采集方案。
- 处理 macOS 麦克风权限说明。
- 支持开始 / 停止录音。
- 录制音频保存到桌面数据目录。
- 录完后创建 recording，复用现有播放 / 转写 / 总结链路。
- 第一版只录麦克风，不做系统声音。

不做：

- 不采集系统声音。
- 不采集游戏输出。
- 不混录。
- 不做实时字幕。

完成标准：

- 打开桌面 App，点击录音。
- macOS 正常请求麦克风权限。
- 录 30 秒后生成可播放音频。
- 点击真实转写后走 Win FunASR。
- 点击 AI 总结后走 DashScope。

## 阶段 2：桌面长录音 / 游戏自测 Alpha

目标：边打游戏边录自己的麦克风，验证长时间稳定性。

范围：

- 将原生麦克风录音接入长录音 session/chunk。
- 支持 30 秒开发测试分段和 3/5 分钟实用分段。
- 每个 chunk 自动上传、转写、总结。
- 某个 chunk 失败不影响后续 chunk。
- 支持失败 chunk 手动重试。
- 整场总结复用现有 session-level summary。

完成标准：

- 连续录 10-30 分钟不丢文件。
- 至少 3 个 chunk 自动生成。
- chunk 可播放、可转写、可总结。
- 整场总结可生成和导出。
- Win FunASR 断开时错误清晰，不导致 App 崩溃。

## 阶段 3：系统声音 / 游戏语音采集

建议新建 change：`desktop-system-audio-capture`

目标：支持真正的游戏语音复盘，能采集队友语音、游戏内语音或 Discord/YY 等系统输出。

范围：

- 分平台调研：
  - macOS 系统声音采集限制。
  - Windows loopback capture。
  - 外部虚拟声卡方案。
- 决定第一版形态：
  - 内置系统音频采集，或
  - 引导用户配置虚拟声卡，或
  - 先只支持 Windows loopback。
- 设计麦克风 + 系统声音混录。
- 输出统一音频文件，继续走 FunASR + DashScope。

不做：

- 不在没有设计的情况下直接引入复杂音频依赖。
- 不为了系统声音采集破坏已有麦克风/上传链路。

完成标准：

- 能录到自己麦克风和系统输出。
- 打游戏时能捕获队友语音。
- 音频可播放、可转写、可总结。
- 用户知道当前使用的是哪一路输入。

## 阶段 4：设置页配置化

目标：非开发用户不需要编辑 `.env`。

范围：

- 设置页展示并保存：
  - ASR provider。
  - FunASR base URL。
  - health path。
  - transcribe path。
  - model。
  - LLM provider。
  - key 配置状态。
- 后端读取配置文件或安全存储。
- 密钥最终进入系统 keychain 或等价安全存储。

完成标准：

- 修改 FunASR 地址后重启后端或热更新生效。
- 配置错误时设置页给出明确提示。
- 不把 key 暴露给前端日志或 git。

## 阶段 5：可分发 Beta

目标：让非开发者可安装、可启动、可配置、可排错。

范围：

- 正式图标。
- Tauri production build。
- macOS 代码签名 / 公证。
- 安装和首次启动文档。
- 权限说明：麦克风、网络、本地文件。
- 日志目录和“打开日志”入口。
- 基础崩溃 / 后端不可达排查。

完成标准：

- 用户不需要终端。
- 打开 App 自动启动后端。
- 设置页能完成基础配置。
- 上传或录音能完成转写和总结。
- 关闭 App 后无残留 sidecar。

## 什么叫“差不多完成”

### 内部可用

- 上传音频复盘稳定。
- Win FunASR + DashScope 路径稳定。
- Tauri 自动拉起后端稳定。
- 文档和配置清楚。

当前已经接近这一档，剩余主要是收口和提交。

### 可以打游戏自测

- 桌面 App 内能原生录麦克风。
- 录音文件稳定落盘。
- 录完能转写和总结。
- 长录音 10-30 分钟可用。

这是下一阶段目标。

### 可以给别人用的 Beta

- 不需要终端。
- 不需要手改 `.env`。
- 配置页可用。
- App 已签名 / 公证。
- 麦克风录音稳定。
- 系统声音如果未内置，也至少有清晰外部混音方案。

这是可分发 Beta 目标。
