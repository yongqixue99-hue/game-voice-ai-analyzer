## 1. OpenSpec

- [x] 1.1 创建 `ai-summary-highlights` change 目录。
- [x] 1.2 编写 `proposal.md`、`spec.md`、`design.md` 和 `tasks.md`。

## 2. 后端数据模型与配置

- [x] 2.1 新增 LLM 相关环境变量读取。
- [x] 2.2 新增 `RecordingAnalysis` 模型和 `recording_analyses` 表。
- [x] 2.3 添加分析结果序列化逻辑。

## 3. 后端 LLM Provider

- [x] 3.1 新增独立 `llm.py` service。
- [x] 3.2 实现 prompt 构造和 transcript context 拼接。
- [x] 3.3 实现 `MockLLMProvider`。
- [x] 3.4 实现 DashScope/OpenAI provider 的配置校验和请求结构。
- [x] 3.5 实现 JSON 解析、字段补齐和基础校验。

## 4. 后端 API

- [x] 4.1 实现 `POST /api/recordings/{recording_id}/analyze`。
- [x] 4.2 实现 `GET /api/recordings/{recording_id}/analysis`。
- [x] 4.3 没有 segments 时返回“请先完成转写”。
- [x] 4.4 成功后保存并返回分析结果。
- [x] 4.5 添加后端测试覆盖 mock 成功、无 segments、缺 key 和持久化读取。

## 5. 前端

- [x] 5.1 增加 AI 分析类型定义和 API client。
- [x] 5.2 页面加载时读取已保存分析。
- [x] 5.3 增加“生成 AI 总结”按钮、loading 和错误状态。
- [x] 5.4 展示 title、summary、key_points、timeline_summary 和 notes。
- [x] 5.5 时间段摘要点击跳转播放器。

## 6. 验证

- [x] 6.1 运行后端测试。
- [x] 6.2 运行前端 lint/build。
- [x] 6.3 浏览器验证 mock 转写、AI 总结、刷新持久化和时间段跳转。

## 7. 简化为 AI 总结

- [x] 7.1 更新 OpenSpec，明确 AI 总结的新结构和非游戏模板原则。
- [x] 7.2 后端 schema 改为 `title`、`summary`、`key_points`、`timeline_summary`、`notes`。
- [x] 7.3 修改 LLM prompt，避免强行套游戏复盘模板。
- [x] 7.4 修改 mock provider 为通用 mock 总结。
- [x] 7.5 前端文案改为“AI 总结”和“生成 AI 总结”。
- [x] 7.6 前端删除/隐藏旧复盘模块，只展示新总结字段。
- [x] 7.7 兼容旧分析 JSON，不破坏已保存数据。
- [x] 7.8 运行后端测试和前端 lint/build。
