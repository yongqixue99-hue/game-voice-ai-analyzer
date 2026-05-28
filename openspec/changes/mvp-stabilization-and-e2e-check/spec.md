# mvp-stabilization-and-e2e-check

## Goal

对当前 MVP 做稳定化和端到端验收加固，确保主链路可串联、错误可读、空状态友好，并提供完整手动验收文档。

## User Story

作为项目使用者，我希望按一份清晰文档启动前后端并逐步验收：上传/播放、ASR、AI 总结、转写编辑、浏览器录音、长录音分段、整场总结和导出；当某一步失败时，页面能告诉我失败原因和下一步可重试方式。

## Requirements

1. 前端 loading 状态不得无限卡住。
2. API 失败必须显示可读错误。
3. 关键失败步骤必须保留手动重试入口。
4. 空状态必须友好展示。
5. 页面必须清楚显示 provider/model/source，避免 mock 和真实数据混淆。
6. 某个 API 失败不得导致整个页面崩溃。
7. 端到端验收文档必须覆盖启动、配置、上传、ASR、AI 总结、录音、长录音、整场总结和导出。

## API Design

本阶段原则上不新增 API。若发现现有 API 有明显 bug，仅做兼容性修复。

## Frontend Stabilization

- 检查上传、浏览器录音、长录音、整场总结区域是否有 loading/error/empty/success 状态。
- 保留现有手动按钮和重试入口。
- 不做复杂 UI 重设计。

## Backend Stabilization

- 运行现有后端测试并补齐必要测试。
- 确认现有上传、ASR、AI 总结、session/chunk、session summary API 不互相破坏。

## Documentation

新增或更新 `docs/manual-e2e-test.md`。

## Acceptance Criteria

1. OpenSpec change 已创建。
2. 当前明显 build/lint/test 问题已修复。
3. 后端测试通过。
4. 前端 lint/build 通过。
5. `docs/manual-e2e-test.md` 已覆盖完整手动验收流程。
6. 无法自动化确认的项目被明确列为手动测试项。
7. 不新增桌面端、系统声音录制、FunASR 本地部署、实时流式 ASR、WebSocket、复杂 UI 重设计、登录/支付/会员系统。

## Out of Scope

- 桌面端。
- Electron/Tauri。
- 系统声音录制。
- 游戏内语音捕获。
- FunASR 本地部署。
- 真正实时流式 ASR。
- WebSocket。
- 复杂 UI 重设计。
- 登录/支付/会员系统。
- 大规模重构。

## Risks / Trade-offs

- 云端 ASR/LLM 无法在无密钥或无公网 URL 环境中自动验收真实成功路径。
- 麦克风录音需要用户浏览器授权，必须由用户手动确认。
- 分段长录音和整场总结涉及较长操作链路，自动测试覆盖 API，真实体验需要人工点击。

