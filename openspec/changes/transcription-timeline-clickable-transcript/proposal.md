## Why（为什么）

当前项目已经打通“音频上传 -> 后端保存 -> 数据库记录 -> 前端列表展示 -> 网页播放”。下一步需要在不接入真实 ASR 或 AI 的前提下，把播放器升级为可复盘的转写时间轴，让用户可以围绕一条录音查看 mock 片段并点击跳转到对应时间。

## What Changes（变更内容）

- 新增 transcript segment 数据模型，用 SQLite 持久化录音的转写片段。
- 新增获取某条录音 segments 的后端 API。
- 新增为某条录音生成 mock segments 的后端 API。
- mock 生成策略为幂等重建：每次生成前删除该录音已有 segments，再写入固定模板，避免重复片段。
- 前端在录音卡片中展示“生成 mock 转写”按钮和转写时间轴。
- 用户点击某条 segment 时，当前录音的 HTML audio 播放器跳转到 `segment.start_time` 并尝试播放。
- 播放过程中根据 `audio.currentTime >= start_time && audio.currentTime < end_time` 自动高亮当前 segment。

## Capabilities（能力范围）

### New Capabilities（新增能力）

- `transcription-timeline`: 覆盖 mock 转写片段的数据模型、生成、持久化、查询和按时间顺序展示。
- `clickable-transcript`: 覆盖点击转写片段跳转音频时间、播放尝试和当前片段高亮。

### Modified Capabilities（修改能力）

- 无。

## Impact（影响范围）

- Backend：新增 transcript segment SQLAlchemy 模型、序列化逻辑和录音 segments API。
- Database：新增 `transcript_segments` 表。
- Frontend：扩展当前录音列表页面，加入 mock 转写生成按钮、转写时间轴和 audio ref 控制。
- Tests：新增后端 segment API 测试，并确保现有音频上传/播放测试继续通过。
- OpenSpec：新增本 change 的 proposal、design、spec 和 tasks。
