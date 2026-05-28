# auto-transcribe-and-summary

## ADDED Requirements

### Requirement: Auto analysis toggle

页面必须提供自动分析开关。开关关闭时，上传或录音完成后不得自动执行 ASR；开关开启时，上传或录音完成后必须自动执行 ASR 和 AI 总结。

#### Scenario: Auto analysis disabled

- **GIVEN** 自动分析开关关闭
- **WHEN** 用户上传音频或完成浏览器录音上传
- **THEN** 系统只创建 recording
- **AND** 不自动调用 ASR

#### Scenario: Auto analysis enabled

- **GIVEN** 自动分析开关开启
- **WHEN** 用户上传音频或完成浏览器录音上传
- **THEN** 系统自动调用 ASR
- **AND** ASR 成功后自动调用 AI 总结

### Requirement: Auto analysis state display

页面必须显示自动分析状态，并区分上传、转写、总结、完成和失败。

#### Scenario: Show processing state

- **GIVEN** 自动分析正在运行
- **WHEN** 系统进入转写或总结步骤
- **THEN** 页面显示对应状态

### Requirement: Stop on ASR failure

ASR 失败时，自动流程不得继续执行 AI 总结。

#### Scenario: ASR fails

- **GIVEN** 自动分析已开始
- **WHEN** ASR 接口返回错误
- **THEN** 页面显示 ASR 错误
- **AND** 不调用 AI 总结接口

### Requirement: Preserve transcript on summary failure

AI 总结失败时，必须保留已经成功生成的转写结果。

#### Scenario: Summary fails

- **GIVEN** ASR 已成功生成 segments
- **WHEN** AI 总结接口返回错误
- **THEN** 页面显示总结错误
- **AND** 页面继续展示已生成的转写时间轴

