## ADDED Requirements

### Requirement: MVP 主链路稳定化
系统 SHALL 保持上传、播放、转写、AI 总结、编辑、录音、长录音和整场总结主链路可用。

#### Scenario: 自动测试通过
- **WHEN** 开发者运行后端测试和前端 lint/build
- **THEN** 系统 SHALL 不出现测试失败、TypeScript 构建失败或 lint 失败

#### Scenario: API 失败不导致页面崩溃
- **WHEN** 任一主链路 API 返回错误
- **THEN** 前端 SHALL 显示可读错误
- **AND** 页面 SHALL 保持可继续操作

### Requirement: 友好的状态展示
前端 SHALL 为主链路显示明确的 loading、empty、error 和 success 状态。

#### Scenario: 空状态展示
- **WHEN** 当前没有录音、转写、AI 总结、session chunks 或整场总结
- **THEN** 前端 SHALL 显示对应的空状态提示

#### Scenario: 失败状态展示
- **WHEN** 上传、ASR、AI 总结、录音、chunk 分析或导出失败
- **THEN** 前端 SHALL 显示可读错误，并保留可重试入口或手动操作入口

### Requirement: 数据来源可辨识
前端 SHALL 清楚展示 mock/真实 provider、model 或 source。

#### Scenario: 展示 provider model source
- **WHEN** 页面展示转写、AI 总结或整场总结
- **THEN** 页面 SHALL 显示对应 source、provider 或 model

### Requirement: 手动端到端验收文档
项目 SHALL 提供完整手动 E2E 验收文档。

#### Scenario: 查看验收文档
- **WHEN** 用户打开 `docs/manual-e2e-test.md`
- **THEN** 文档 SHALL 包含环境变量、启动命令、PUBLIC_BASE_URL、上传音频、浏览器录音、长录音、整场总结、导出和常见问题排查

