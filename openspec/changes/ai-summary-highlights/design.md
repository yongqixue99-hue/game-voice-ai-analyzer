# ai-summary-highlights 设计说明：AI 总结简化

## 存储兼容

继续使用 `recording_analyses.analysis_json` 保存结构化 JSON，不改变表结构。

新生成数据保存为：

- `title`
- `summary`
- `key_points`
- `timeline_summary`
- `notes`

旧数据可能包含 `main_events`、`key_moments`、`funny_moments`、`conflict_moments`、`communication_issues`、`player_traits`、`suggestions`。后端序列化时会规范化为新结构；前端只展示新结构。

## Provider 调整

`MockLLMProvider` 改为通用 mock 总结：

```json
{
  "title": "录音内容摘要",
  "summary": "这段录音主要围绕若干话题展开，具体内容取决于转写文本。当前为 mock 总结，仅用于验证展示流程。",
  "key_points": [
    "已成功读取转写文本",
    "AI 总结模块可以正常展示",
    "后续可接入真实 LLM 生成自然总结"
  ],
  "timeline_summary": [],
  "notes": [
    "当前为 mock 结果，不代表真实内容分析"
  ]
}
```

DashScope/OpenAI provider 保留，但 prompt 改成通用音频总结。

## Prompt 调整

Prompt 不再定位为“游戏开黑语音复盘助手”，而是“音频转写总结助手”。

内部可判断内容类型，但输出不展示内容类型字段。这样能帮助模型区分会议、访谈、新闻、讲解、闲聊或游戏语音，同时避免 UI 生硬。

## 前端调整

页面只展示：

- 标题
- 总结
- 重点信息
- 时间段摘要
- 备注 / 待确认信息

删除或隐藏旧模块：

- 本段语音主要事件
- 关键片段
- 搞笑片段
- 冲突/情绪波动片段
- 沟通问题
- 玩家沟通风格
- 改进建议

时间段摘要可点击跳转到 `start_time`，继续复用现有 audio ref。
