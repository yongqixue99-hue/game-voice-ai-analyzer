# transcript-editing-speaker-labels

## ADDED Requirements

### Requirement: Transcript segment editing

用户必须能够编辑某条录音下的 transcript segment 文本并保存；保存后刷新页面仍保留修改，segment 返回 `is_edited=true` 和更新后的 `updated_at`。

#### Scenario: Edit segment text

- **GIVEN** 某条录音已经有 transcript segments
- **WHEN** 用户通过 `PATCH /api/recordings/{recording_id}/segments/{segment_id}` 保存新文本
- **THEN** 后端返回更新后的 segment
- **AND** 再次获取 segments 时文本仍为修改后的内容

### Requirement: Speaker label display names

用户必须能够把某条录音下的原始 `speaker_label` 映射为更友好的 `display_name`；相同 source label 的所有 segments 必须显示同一 display name。

#### Scenario: Rename Channel 0

- **GIVEN** 某条录音存在 `speaker_label=Channel 0` 的 segments
- **WHEN** 用户保存 `source_label=Channel 0`、`display_name=主持人`
- **THEN** `GET /segments` 返回的相关 segments 必须包含 `display_speaker_label=主持人`
- **AND** 刷新页面后该名称仍然存在

### Requirement: Stale AI summary indication

已有 AI 总结后，如果 transcript segment 或 speaker label 在总结之后被修改，系统必须提示 AI 总结可能过期。

#### Scenario: Segment edit makes analysis stale

- **GIVEN** 某条录音已有 AI 总结
- **WHEN** 用户编辑任意 segment 文本
- **THEN** `GET /analysis` 返回 `is_stale=true`
- **AND** 前端显示“转写内容已修改，当前 AI 总结可能不是最新结果，请重新生成。”

### Requirement: AI summary uses edited transcript and display names

重新生成 AI 总结时，后端必须使用最新 transcript segment 文本，并在 prompt 中优先使用 speaker display name。

#### Scenario: Regenerate after edits

- **GIVEN** 用户已经编辑 segment 文本并重命名 speaker label
- **WHEN** 用户重新生成 AI 总结
- **THEN** LLM prompt 使用修改后的文本和 display name
- **AND** 新返回的 analysis `is_stale=false`

