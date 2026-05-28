## ADDED Requirements

### Requirement: 生成整场 session 总结
系统 SHALL 允许用户为一个长录音 session 生成整场总结，并将结果持久化。

#### Scenario: 成功生成整场总结
- **WHEN** session 下存在至少一个带有 transcript segments 的 chunk
- **THEN** 系统 SHALL 按 `chunk_index` 升序聚合 chunk 转写和 chunk AI 总结
- **AND** 系统 SHALL 调用当前 LLM provider 生成结构化整场总结
- **AND** 系统 SHALL 保存 provider、model、summary JSON、raw response 和生成时间

#### Scenario: session 没有 chunks
- **WHEN** 用户请求为没有 chunks 的 session 生成整场总结
- **THEN** 系统 SHALL 返回清晰的 400 错误

#### Scenario: chunks 全部缺少转写
- **WHEN** session 下 chunks 均没有 transcript segments
- **THEN** 系统 SHALL 返回清晰的 400 错误，提示先完成 chunk 转写

### Requirement: 读取整场 session 总结
系统 SHALL 允许前端读取已有整场总结。

#### Scenario: 已存在整场总结
- **WHEN** 前端调用 `GET /api/recording-sessions/{session_id}/summary`
- **THEN** 系统 SHALL 返回该 session 最新整场总结
- **AND** 响应 SHALL 包含 `title`、`summary`、`key_points`、`timeline`、`chunk_summaries`、`notes`、`provider`、`model` 和 `is_stale`

#### Scenario: 不存在整场总结
- **WHEN** 前端读取没有 summary 的 session
- **THEN** 系统 SHALL 返回 404 错误

### Requirement: 导出整场总结
系统 SHALL 支持将已有整场总结导出为 Markdown 和 TXT。

#### Scenario: 导出 Markdown
- **WHEN** 前端调用 `GET /api/recording-sessions/{session_id}/export.md`
- **THEN** 系统 SHALL 返回 Markdown 文本
- **AND** 内容 SHALL 包含标题、整体总结、重点信息、时间线、分段摘要、备注和生成信息

#### Scenario: 导出 TXT
- **WHEN** 前端调用 `GET /api/recording-sessions/{session_id}/export.txt`
- **THEN** 系统 SHALL 返回纯文本内容
- **AND** 内容 SHALL 包含标题、整体总结、重点信息、时间线、分段摘要、备注和生成信息

### Requirement: 前端展示整场总结
前端 SHALL 在长录音 session 区域展示整场总结入口和结果。

#### Scenario: 空状态
- **WHEN** session 还没有整场总结
- **THEN** 前端 SHALL 显示空状态并提供“生成整场总结”按钮

#### Scenario: 生成中状态
- **WHEN** 用户点击“生成整场总结”
- **THEN** 前端 SHALL 显示“正在生成整场总结...”并防止重复提交

#### Scenario: 展示成功结果
- **WHEN** 后端返回整场总结
- **THEN** 前端 SHALL 展示标题、整体总结、重点信息、时间线、分段摘要和备注
- **AND** 前端 SHALL 提供复制 Markdown、下载 Markdown 和下载 TXT 操作

### Requirement: 整场总结时间线跳转
前端 SHALL 支持点击整场总结时间线条目跳转到对应 chunk 音频时间。

#### Scenario: 点击时间线条目
- **WHEN** 用户点击带有 `start_time` 的整场总结时间线条目
- **THEN** 前端 SHALL 找到覆盖该 session offset 的 chunk
- **AND** 前端 SHALL 将该 chunk 对应 audio 播放器跳转到 chunk 内相对时间

### Requirement: 整场总结过期提示
系统 SHALL 在 chunk 内容更新后标记已有整场总结可能过期。

#### Scenario: chunk AI 总结重新生成
- **WHEN** 某个 chunk recording 重新生成 AI 总结
- **THEN** 系统 SHALL 将关联 session summary 标记为 stale

#### Scenario: chunk 转写或 speaker label 修改
- **WHEN** 某个 chunk recording 的 transcript segment 或 speaker label 被修改
- **THEN** 系统 SHALL 将关联 session summary 标记为 stale
- **AND** 前端 SHALL 显示“部分分段内容已更新，整场总结可能不是最新结果，请重新生成。”
