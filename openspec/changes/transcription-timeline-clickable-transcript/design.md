## Context（背景）

`audio-upload-playback` 已经提供录音上传、保存、列表和播放能力。当前 `Recording` 模型中有 nullable `duration` 字段，但上传阶段尚未提取音频时长。本变更只做 mock 转写时间轴，不接真实 ASR、Whisper、说话人分离或 AI 总结。

前端当前是单页实现，录音列表中的每条录音都有一个原生 HTML audio 控件。本变更优先扩展现有页面，避免引入录音详情页和复杂路由。

## Goals / Non-Goals（目标 / 非目标）

**目标：**

- 为已存在录音生成固定模板的 mock 转写片段。
- 将转写片段持久化到 SQLite，页面刷新后仍可读取。
- 在前端按时间顺序展示转写时间轴。
- 点击 segment 后跳转当前录音播放器到 `segment.start_time`。
- 播放过程中高亮当前时间落入的 segment。

**非目标：**

- 不接真实 ASR、Whisper、WhisperX、faster-whisper。
- 不接 pyannote 或任何说话人分离。
- 不生成 AI 总结、高光片段或实时字幕。
- 不做登录、支付、复杂权限或复杂 UI。

## Decisions（技术决策）

1. 新增 `TranscriptSegment` 表并通过 `recording_id` 关联 `Recording`。

   原因：segments 需要独立排序、查询、重建和未来扩展，单独表比塞进 recording JSON 字段更清晰。

2. mock 生成采用“删除旧 segments 后重建”的策略。

   原因：这让 `POST /api/recordings/{recording_id}/segments/mock` 结果可预测，避免用户重复点击生成按钮时出现重复内容。

3. mock 模板使用 0 到 24 秒的固定片段；如果未来 recording 有 `duration`，生成时不得超过该时长。

   原因：当前上传流程不提取音频时长，因此先使用 0-30 秒内的固定时间轴。若 `duration` 存在，则跳过或裁剪超过时长的片段，保证时间不越界。

4. 前端继续在当前页面扩展，不新增详情页。

   原因：本变更目标是打通最小功能闭环，当前页面已经有录音列表和播放器，局部扩展能减少重构风险。

## Risks / Trade-offs（风险 / 权衡）

- mock segments 不是音频真实内容 -> 页面文案和 API 命名明确标记为 mock，不让它看起来像真实识别结果。
- 当前录音可能少于固定模板总时长 -> 有 duration 时按 duration 限制；无 duration 时采用固定 0-24 秒临时策略。
- 浏览器可能阻止脚本触发 `audio.play()` -> 点击 segment 时仍设置 `currentTime`，播放失败时给出可恢复提示。
- 单页状态会变多 -> 只抽取少量 helper 和类型，不做大规模重构。

## Migration Plan（迁移计划）

本变更新增 `transcript_segments` 表。开发环境通过现有 `init_db()` 创建缺失表，不迁移或修改已有 `recordings` 数据。

回滚时可以删除新增路由、前端 segments 展示逻辑和 `transcript_segments` 表；已上传音频和 `recordings` 表不受影响。
