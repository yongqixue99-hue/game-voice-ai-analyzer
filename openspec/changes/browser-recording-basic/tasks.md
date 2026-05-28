## 1. OpenSpec

- [x] 1.1 创建 `browser-recording-basic` change。
- [x] 1.2 编写 `proposal.md`、`spec.md`、`design.md`、`tasks.md`。
- [x] 1.3 补充 capability spec 文件。

## 2. 后端上传支持

- [x] 2.1 确认现有上传接口可复用。
- [x] 2.2 支持 `.webm` 扩展名。
- [x] 2.3 支持 `audio/webm` MIME。
- [x] 2.4 添加 webm 上传测试。

## 3. 前端录音状态

- [x] 3.1 新增录音状态类型和状态文案。
- [x] 3.2 增加 MediaRecorder、MediaStream、chunks refs。
- [x] 3.3 增加录音时长计算和显示。
- [x] 3.4 组件卸载时清理麦克风 tracks。

## 4. 前端录音交互

- [x] 4.1 新增“浏览器录音”区域。
- [x] 4.2 实现“开始录音”和麦克风权限请求。
- [x] 4.3 实现不支持 MediaRecorder 的提示。
- [x] 4.4 实现拒绝麦克风权限的提示。
- [x] 4.5 实现暂停/继续。
- [x] 4.6 实现停止录音。
- [x] 4.7 停止后生成 `.webm` File 并自动上传。
- [x] 4.8 上传成功后刷新录音列表。
- [x] 4.9 防止重复点击创建多个 recorder。

## 5. 验证

- [x] 5.1 运行后端测试。
- [x] 5.2 运行前端 lint/build。
- [x] 5.3 浏览器验证页面出现录音区域和基础状态。
- [ ] 5.4 手动验收麦克风录音、暂停/继续、停止上传和播放。
