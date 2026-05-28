## 1. OpenSpec

- [x] 1.1 创建 `transcript-editing-speaker-labels` change。
- [x] 1.2 编写 `proposal.md`、`spec.md`、`design.md`、`tasks.md`。

## 2. 后端数据模型与迁移

- [x] 2.1 为 `TranscriptSegment` 增加 `is_edited`、`updated_at`。
- [x] 2.2 新增 `SpeakerLabel` 模型和 `speaker_labels` 表。
- [x] 2.3 增加 SQLite 最小 schema migration。

## 3. 后端 API

- [x] 3.1 `GET /api/recordings/{recording_id}/segments` 返回 `display_speaker_label`、`is_edited`、`updated_at`。
- [x] 3.2 实现 `PATCH /api/recordings/{recording_id}/segments/{segment_id}`。
- [x] 3.3 实现 `GET /api/recordings/{recording_id}/speaker-labels`。
- [x] 3.4 实现 `PATCH /api/recordings/{recording_id}/speaker-labels`。
- [x] 3.5 补充不存在 recording/segment/label 的错误处理。

## 4. AI 总结联动

- [x] 4.1 AI 总结 prompt 使用 speaker display name。
- [x] 4.2 `GET /analysis` 和 `POST /analyze` 返回 `is_stale`。
- [x] 4.3 修改 segment 或 speaker label 后可判断已有总结过期。

## 5. 前端

- [x] 5.1 增加 segment 编辑按钮、保存/取消交互。
- [x] 5.2 增加 speaker/channel 重命名入口。
- [x] 5.3 保存 segment 后立即更新页面并显示已编辑状态。
- [x] 5.4 保存 speaker label 后立即更新所有相关 segments 显示名。
- [x] 5.5 AI 总结区域显示过期提示。
- [x] 5.6 重新生成 AI 总结后清除过期提示。

## 6. 测试与验收

- [x] 6.1 添加后端测试覆盖 segment 编辑持久化。
- [x] 6.2 添加后端测试覆盖 speaker label 重命名持久化。
- [x] 6.3 添加后端测试覆盖 AI 总结 stale 计算和 display name prompt。
- [x] 6.4 运行后端测试。
- [x] 6.5 运行前端 lint/build。
- [x] 6.6 浏览器手动验收主要流程。
