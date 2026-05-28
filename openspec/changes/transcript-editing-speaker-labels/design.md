# transcript-editing-speaker-labels 设计说明

## 数据模型取舍

### Segment 编辑

直接更新 `transcript_segments.text`，并增加：

- `is_edited`
- `updated_at`

不额外保存 `edited_text`，因为 MVP 只需要当前有效转写文本；原始 ASR 文本后续如果需要审计或版本对比，再单独引入 revision 表。

### Speaker 显示名

新增 `speaker_labels` 表，使用 `(recording_id, source_label)` 作为唯一映射。这样可以保留 ASR 原始 `speaker_label`，同时给用户展示更友好的 `display_name`。

### AI 总结过期

不在 `recording_analyses` 增加 `is_stale` 字段。每次读取分析时动态比较：

- 当前 analysis `updated_at`
- 当前 recording 下最新 segment `updated_at`
- 当前 recording 下最新 speaker label `updated_at`

如果 transcript 或 speaker label 更新晚于 analysis，则返回 `is_stale: true`。

## API 行为

### Segment 更新

`PATCH /api/recordings/{recording_id}/segments/{segment_id}` 只允许修改文本。保存时：

- 校验录音存在。
- 校验 segment 属于该录音。
- 去掉首尾空白。
- 文本为空返回 `400`。
- 设置 `is_edited=true` 和新的 `updated_at`。

### Speaker label 更新

`PATCH /api/recordings/{recording_id}/speaker-labels` 使用 upsert 行为：

- `source_label` 必须是该 recording 已存在的 segment label。
- `display_name` 为空字符串时清空自定义名称。
- 保存后返回当前 label 映射。

## AI 总结

`analyze_recording` 查询当前 speaker label 映射后传给 LLM provider。`build_transcript_context` 输出时：

- 有 display name：`主持人 (Channel 0): 文本`
- 无 display name：`Channel 0: 文本`

这样真实 LLM 能理解用户重命名后的角色，同时仍保留 source label 作为上下文。

## 前端状态

前端新增：

- `speakerLabelsByRecordingId`
- `labelErrorsByRecordingId`
- `editingSegmentById`
- `segmentDraftById`
- `speakerLabelDraftByKey`

保存 segment 或 speaker label 后：

- 立即更新本地 segments / labels。
- 如果当前 recording 已有 analysis，则把对应 analysis 的 `is_stale` 置为 `true`，无需等刷新。
- 重新生成 AI 总结成功后使用后端返回值覆盖 analysis，`is_stale` 变为 `false`。

