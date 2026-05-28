# mvp-stabilization-and-e2e-check

## Why

项目已经完成 MVP 主链路和多个增强能力，但功能跨度较大：上传、播放、ASR、AI 总结、转写编辑、浏览器录音、长录音分段、整场总结和导出。进入下一轮开发前，需要先做一次稳定化检查，修复明显问题，补齐错误/空状态，并沉淀端到端手动验收文档。

本 change 不新增大功能，目标是把已有 MVP 串起来，减少“功能存在但页面卡住、错误不可读、用户不知道下一步”的风险。

## What Changes

- 创建 MVP 端到端验收和稳定化 checklist。
- 检查并修复明显的 build/lint/test 或运行时问题。
- 加固 loading、error、empty 和 retry 状态。
- 补充 `docs/manual-e2e-test.md`，说明完整手动验收流程。
- 保持现有上传、ASR、总结、录音和长录音主链路，不做大规模重构。

## Capabilities

- `mvp-stabilization-and-e2e-check`

## Impact

- 前端：可能做少量状态处理、错误提示或半接入功能收尾。
- 后端：仅修复明显 API/测试问题，不改变主链路设计。
- 文档：新增手动 E2E 验收文档。
- 测试：运行后端测试、前端 lint/build；无法自动化的麦克风和云端链路明确列为手动确认项。

