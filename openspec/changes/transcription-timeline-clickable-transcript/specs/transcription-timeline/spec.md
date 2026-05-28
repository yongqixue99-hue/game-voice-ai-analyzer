# Mock 转写时间轴

## Goal（目标）

为已上传录音创建、持久化并展示 mock 转写时间轴，让用户能在不接真实 ASR 的情况下体验录音复盘的时间轴形态。

## User Story（用户故事）

作为一个复盘游戏语音的玩家，我希望为已上传录音生成一组 mock 转写片段，并在页面刷新后继续看到这些片段，以便先验证时间轴复盘体验。

## Requirements（需求摘要）

- 后端 MUST 为录音保存 transcript segment。
- 后端 MUST 支持查询某条录音的 segments。
- 后端 MUST 支持为某条录音重建 mock segments。
- 前端 MUST 能展示空状态和按时间顺序排列的转写时间轴。

## API Design（API 设计）

- `GET /api/recordings/{recording_id}/segments`
  - 响应 `200`：该录音的 segment JSON 列表，按 `start_time` 升序排序。
  - 响应 `404`：录音不存在。
- `POST /api/recordings/{recording_id}/segments/mock`
  - 响应 `201`：新生成的 segment JSON 列表，按 `start_time` 升序排序。
  - 行为：如果该录音已有 segments，先删除旧 segments，再创建新的 mock segments，避免重复生成。
  - 响应 `404`：录音不存在。

## Data Model（数据模型）

SQLite 表：`transcript_segments`

- `id`：字符串 UUID 主键。
- `recording_id`：所属录音 ID，关联 `recordings.id`。
- `speaker_label`：说话人展示标签，例如 `Speaker 1`。
- `start_time`：片段开始时间，单位秒。
- `end_time`：片段结束时间，单位秒。
- `text`：片段转写文本。
- `created_at`：创建时间戳。

mock 模板：

- `0` - `3`，`Speaker 1`：兄弟们这波可以打
- `3` - `7`，`Speaker 2`：别急，对面打野不见了
- `7` - `12`，`Speaker 1`：我有大，我先开
- `12` - `18`，`Speaker 3`：我绕后了，等我位置
- `18` - `24`，`Speaker 2`：可以可以，直接开

临时策略：当前上传流程没有提取音频 `duration` 时，使用上述 0-24 秒固定模板。若未来 `recording.duration` 存在，mock 生成不得创建 `start_time >= duration` 的片段，并且 `end_time` MUST 不超过 `duration`。

## ADDED Requirements

以下为本变更新增需求。

### Requirement: 保存转写片段

系统 SHALL 使用 SQLite 为录音持久化 transcript segment。

#### Scenario: segment 被保存

- **WHEN** 后端为一条存在的录音生成 mock segments
- **THEN** SQLite 中存在多条带 `recording_id`、`speaker_label`、`start_time`、`end_time`、`text` 和 `created_at` 的 segment 记录

### Requirement: 查询转写时间轴

系统 SHALL 提供接口查询某条录音的转写片段，并按开始时间升序返回。

#### Scenario: 查询已有 segments

- **WHEN** 用户请求已有 mock 转写的录音 segments
- **THEN** 后端返回按 `start_time` 升序排列的 segment 列表

#### Scenario: 查询不存在录音的 segments

- **WHEN** 用户请求不存在的 `recording_id` 的 segments
- **THEN** 后端返回 `404`

### Requirement: 生成 mock 转写片段

系统 SHALL 为已存在录音生成固定模板 mock segments。

#### Scenario: 首次生成 mock segments

- **WHEN** 用户对一条无 segments 的录音调用 mock 生成接口
- **THEN** 后端创建固定模板 segments 并返回生成结果

#### Scenario: 重新生成 mock segments

- **WHEN** 用户对一条已有 segments 的录音再次调用 mock 生成接口
- **THEN** 后端先删除该录音旧 segments，再创建新的 mock segments，且不会产生重复片段

### Requirement: 展示转写时间轴

系统 SHALL 在前端为录音展示转写时间轴或友好空状态。

#### Scenario: 展示已有时间轴

- **WHEN** 一条录音已有 segments
- **THEN** 前端按时间顺序展示时间范围、`speaker_label` 和 `text`

#### Scenario: 展示空状态

- **WHEN** 一条录音没有 segments
- **THEN** 前端展示“暂无转写，请先生成 mock 转写”一类的友好提示

## Acceptance Criteria（验收标准）

- 可以为已上传录音生成 mock 转写片段。
- mock 生成接口重复调用不会产生重复片段。
- segments 被保存到 SQLite。
- 页面刷新后，已生成 segments 仍然存在。
- 前端按 `start_time` 升序展示转写时间轴。
- 不存在的 `recording_id` 返回 `404`。

## Out of Scope（不在范围内）

- 真实 ASR。
- Whisper、WhisperX、faster-whisper。
- pyannote 或说话人分离。
- AI 总结。
- 高光片段。
- 实时录音。
- 实时字幕。
- 登录系统。
- 支付系统。
- 复杂 UI 设计。

## Task List（任务列表）

- 新增 `TranscriptSegment` SQLAlchemy 模型和数据库表。
- 实现 segments 查询接口。
- 实现 mock segments 重建接口。
- 前端加载、生成并展示 segments。
- 添加后端基础测试。
