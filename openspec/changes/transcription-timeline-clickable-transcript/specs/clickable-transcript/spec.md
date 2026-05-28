# 可点击转写片段

## Goal（目标）

让用户点击转写时间轴中的任意 segment 后，当前录音播放器跳转到该片段开始时间，并在播放过程中高亮当前 segment。

## User Story（用户故事）

作为一个复盘游戏语音的玩家，我希望点击某句转写后立即回听对应时间点，并在播放时看到当前正在对应哪条转写片段。

## Requirements（需求摘要）

- 前端 MUST 使用稳定的 audio ref 控制当前录音播放器。
- 点击 segment MUST 设置 `audio.currentTime = segment.start_time`。
- 点击 segment SHOULD 调用 `audio.play()`；如果浏览器阻止自动播放，前端 MUST 给出可恢复提示。
- 播放过程中 MUST 使用 `currentTime >= start_time && currentTime < end_time` 判断当前 segment 并高亮。

## API Design（API 设计）

本能力不新增独立 API，依赖 `transcription-timeline` 中的：

- `GET /api/recordings/{recording_id}/segments`
- `POST /api/recordings/{recording_id}/segments/mock`
- 以及现有 `GET /api/recordings/{recording_id}/audio`

## Data Model（数据模型）

前端使用后端返回的 `TranscriptSegment`：

- `id`
- `recording_id`
- `speaker_label`
- `start_time`
- `end_time`
- `text`
- `created_at`

当前 segment 是派生 UI 状态，不单独持久化。

## ADDED Requirements

以下为本变更新增需求。

### Requirement: 点击 segment 跳转播放

系统 SHALL 允许用户点击 segment 后跳转当前录音播放器到 `segment.start_time`。

#### Scenario: 点击 segment 成功跳转

- **WHEN** 用户点击某条转写片段
- **THEN** 前端设置对应 audio 的 `currentTime` 为该片段 `start_time`

#### Scenario: 自动播放被阻止

- **WHEN** 用户点击 segment 后浏览器拒绝 `audio.play()`
- **THEN** 前端仍保留跳转后的时间，并展示可恢复提示

### Requirement: 播放时高亮当前 segment

系统 SHALL 在音频播放过程中根据当前播放时间高亮对应 segment。

#### Scenario: 当前时间落入 segment

- **WHEN** audio 的 `currentTime` 满足 `currentTime >= start_time && currentTime < end_time`
- **THEN** 前端高亮该 segment

#### Scenario: 当前时间不在任何 segment 内

- **WHEN** audio 的 `currentTime` 不属于任何 segment 时间范围
- **THEN** 前端不高亮任何 segment

## Acceptance Criteria（验收标准）

- 点击任意 segment，播放器跳转到对应 `start_time`。
- 点击 segment 后会尝试播放音频，若失败则展示提示。
- 播放过程中当前 segment 自动高亮。
- 没有 segments 时，不出现可点击时间轴并展示空状态。

## Out of Scope（不在范围内）

- 自动生成真实字幕。
- 实时字幕。
- 多轨音频。
- 波形图。
- 复杂播放器 UI。
- 键盘快捷键。

## Task List（任务列表）

- 为每条录音维护 audio ref。
- 实现 segment 点击跳转和播放尝试。
- 监听 `timeupdate` 更新当前播放时间。
- 按时间范围计算并高亮当前 segment。
