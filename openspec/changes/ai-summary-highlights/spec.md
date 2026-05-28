# ai-summary-highlights 规格：AI 总结

## Goal

把现有“AI 复盘”调整为通用“AI 总结”，让系统基于 transcript segments 自然总结录音内容，而不是套用游戏复盘、高光、冲突或玩家风格模板。

## User Story

用户完成转写后点击“生成 AI 总结”。系统读取时间轴文本，调用当前 LLM provider，生成中文自然总结。总结内容必须贴合实际转写；如果信息不足，应明确说明，避免硬凑分析。

## Requirements

1. 保留 `POST /api/recordings/{recording_id}/analyze`。
2. 保留 `GET /api/recordings/{recording_id}/analysis`。
3. 没有 transcript segments 时仍返回 `400`，提示“请先完成转写”。
4. 新生成的分析必须使用新 schema：`title`、`summary`、`key_points`、`timeline_summary`、`notes`。
5. `timeline_summary` 可为空；如果非空，每项必须包含 `start_time`、`end_time`、`summary`。
6. `timeline_summary` 时间必须来自已有 segments 时间范围。
7. mock provider 必须改为通用 mock 总结，不输出游戏模板。
8. DashScope/OpenAI provider prompt 必须强调不一定是游戏语音。
9. Prompt 禁止强行寻找搞笑片段、冲突片段、高光、沟通问题或玩家沟通风格。
10. Prompt 禁止编造转写中没有的信息。
11. 前端文案改为“AI 总结”和“生成 AI 总结”。
12. 前端只展示标题、总结、重点信息、时间段摘要、备注/待确认信息。
13. 前端不展示旧的主要事件、关键片段、搞笑片段、冲突片段、沟通问题、玩家风格、改进建议模块。
14. 旧数据如果只有旧字段，后端或前端要兼容，不崩溃。
15. 点击时间段摘要可以跳转播放器到对应 `start_time`。

## API Design

### POST `/api/recordings/{recording_id}/analyze`

成功：`201 Created`，返回 AI 总结。

### GET `/api/recordings/{recording_id}/analysis`

成功：`200 OK`，返回最新 AI 总结。

响应结构：

```json
{
  "id": "analysis-id",
  "recording_id": "recording-id",
  "provider": "mock",
  "model": "mock-summary-v1",
  "title": "录音内容摘要",
  "summary": "对整段录音的自然总结",
  "key_points": ["重点信息 1", "重点信息 2"],
  "timeline_summary": [
    {
      "start_time": 0,
      "end_time": 15,
      "summary": "这一时间段大致讲了什么"
    }
  ],
  "notes": ["信息不足或需要确认的地方"],
  "created_at": "2026-05-27T00:00:00+00:00",
  "updated_at": "2026-05-27T00:00:00+00:00"
}
```

## Data Model

继续复用 `recording_analyses.analysis_json` 保存 JSON，不改表结构。

新 JSON schema：

```json
{
  "title": "一句话标题",
  "summary": "对整段录音的自然总结",
  "key_points": ["重点信息 1", "重点信息 2"],
  "timeline_summary": [
    {
      "start_time": 0,
      "end_time": 15,
      "summary": "这一时间段大致讲了什么"
    }
  ],
  "notes": ["信息不足或需要确认的地方"]
}
```

## Environment Variables

沿用：

```bash
LLM_PROVIDER=mock
DASHSCOPE_API_KEY=replace-with-your-key
DASHSCOPE_LLM_MODEL=qwen-plus
DASHSCOPE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=replace-with-your-key
OPENAI_LLM_MODEL=gpt-4o-mini
OPENAI_LLM_BASE_URL=https://api.openai.com/v1
LLM_REQUEST_TIMEOUT_SECONDS=60
```

## Prompt Design

System prompt：

- 你是音频转写总结助手。
- 这段音频不一定是游戏语音。
- 只根据用户提供的 transcript segments 总结。
- 不要编造没出现的信息。
- 不要做心理、人格、医学判断。
- 只输出严格 JSON，不要 Markdown。

User prompt：

- 先在内部判断内容类型：游戏语音、会议/访谈、闲聊、讲解、新闻/视频音频或其他。
- 不要在输出中生硬展示内容类型。
- 不要套游戏模板。
- 不要强行寻找搞笑、冲突、高光、沟通问题或玩家风格。
- 不要使用“本局”“开团”“资源争夺”“团队协作”等游戏词，除非转写中确实出现类似内容。
- 如果信息不足，明确说“信息较少，无法进一步判断”。
- 所有时间必须来自已有 segments 的时间范围。
- 如果无法合理拆分 `timeline_summary`，返回空数组。
- 输出中文。

## Acceptance Criteria

1. 页面按钮显示为“生成 AI 总结”。
2. 页面模块标题显示为“AI 总结”。
3. 前端不再展示搞笑片段、冲突片段、玩家沟通风格等固定模块。
4. AI 输出不再强行套游戏模板。
5. 对非游戏语音，可以自然总结内容。
6. 对信息不足的录音，会说明信息有限，而不是硬凑分析。
7. 原有上传、播放、ASR 转写功能不受影响。
8. 点击时间段摘要时，如果有 `start_time`，可以继续跳转音频。
9. 前端 build/lint 通过。
10. 后端测试通过。
11. OpenSpec tasks 已更新。

## Out of Scope

- 不做复杂游戏复盘。
- 不做搞笑/冲突/玩家风格等固定模块。
- 不做说话人分离。
- 不做实时总结。
- 不做复杂 UI 重设计。
- 不改变已有 `recording_analyses` 表结构。

## Risks / Trade-offs

- 新结构更简洁，但不再提供高光/冲突等专项分类。
- 旧 JSON 数据需要兼容读取。
- 真实 LLM 可能仍有模板化倾向，需要通过 prompt 和 mock 示例收敛。
