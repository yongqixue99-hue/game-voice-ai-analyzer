# LUNARIS 桌面端 Beta 状态

> 版本定位：**内部桌面 Beta 候选**（本机 macOS aarch64，未签名）
> 自动化验收：`scripts/desktop_beta_smoke_check.sh` —— 最近一次 **17 PASS / 0 FAIL / 1 KNOWN**
> 关联：`docs/desktop-beta-test.md`、`docs/desktop-beta-known-issues.md`

---

## 1. 当前是否可称为内部 Beta？

**可以，作为内部桌面 Beta 候选。**

依据：核心链路（启动/停止真实后端、health、上传、播放、mock 转写、AI 总结、导出、
session 页）在真实 sidecar 上跑通；`tauri build` 能产出含双 sidecar 的 `LUNARIS.app`；
进程生命周期干净（停止/关闭后端口释放、无残留）。剩余两项是**已知限制**（真实 ASR 公网
回源、WebView 录音），不阻塞「内部自测/试用」级别的 Beta。

尚**不是**正式发布版：未做代码签名 / 公证、未做真实 ASR 端到端闭环。

## 2. 已通过项（自动化验证）

| 能力 | 状态 | 验证方式 |
|---|---|---|
| Tauri build → LUNARIS.app（含双 sidecar） | ✅ | smoke §6 / 手动 |
| 真实 backend sidecar 启停 | ✅ | smoke §1 / 手动 B2/B15 |
| /api/health | ✅ | smoke §1.1 |
| 停止/关闭后端口释放、无残留进程（B16） | ✅ | smoke §1.3/1.4 |
| 上传音频 | ✅ | smoke §2.1 / 手动 B8 |
| 音频播放 | ✅ | 手动 B7 |
| mock 转写 | ✅ | 手动 B10 |
| AI 总结 | ✅ | 手动 B12 |
| 导出 / 整场总结 | ✅ | 手动 B14 |
| 前端 lint / build（静态导出 out/） | ✅ | smoke §4 |
| 后端 pytest（35） | ✅ | smoke §5 |
| Tauri cargo test（sidecar mock-runtime） | ✅ | smoke §3.5 |

## 3. 未完全通过项（已知限制，非桌面壳失败）

| 项 | 状态 | 说明 |
|---|---|---|
| 真实 ASR 端到端 | ⚠️ 受限 | 阿里云需公网音频 URL，桌面端 `127.0.0.1` 本地文件云端不可达。按钮调用 / provider 选择 / 错误链路均正确（错误明确指向公网 URL）。详见 known-issues §2。 |
| WebView 内置录音 | ⚠️ 受限 | macOS WKWebView 不支持 `MediaRecorder`。改用上传音频。详见 known-issues §1。 |
| 代码签名 / 公证 | ⚠️ 未做 | 本机内部 Beta，首次打开需右键「打开」。详见 known-issues §3。 |

## 4. 下一阶段建议

1. **优先闭环真实 ASR**：在 **FunASR HTTP Provider** 与 **OSS 临时签名 URL** 中**二选一**先做一个，
   解除"真实转写端到端不通"这一当前唯一卡住核心价值的限制。
   - 推荐顺序见本仓库会话报告 / 团队讨论。
2. **不要继续堆 UI**：当前 UI 已够用，重心放在 ASR 闭环与稳定性。
3. **不要先做系统声音录制 / 混录**：在真实 ASR 闭环稳定前，系统声音录制无意义；
   待 ASR 稳定后再评估。
4.（可选）真实 ASR 闭环稳定后，再做代码签名 / 公证，迈向"可分发 Beta"。

## 5. 如何复跑自动化验收

```bash
scripts/desktop_beta_smoke_check.sh          # 生命周期 + B11 + 配置 + lint/build/pytest/cargo
scripts/desktop_beta_smoke_check.sh --quick  # 只跑生命周期 + B11 + 配置检查（秒级）
scripts/desktop_beta_smoke_check.sh --build  # 额外重跑 npm run tauri build（很慢）
```

冒烟脚本对真实数据无副作用：真实后端始终跑在临时 `LUNARIS_DATA_DIR`，不碰你的 dev DB/音频。
注：frozen onefile 冷启动约 10–15s（解包 + 导入），脚本已留足健康轮询窗口。
