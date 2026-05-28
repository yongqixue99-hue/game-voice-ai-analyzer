## 1. 后端数据模型

- [x] 1.1 新增 `TranscriptSegment` SQLAlchemy 模型，字段包含 `id`、`recording_id`、`speaker_label`、`start_time`、`end_time`、`text`、`created_at`。
- [x] 1.2 确保 `init_db()` 可以创建 `transcript_segments` 表且不破坏现有 `recordings` 表。
- [x] 1.3 添加 segment 序列化逻辑，时间戳按 ISO 字符串返回。

## 2. 后端 API

- [x] 2.1 实现 `GET /api/recordings/{recording_id}/segments`，录音不存在返回 `404`。
- [x] 2.2 实现 `POST /api/recordings/{recording_id}/segments/mock`，录音不存在返回 `404`。
- [x] 2.3 mock 生成前删除该录音旧 segments，再写入固定模板，避免重复生成。
- [x] 2.4 如果 recording 有 `duration`，mock segments 不得超过该时长；如果没有 duration，使用 0-24 秒固定模板。
- [x] 2.5 添加后端测试，覆盖 segments 查询、mock 生成、重复生成、不存在录音错误和原有上传能力。

## 3. 前端时间轴

- [x] 3.1 添加 `TranscriptSegment` 类型和 segment API client。
- [x] 3.2 页面加载录音列表后，为每条录音加载 segments。
- [x] 3.3 每条录音提供“生成 mock 转写”按钮，并在成功后刷新该录音 segments。
- [x] 3.4 前端按时间顺序展示每条 segment 的时间范围、`speaker_label` 和 `text`。
- [x] 3.5 没有 segments 时展示“暂无转写，请先生成 mock 转写”空状态。

## 4. 可点击播放

- [x] 4.1 为每条录音维护稳定 audio ref。
- [x] 4.2 点击 segment 时设置 `audio.currentTime = segment.start_time` 并调用 `audio.play()`。
- [x] 4.3 如果浏览器阻止自动播放，展示可恢复提示。
- [x] 4.4 监听 audio `timeupdate`，按 `currentTime >= start_time && currentTime < end_time` 高亮当前 segment。

## 5. 验证

- [x] 5.1 验证原有音频上传、列表和播放功能仍可用。
- [x] 5.2 验证 mock segments 可生成、持久化、刷新后仍展示。
- [x] 5.3 验证点击 segment 会跳转播放器时间。
- [x] 5.4 验证播放时当前 segment 自动高亮。
- [x] 5.5 运行后端测试、前端 lint/build 和 OpenSpec 校验。
