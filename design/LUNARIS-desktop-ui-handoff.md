# LUNARIS 桌面端 UI 设计交付说明

## 设计来源

本目录包含 Pencil / pencli 生成的桌面端 UI 设计稿。

- 原始导出：`raw-export/export.zip`
- 页面截图：`screenshots/`

## 页面对应关系

- `screenshots/dashboard.png`：控制台
- `screenshots/session-detail.png`：会话详情
- `screenshots/recording-detail.png`：单段录音详情
- `screenshots/library.png`：历史记录
- `screenshots/settings.png`：设置
- `screenshots/mini-recorder.png`：迷你录音窗

## 当前实现目标

本阶段只将现有 Web 前端改造成桌面端风格 UI。

不要实现：
- Electron
- Tauri
- 系统托盘
- 真正悬浮窗
- 系统声音录制
- FunASR 本地部署

## 实现优先级

P0：
- 中文侧边栏
- 控制台
- 历史记录
- 会话列表
- 会话详情
- 单段录音详情
- 设置页
- 保持现有上传、录音、ASR、AI 总结、分段录音、整场总结功能可用

P1：
- 尽量贴近设计稿布局
- 首页突出“开始对局录制”
- 会话详情使用清晰的分段状态表格
- 录音详情使用左侧转写、右侧 AI 总结布局

P2：
- 迷你录音窗先做静态展示，不实现系统级悬浮

## 视觉方向

- 简体中文
- 白底 / 浅灰底
- 桌面效率工具风格
- 轻度偏游戏玩家
- 不要电竞霓虹风
- 不要营销官网风

## 状态颜色

- 已完成：绿色
- 进行中 / 转写中 / 总结中：蓝色
- 等待中：灰色
- 警告：橙色
- 失败：红色
