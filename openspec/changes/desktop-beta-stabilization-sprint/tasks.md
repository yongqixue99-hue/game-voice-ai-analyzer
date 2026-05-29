# Tasks — desktop-beta-stabilization-sprint

## 1. 预检修复（已自动验证）

- [x] 1.1 修复 API base 路由：真实 sidecar 运行时前端指向 `:18080`，停止回落默认（`page.tsx`）。
- [x] 1.2 `next.config.ts` 加 `output: "export"`，`npm run build` 产出真实 `out/`。
- [x] 1.3 `tauri.conf.json` 加 `beforeDevCommand`/`beforeBuildCommand`、`bundle.active=true`、`targets="app"`。
- [x] 1.4 确认后端 CORS 已含 Tauri WebView 源（无需改）。

## 2. 静态门禁

- [x] 2.1 `npm run lint` 通过。
- [x] 2.2 `npm run build` 通过并生成 `out/index.html`（非占位）。
- [x] 2.3 backend `pytest` 通过。
- [x] 2.4 `cargo test`（sidecar mock-runtime）通过。

## 3. 尝试 tauri build

- [x] 3.1 `npm run tauri build` 运行并记录结果：**成功**，产出 `frontend/src-tauri/target/release/bundle/macos/LUNARIS.app`（43MB，含 main + hello + real 两个 sidecar）。

## 4. 手动 Tauri dev 验收（用户执行，引导 + 最小修 bug）

- [x] 4.1 `npm run tauri dev` 打开窗口。✅
- [x] 4.2 设置页「启动真实后端」→ sidecar 启动，状态 running + pid + api_base_url。✅
- [x] 4.3 `/api/health` 返回 ok。✅
- [x] 4.4 历史记录加载。✅
- [x] 4.5 录音详情页打开 + 音频播放。✅
- [x] 4.6 上传新音频成功。✅
- [x] 4.7 WebView 录音实测：⚠️ WKWebView 不支持 MediaRecorder → known issue。
- [x] 4.8 mock 转写 ✅；真实转写：🔧 原报「未配置 key」(frozen .env bug)，已修，重打包后转为公网 URL 已知限制（待用户重测）。
- [x] 4.9 AI 总结 ✅。
- [x] 4.10 长录音 session 页 + 整场总结/导出 ✅。
- [ ] 4.11 停止真实后端 → 端口释放（用户已点停止，端口释放待 `lsof` 确认）。
- [ ] 4.12 关闭 Tauri → 真实后端进程不残留（待 `pgrep` 确认）。

## 4b. 验收中发现并修复的 bug（最小修）

- [x] 4b.1 **frozen 凭证加载**：`config.py` 在 `LUNARIS_DATA_DIR` 模式下额外读 `数据目录/config/.env` 与 `数据目录/.env`；仓库根 `.env` 仍优先，dev 不变。
- [x] 4b.2 `desktop_entry.py` 启动日志打印凭证 `.env` 路径与 key 是否加载。
- [x] 4b.3 新增 `backend/desktop-data-config.env.example` 模板。
- [x] 4b.4 重打包真实后端二进制并同步到 `src-tauri/binaries/`；pytest 35、cargo 2 仍通过。

## 5. 文档与收尾

- [x] 5.1 `docs/desktop-beta-test.md`：验收清单 + 通过/known issues（已回填 B 表，B11/B16 已定稿）。
- [x] 5.2 输出 Beta 结论：见 `docs/desktop-beta-status.md`（内部 Beta 候选）。

## 6. 自动化验收（auto-smoke 收尾）

- [x] 6.1 `scripts/desktop_beta_smoke_check.sh`：health + desktop_entry/frozen 启停 + 端口释放
      + B11 真实 ASR 路径 + sidecar 配置 + cargo + lint + build + pytest + 打包产物检查。
- [x] 6.2 B11 自动复测：走 aliyun provider，错误指向公网 URL（达标，已知限制），不再报「未配置 key」。
- [x] 6.3 B16 自动复测：停止后端口释放、无 `lunaris-real-backend` 残留。
- [x] 6.4 修复脚本健康轮询窗口（frozen 冷启动 ~10–15s，避免 SIGTERM mid-unpack 孤儿化子进程）。
- [x] 6.5 新增 `docs/desktop-beta-known-issues.md`、`docs/desktop-beta-status.md`。
- [x] 6.6 全量 smoke：17 PASS / 0 FAIL / 1 KNOWN。
