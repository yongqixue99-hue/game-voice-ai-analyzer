# LUNARIS 桌面端 Beta 状态

> 版本定位：**内部桌面 Beta 候选**（本机 macOS aarch64，未签名）
> 当前 ASR 路线：桌面 sidecar + 局域网 Win 3070 FunASR HTTP Provider
> 关联：`docs/desktop-beta-test.md`、`docs/desktop-beta-known-issues.md`、`docs/funasr-http-provider-handoff.md`

---

## 1. 当前是否可称为内部 Beta？

**可以，作为内部桌面 Beta 候选。**

相比上一版，核心变化是：桌面端真实 ASR 已不再卡在阿里云公网回源限制上。当前桌面端已能：

```text
打开 Tauri App
-> 自动拉起真实 FastAPI sidecar (:18080)
-> 上传音频
-> 直传到 Win 3070 FunASR HTTP 服务
-> 生成 transcript_segments
-> 调用 DashScope qwen-plus 生成 AI 总结
```

这已经满足“上传音频复盘”的内部 Beta 标准。

尚**不是**可分发 Beta / 正式版：缺少桌面原生录音、系统声音/游戏语音采集、配置页写入、代码签名/公证。

## 2. 已通过项

| 能力 | 状态 | 验证方式 |
|---|---|---|
| Tauri dev 打开 LUNARIS 窗口 | ✅ | 手动 |
| Tauri 启动自动拉起真实 FastAPI sidecar | ✅ | `curl :18080/api/health` |
| 前端 API base 自动指向 `:18080` | ✅ | 设置页 / 接口验证 |
| 桌面数据目录 `config/.env` 加载 | ✅ | sidecar ASR status |
| 上传 MP3 音频 | ✅ | 手动 |
| 上传时长探测 | ✅ | MP3 样例 `138.579563s` |
| Win 3070 FunASR health | ✅ | `GET http://192.168.1.5:10095/health` |
| Win 3070 FunASR 转写 | ✅ | `POST /v1/audio/transcriptions` |
| FunASR 转写落库 | ✅ | `source=funasr_http` |
| DashScope AI 总结 | ✅ | `provider=dashscope`, `model=qwen-plus` |
| 后端 pytest | ✅ | `49 passed` |
| 前端 lint | ✅ | 通过 |
| Tauri cargo test | ✅ | `2 passed` |

## 3. 已知限制

| 项 | 状态 | 说明 |
|---|---|---|
| 桌面内置网页录音 | ⚠️ 受限 | macOS WKWebView 中 `MediaRecorder/getUserMedia` 不可靠；下一阶段改做 Tauri/Rust 原生麦克风录音。 |
| 系统声音 / 游戏声音 / 队友语音 | ❌ 未实现 | 当前不能直接采集系统输出，也不能麦克风 + 系统声混录。 |
| FunASR 句级时间戳 | ⚠️ 受限 | 当前 Win 服务只返回整段 `text`，LUNARIS 会落成单段 `[0, duration]`。 |
| WebM 输入 | ⚠️ 受限 | 当前 Win FunASR 服务对本地 WebM 样例返回 500；优先使用 MP3/WAV/M4A。 |
| 配置体验 | ⚠️ 过渡期 | 仍需手动编辑数据目录 `config/.env`；后续应做设置页配置。 |
| 代码签名 / 公证 | ⚠️ 未做 | 当前是本机内部 Beta，尚不是可分发版。 |

## 4. 下一阶段建议

1. **先收口当前变更**：文档、测试、sidecar 二进制同步、git 提交。
2. **做桌面原生麦克风录音**：绕开 WKWebView `MediaRecorder`，先支持录自己的麦克风。
3. **做游戏自测 Alpha**：用原生麦克风录音 + FunASR + DashScope 跑 10-30 分钟真实游戏场景。
4. **再做系统声音/混录**：这是队伍语音复盘的关键，但复杂度高于麦克风，应放在麦克风稳定后。
5. **最后做可分发 Beta**：设置页配置、keychain/配置安全、签名/公证、安装文档。

## 5. 当前推荐验收命令

```bash
cd /Users/xueyongqi/project/project-2/backend
.venv/bin/python -m pytest -q

cd /Users/xueyongqi/project/project-2/frontend
npm run lint
npm run build

cd /Users/xueyongqi/project/project-2/frontend/src-tauri
cargo test -- --test-threads=1
```

FunASR 状态：

```bash
curl http://127.0.0.1:18080/api/asr/status
curl http://192.168.1.5:10095/health
```

桌面启动：

```bash
cd /Users/xueyongqi/project/project-2/frontend
npm run tauri dev
```
