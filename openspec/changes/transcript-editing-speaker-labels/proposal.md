## Why

当前 ASR 转写已经能生成可点击时间轴，但真实语音识别经常会出现错字、断句不准、人名地名或术语识别错误。用户如果不能修正转写，后续 AI 总结也会基于错误文本继续放大偏差。

同时 ASR 返回的 `Channel 0` 这类 speaker/channel 名称不适合用户理解，需要允许用户把原始 label 改成“主持人”“嘉宾”“我”等更友好的显示名。

## What Changes

- 允许用户编辑单条 transcript segment 的 `text` 并保存。
- 为 `transcript_segments` 增加编辑状态和更新时间，刷新页面后仍保留用户修改。
- 新增 speaker label 显示名映射，允许把 `Channel 0` 等原始 label 重命名为用户自定义名称。
- 列表和时间轴展示优先使用 speaker display name；未重命名时继续显示原始 label。
- AI 总结生成时使用最新 segment 文本和 speaker display name。
- 如果用户在已有 AI 总结后修改转写或 speaker label，前端显示“AI 总结可能过期”的提示。
- 重新生成 AI 总结后，过期提示消失。

## Capabilities

### New Capabilities

- `transcript-editing-speaker-labels`: 转写文本编辑、speaker/channel 显示名重命名、AI 总结过期判断。

### Modified Capabilities

- `ai-summary-highlights`: AI 总结生成时使用用户修正后的 transcript 和 speaker display name，并返回 `is_stale` 供前端提示。

## Impact

- Backend:
  - `transcript_segments` 增加 `is_edited`、`updated_at`。
  - 新增 `speaker_labels` 表。
  - 新增/修改 segment 与 speaker label API。
  - AI 总结读取 speaker label 映射，并动态计算 `is_stale`。
- Frontend:
  - 时间轴增加 segment 编辑交互。
  - 增加 speaker/channel 重命名入口。
  - AI 总结区域展示过期提示。
- Database:
  - SQLite 启动时执行最小 schema migration。

