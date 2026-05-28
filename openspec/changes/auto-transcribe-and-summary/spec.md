# auto-transcribe-and-summary 规格

## Goal

让用户在上传音频或完成浏览器录音后，可以选择自动执行 ASR 转写和 AI 总结，减少手动点击步骤。

## User Story

用户开启“自动分析”后上传音频或录制麦克风音频。上传成功后系统自动开始转写，转写成功后自动生成 AI 总结。用户能看到当前处理状态；如果某一步失败，页面展示明确错误并保留可手动重试入口。

## Requirements

1. 页面必须出现“自动分析”开关。
2. 自动分析关闭时，上传或录音完成后不得自动调用 ASR。
3. 自动分析开启时，手动上传成功后自动调用 `POST /api/recordings/{recording_id}/transcribe`。
4. 自动分析开启时，浏览器录音上传成功后自动调用同一自动流程。
5. ASR 转写成功后自动调用 `POST /api/recordings/{recording_id}/analyze`。
6. 自动流程完成后刷新转写时间轴和 AI 总结。
7. 自动流程必须显示状态：`idle`、`uploading`、`uploaded`、`transcribing`、`transcribed`、`summarizing`、`completed`、`failed`。
8. ASR 失败时不得继续 AI 总结。
9. ASR 失败时必须展示错误原因。
10. AI 总结失败时必须保留已成功的转写结果。
11. AI 总结失败时必须展示错误原因。
12. 自动流程失败后，用户仍可手动点击“真实转写”或“生成 AI 总结”重试。
13. 自动流程运行中，同一 recording 不得重复触发自动分析。
14. 原有手动上传、浏览器录音、真实转写、AI 总结按钮必须继续可用。
15. 不新增后端组合接口，第一版由前端顺序调用现有接口。

## API Design

本阶段不新增 API。

自动流程复用：

```http
POST /api/recordings/{recording_id}/transcribe
POST /api/recordings/{recording_id}/analyze
```

前端调用顺序：

```text
upload recording -> transcribe recording -> analyze recording -> refresh UI
```

如果后续需要服务端任务编排，可以再引入：

```http
POST /api/recordings/{recording_id}/auto-analyze
```

但不属于本 change。

## Frontend Interaction

新增自动分析开关：

- 默认关闭。
- 关闭时，上传或录音后只刷新录音列表。
- 开启时，上传或录音后立即显示自动流程状态。

自动流程展示：

- 上传中。
- 上传完成。
- 转写中。
- 转写完成。
- 总结中。
- 完成。
- 失败。

失败后：

- ASR 失败：不继续总结，保留手动“真实转写”按钮。
- AI 总结失败：保留已生成 segments，保留手动“生成 AI 总结”按钮。

## State Machine

```text
idle
  -> uploading
  -> uploaded
  -> transcribing
  -> transcribed
  -> summarizing
  -> completed
```

任一步失败：

```text
failed
```

上传失败时停留在 `failed`，不进入转写。

ASR 失败时停留在 `failed`，不进入总结。

总结失败时停留在 `failed`，但保留已成功的转写结果。

## Error Handling

- 上传失败：展示上传错误，不调用 ASR。
- ASR 失败：展示 ASR 错误，不调用 AI 总结。
- AI 总结失败：展示 AI 总结错误，保留 segments。
- 自动流程运行中禁用重复触发，避免同一 recording 并发自动分析。
- 手动按钮仍保留，用于失败后的重试。

## Acceptance Criteria

1. 原有手动上传音频功能仍然可用。
2. 原有浏览器录音功能仍然可用。
3. 原有手动“真实转写”按钮仍然可用。
4. 原有手动“生成 AI 总结”按钮仍然可用。
5. 页面出现“自动分析”开关。
6. 自动分析关闭时，上传或录音后不会自动转写。
7. 自动分析开启时，上传音频成功后自动开始 ASR 转写。
8. ASR 转写成功后自动开始 AI 总结。
9. 自动流程完成后，页面显示转写时间轴和 AI 总结。
10. 浏览器录音停止并上传成功后，也能自动执行转写和总结。
11. ASR 失败时，不继续执行 AI 总结，并展示错误。
12. AI 总结失败时，保留转写结果，并展示错误。
13. 用户可以手动重试失败步骤。
14. 前端 build/lint 通过。
15. 后端测试通过。
16. OpenSpec tasks.md 已更新。

## Out of Scope

- 每 3-5 分钟自动切片。
- 长录音 session。
- 真正实时流式 ASR。
- WebSocket。
- 系统声音录制。
- 游戏内语音捕获。
- 桌面端。
- FunASR 本地部署。
- 说话人分离算法。
- 高光片段。
- 复杂任务队列。
- 后台 worker。
- 登录系统。
- 权限系统。
- 大规模 UI 重设计。

## Risks / Trade-offs

- 前端顺序调用实现简单，但刷新页面会丢失当前临时状态。
- ASR 和 LLM 调用耗时较长，前端需要清晰展示 loading 和失败原因。
- 不引入队列意味着长任务可靠性有限，但能保持第一版实现简单，并复用现有主链路。

