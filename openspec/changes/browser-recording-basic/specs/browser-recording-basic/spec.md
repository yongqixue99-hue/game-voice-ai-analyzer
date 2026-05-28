# browser-recording-basic

## ADDED Requirements

### Requirement: Browser microphone recording

页面必须提供浏览器麦克风录音入口，允许用户开始录音、暂停/继续、停止并上传。

#### Scenario: Record and upload audio

- **GIVEN** 用户使用支持 `MediaRecorder` 的浏览器
- **WHEN** 用户允许麦克风权限并完成录音
- **THEN** 前端生成 `.webm` 音频文件
- **AND** 复用现有上传接口创建 recording
- **AND** 新 recording 出现在录音列表中

### Requirement: Recording status and duration

录音区域必须显示当前录音状态和录音时长。

#### Scenario: Show recording duration

- **GIVEN** 用户正在录音
- **WHEN** 录音持续进行
- **THEN** 页面显示“录音中”
- **AND** 页面显示不断增长的录音时长

### Requirement: Permission and compatibility errors

如果浏览器不支持网页录音或用户拒绝麦克风权限，页面必须展示清晰错误。

#### Scenario: Unsupported browser

- **GIVEN** 当前浏览器不支持 `MediaRecorder`
- **WHEN** 用户点击“开始录音”
- **THEN** 页面显示“当前浏览器不支持网页录音，请换用 Chrome / Edge。”

#### Scenario: Microphone permission denied

- **GIVEN** 用户拒绝麦克风权限
- **WHEN** 页面尝试开始录音
- **THEN** 页面显示“无法访问麦克风，请检查浏览器权限。”

### Requirement: Reuse upload main path

浏览器录音必须复用现有音频上传接口，不新增专用录音后端 API。

#### Scenario: Upload webm recording

- **GIVEN** 前端生成 `browser-recording-YYYYMMDD-HHmmss.webm`
- **WHEN** 前端上传该文件
- **THEN** 后端通过现有 `POST /api/recordings/upload` 保存音频和 recording 记录

