## Goal

将当前模板化的“AI 复盘”简化为自然、克制、通用的“AI 总结”。系统只根据 transcript segments 总结录音内容，不强行判断为游戏语音，不强行输出搞笑、冲突、高光、沟通问题或玩家风格。

## User Story

作为用户，我希望上传并转写一段录音后，点击“生成 AI 总结”，系统能根据真实转写自然概括内容。如果这段录音是访谈、新闻、讲解或闲聊，就按对应内容总结；如果信息不足，就明确说明信息较少，而不是套用游戏复盘模板。

## Requirements

- 页面文案从“AI 复盘”改为“AI 总结”。
- 按钮文案从“生成 AI 复盘”改为“生成 AI 总结”。
- 后端 `POST /api/recordings/{recording_id}/analyze` 保持不变，但返回结构改为通用总结结构。
- 后端 `GET /api/recordings/{recording_id}/analysis` 兼容读取旧数据，但新生成数据使用新结构。
- 新结构包含 `title`、`summary`、`key_points`、`timeline_summary`、`notes`。
- Prompt 必须强调录音不一定是游戏语音。
- Prompt 只允许根据转写中真实出现的信息总结，不编造。
- Prompt 不应强行寻找搞笑片段、冲突片段、玩家风格、沟通问题或高光。
- Prompt 不应使用“本局”“开团”“资源争夺”“团队协作”等游戏术语，除非转写内容确实出现类似语境。
- 信息不足时应明确说明“信息较少，无法进一步判断”。
- `timeline_summary` 的时间范围必须来自已有 segments，可为空数组。
- 前端只展示标题、总结、重点信息、时间段摘要、备注/待确认信息。
- 旧字段如 `key_moments`、`funny_moments`、`conflict_moments`、`player_traits` 等可保留在旧数据里，但新 UI 不展示。

## API Design

### POST `/api/recordings/{recording_id}/analyze`

请求体：无。

成功响应：

```json
{
  "id": "analysis-id",
  "recording_id": "recording-id",
  "provider": "mock",
  "model": "mock-summary-v1",
  "title": "录音内容摘要",
  "summary": "对整段录音的自然总结",
  "key_points": ["重点信息 1"],
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

### GET `/api/recordings/{recording_id}/analysis`

返回最新保存的 AI 总结。旧分析数据会被规范化为新结构后返回，避免前端崩溃。

## Data Model

继续使用 `recording_analyses` 表，不新增表。

字段保持：

- `id`
- `recording_id`
- `provider`
- `model`
- `analysis_json`
- `raw_response_json`
- `created_at`
- `updated_at`

`analysis_json` 新 schema：

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

沿用现有 LLM provider 配置：

- `LLM_PROVIDER=mock | dashscope | openai`
- `DASHSCOPE_API_KEY`
- `DASHSCOPE_LLM_MODEL=qwen-plus`
- `DASHSCOPE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `OPENAI_API_KEY`
- `OPENAI_LLM_MODEL=gpt-4o-mini`
- `OPENAI_LLM_BASE_URL=https://api.openai.com/v1`
- `LLM_REQUEST_TIMEOUT_SECONDS=60`

## Prompt Design

提示词要求：

- 你是在总结一段音频转写，不一定是游戏语音。
- 先在内部判断内容类型：游戏语音、会议/访谈、闲聊、讲解、新闻/视频音频或其他。
- 不要在前端生硬展示“内容类型”，只把判断用于帮助总结。
- 不要套模板。
- 不要强行寻找搞笑、冲突、高光、沟通问题。
- 只总结转写中真实出现的信息。
- 不要使用“本局”“开团”“资源争夺”“团队协作”等游戏词，除非转写中确实出现类似内容。
- 如果转写内容很短或信息不足，要简短说明，不要硬分析。
- 输出必须是严格 JSON，不要 Markdown。
- 所有时间必须来自已有 transcript segments 的时间范围。
- 如果无法合理拆分 `timeline_summary`，可以返回空数组。
- 输出中文。

## Acceptance Criteria

- 页面按钮显示为“生成 AI 总结”。
- 页面模块标题显示为“AI 总结”。
- 前端不再展示搞笑片段、冲突片段、玩家沟通风格等固定模块。
- AI 输出不再强行套游戏模板。
- 对非游戏语音，可以自然总结内容。
- 对信息不足的录音，会说明信息有限，而不是硬凑分析。
- 原有上传、播放、ASR 转写功能不受影响。
- 点击时间段摘要时，如果有 `start_time`，可以继续跳转音频。
- 前端 build/lint 通过。
- 后端测试通过。
- `tasks.md` 已更新。

## Out of Scope

- 不做复杂复盘模板。
- 不做玩家心理、人格或身份判断。
- 不做说话人分离。
- 不做长音频分块总结。
- 不做实时分析。
- 不做视频导出。
- 不做复杂 UI 重设计。
- 不改变现有 `recording_analyses` 表结构。

## Risks / Trade-offs

- 简化输出会减少结构化“高光”信息，但更符合当前真实内容的泛化需求。
- 旧分析 JSON 可能含旧字段，前端需要兼容但不展示。
- 真实 LLM 仍可能输出非 JSON 或模板化内容，后端需要继续做 JSON 解析和字段规范化。
