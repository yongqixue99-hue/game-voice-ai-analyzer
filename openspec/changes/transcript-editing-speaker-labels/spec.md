# transcript-editing-speaker-labels 规格

## Goal

让用户可以修正 ASR 转写文本、重命名 speaker/channel 显示名，并确保后续 AI 总结基于用户修正后的 transcript segments 生成。

## User Story

用户上传音频并完成 ASR 转写后，发现某些转写文字或 speaker/channel 名称不准确。用户可以在页面上直接编辑 segment 文本，把 `Channel 0` 重命名为“主持人”等名称。修改后系统提示已有 AI 总结可能过期，用户重新生成后得到基于最新转写的总结。

## Requirements

1. 用户可以编辑任意 transcript segment 的 `text`。
2. 保存 segment 后，后端持久化修改，刷新页面仍保留。
3. 保存 segment 后，该 segment 的 `is_edited` 为 `true`，`updated_at` 更新。
4. 用户可以为某条录音下的原始 `speaker_label` 设置 `display_name`。
5. 同一录音中相同 `speaker_label` 的 segments 必须统一显示该 `display_name`。
6. 刷新页面后 speaker label 重命名仍保留。
7. 未重命名时，前端继续显示原始 `speaker_label`。
8. `GET /segments` 响应应包含 `display_speaker_label`，方便前端直接展示。
9. 已存在 AI 总结时，如果转写文本或 speaker label 在总结之后发生变化，`GET /analysis` 应返回 `is_stale: true`。
10. 前端在 `is_stale` 为 `true` 时显示：“转写内容已修改，当前 AI 总结可能不是最新结果，请重新生成。”
11. 用户重新生成 AI 总结后，后端使用最新 segment 文本和 speaker display name。
12. 重新生成成功后，`is_stale` 应为 `false`。
13. 不得破坏已有上传播放、阿里云 ASR、转写时间轴和 AI 总结功能。

## API Design

### PATCH `/api/recordings/{recording_id}/segments/{segment_id}`

请求：

```json
{
  "text": "修改后的转写内容"
}
```

响应：

```json
{
  "id": "segment-id",
  "recording_id": "recording-id",
  "speaker_label": "Channel 0",
  "display_speaker_label": "主持人",
  "start_time": 0,
  "end_time": 7,
  "text": "修改后的转写内容",
  "source": "aliyun",
  "is_edited": true,
  "created_at": "2026-05-27T00:00:00+00:00",
  "updated_at": "2026-05-27T00:01:00+00:00"
}
```

错误：

- `404`：录音或 segment 不存在。
- `400`：文本为空或过长。

### GET `/api/recordings/{recording_id}/speaker-labels`

响应当前录音下出现过的 speaker labels 和显示名：

```json
[
  {
    "source_label": "Channel 0",
    "display_name": "主持人",
    "segment_count": 15,
    "created_at": "2026-05-27T00:00:00+00:00",
    "updated_at": "2026-05-27T00:01:00+00:00"
  }
]
```

### PATCH `/api/recordings/{recording_id}/speaker-labels`

请求：

```json
{
  "source_label": "Channel 0",
  "display_name": "主持人"
}
```

响应更新后的 label 映射。`display_name` 为空时清除自定义显示名。

### GET `/api/recordings/{recording_id}/analysis`

响应保留现有 AI 总结结构，新增：

```json
{
  "is_stale": true
}
```

### POST `/api/recordings/{recording_id}/analyze`

继续返回 AI 总结。生成时必须使用最新 segment 文本，并在 transcript context 中优先使用 speaker display name。

## Data Model

### transcript_segments

新增字段：

- `is_edited` boolean，默认 `false`。
- `updated_at` datetime，默认创建时间，保存编辑时更新。

### speaker_labels

新增表：

- `id`
- `recording_id`
- `source_label`
- `display_name`
- `created_at`
- `updated_at`

约束：

- `(recording_id, source_label)` 唯一。
- `display_name` 最长 100 字符。

### recording_analyses

不新增字段。`is_stale` 通过比较最新 AI 总结 `updated_at` 与该录音下最新 `transcript_segments.updated_at`、`speaker_labels.updated_at` 动态计算。

## Frontend Interaction

1. 每条 segment 旁边显示“编辑”按钮。
2. 点击“编辑”后展示文本输入区和“保存 / 取消”。
3. 保存成功后当前 segment 立即更新，并显示已编辑状态。
4. speaker/channel 区域显示当前录音出现过的 labels。
5. 每个 label 提供输入框和“保存名称”按钮。
6. 保存名称后，所有相同 source label 的 segments 立即显示新名称。
7. 如果已有 AI 总结，编辑 segment 或 speaker label 后立即显示过期提示。
8. 重新生成 AI 总结后清除过期提示。
9. UI 保持简洁，不做复杂视觉设计。

## Acceptance Criteria

1. 原有上传播放功能仍然可用。
2. 阿里云 ASR 真实转写仍然可用。
3. AI 总结仍然可用。
4. 用户可以编辑某条 segment 文本。
5. 编辑后刷新页面，修改仍然存在。
6. 用户可以把 `Channel 0` 重命名为“主持人”等名称。
7. 重命名后所有相关 segments 显示新名称。
8. 刷新页面后 speaker 重命名仍然存在。
9. 修改 transcript 后，已有 AI 总结区域显示“可能过期”的提示。
10. 重新生成 AI 总结后，使用修改后的 transcript 内容。
11. 重新生成 AI 总结后，过期提示消失。
12. 前端 build/lint 通过。
13. 后端测试通过。
14. OpenSpec tasks.md 已更新。

## Out of Scope

- 不做说话人分离算法。
- 不自动识别谁是谁。
- 不做 FunASR 本地部署。
- 不做游戏专用复盘模式。
- 不做高光片段。
- 不做视频导出。
- 不做登录系统。
- 不做权限系统。
- 不做复杂 UI 重设计。
- 不做长音频分块总结。

## Risks / Trade-offs

- 使用 display name 映射而不是直接改写 `speaker_label`，可以保留 ASR 原始输出，但前端需要同时处理原始 label 和显示名。
- `is_stale` 动态计算避免给 `recording_analyses` 增加字段，但依赖所有转写和 speaker label 修改都正确更新 `updated_at`。
- 修改后不自动重新生成 AI 总结，避免用户不知情地触发真实 LLM 成本；改为显式提示用户重新生成。

