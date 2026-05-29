# Design — desktop-beta-stabilization-sprint

> 稳定化冲刺，少改动多验证。只记录关键决策与验收。

## 目标

让本机 Tauri 桌面端进入 Beta：dev 稳定、真实 sidecar 可从设置页启停、核心链路在 WebView 可用、尝试本机 app build。

## 关键修复（均为最小必要）

### 1. API base 路由（核心 bug）

现象：`getApiBaseUrl()` 读 `window.__LUNARIS_CONFIG__?.apiBaseUrl`，但**无人写入**该值 → 桌面端所有请求恒落 `http://127.0.0.1:8000`（dev 后端），真实 sidecar（`:18080`）启动后仍不被使用。

修复：新增 `setRuntimeApiBaseUrl()`；`refreshRealBackendStatus()` 依据 sidecar 状态写入/清除：
- running → `apiBaseUrl = status.api_base_url`（`http://127.0.0.1:18080`）
- stopped → 清除 → 回落默认（dev 8000 / `NEXT_PUBLIC` 覆盖）

启停成功后 `checkBackendHealth + loadRecordings + loadRecordingSessions`，启动时 bootstrap 也走同一路径。

不引入新的全局状态层，保持现有 `window.__LUNARIS_CONFIG__` 约定。

### 2. 静态导出

`next.config.ts` 加 `output: "export"`。应用是单一 `"use client"` 页、无 server route/action/`next/image`，符合静态导出限制。产物落 `out/`（Tauri `frontendDist: ../out`）。

### 3. build 自包含

`tauri.conf.json`：
- `beforeDevCommand: npm run dev` / `beforeBuildCommand: npm run build`
- `bundle.active: true`、`targets: "app"`（只出 .app，避开 dmg 额外依赖）

## CORS

后端已 `allow_origins` 含 `tauri://localhost`、`tauri.localhost`、`localhost:3000`，跨源到 `:18080` 无需改。

## 风险 / known issues

- 阿里云非实时 ASR 无法回源桌面端本地文件（`127.0.0.1`）：dev 用 localtunnel，正式版三选一（OSS 签名 URL / 本地 FunASR / 支持上传的 provider）。本次不解决。
- MediaRecorder/getUserMedia 在 Tauri WebView 的可用性需实测，结果记入文档。
- `tauri build` 可能因签名/打包环境失败；失败只记录，不大改。
- 真实 sidecar onefile 冷启动较慢（unpack + sqlalchemy/pydantic import），健康检查需轮询等待。

## 验收

见 `tasks.md` 勾选与 `docs/desktop-beta-test.md`。最终判断是否达到“桌面 Beta”。
