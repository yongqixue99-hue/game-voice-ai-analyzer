# browser-recording-basic 设计说明

## 前端录音策略

使用浏览器 `MediaRecorder` API：

1. 点击“开始录音”。
2. 检查 `navigator.mediaDevices.getUserMedia` 和 `window.MediaRecorder`。
3. 请求 `audio: true` 的麦克风 MediaStream。
4. 选择优先 MIME：
   - `audio/webm;codecs=opus`
   - `audio/webm`
   - 浏览器默认
5. 创建 `MediaRecorder`。
6. 收集 `dataavailable` chunks。
7. 停止时合并 chunks 成 Blob。
8. 包装成 `.webm` File。
9. 复用现有 `uploadRecording(formData)`。
10. 上传成功后调用 `loadRecordings()`。

## 状态设计

前端维护 `recordingStatus`：

- `idle`
- `requesting`
- `recording`
- `paused`
- `stopping`
- `uploading`
- `uploaded`
- `failed`

展示为中文：

- 未开始
- 请求权限中
- 录音中
- 已暂停
- 停止中
- 上传中
- 上传完成
- 失败

时长使用 `recordingStartedAt`、`recordingElapsedBeforePauseMs` 和 interval 计算，暂停时不继续增长。

## 资源释放

停止录音后必须：

- 调用 `MediaRecorder.stop()`。
- 在 `onstop` 完成后停止所有 `MediaStreamTrack`。
- 清空 recorder、stream 和 chunks ref。

组件卸载时也尝试释放 tracks，避免麦克风一直占用。

## 上传复用

前端生成：

```ts
new File([blob], filename, { type: "audio/webm" })
```

然后：

```ts
const formData = new FormData();
formData.append("file", file);
await uploadRecording(formData);
```

后端只需允许 `.webm` 和 `audio/webm`。

## 不做自动分析

虽然路线图里阶段 B 提到上传后“可以自动触发 ASR 和 AI 总结”，本 change 为基础录音能力，只保证上传后的 recording 可以继续手动使用现有 ASR 和 AI 总结按钮。自动转写和自动总结留给阶段 C `auto-transcribe-and-summary`。

