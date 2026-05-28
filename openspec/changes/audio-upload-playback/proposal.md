## Why（为什么）

在转写、总结和沟通风格分析真正可用之前，MVP 需要先建立一个可靠的录音文件基础流程。这个变更实现第一条离线闭环：用户上传音频，后端保存文件，应用展示录音列表，浏览器可以回放录音。

## What Changes（变更内容）

- 新增音频上传 API，接收本地音频文件并保存到服务端本地存储。
- 新增录音元数据的 SQLite 持久化，让已上传文件可以被列表展示和查询。
- 新增录音列表 API。
- 新增用于向浏览器返回或流式传输已保存音频文件的 API。
- 新增前端视图，支持选择本地音频文件、上传、查看录音列表，并播放选中的录音。

## Capabilities（能力范围）

### New Capabilities（新增能力）

- `audio-upload-playback`: 覆盖本地音频上传、后端文件保存、录音元数据、录音列表和浏览器播放。

### Modified Capabilities（修改能力）

- 无。

## Impact（影响范围）

- Frontend：上传表单、录音列表、HTML audio 播放器联动。
- Backend：用于上传、列表、元数据查询和音频文件响应的 FastAPI 路由。
- Database：用于录音元数据的 SQLite 表。
- Storage：`storage/audio/` 下的本地音频文件。
- Tests：后端 API 测试和重点前端交互检查。
