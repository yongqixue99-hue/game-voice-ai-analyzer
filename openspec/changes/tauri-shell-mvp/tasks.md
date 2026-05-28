## 1. OpenSpec

- [x] 1.1 创建 `tauri-shell-mvp` change。
- [x] 1.2 编写 `proposal.md`。
- [x] 1.3 编写 `design.md`。
- [x] 1.4 编写根目录 `spec.md`。
- [x] 1.5 编写 capability spec 文件。
- [x] 1.6 实现完成后更新本任务清单。

## 2. Backend Health Check

- [x] 2.1 新增 `GET /api/health`。
- [x] 2.2 保留现有 `/health` 兼容。
- [x] 2.3 增加后端测试覆盖 `/api/health`。

## 3. Frontend Runtime Status

- [x] 3.1 增加运行环境检测：Browser / Tauri。
- [x] 3.2 增加后端健康检查请求。
- [x] 3.3 设置页显示运行环境、FastAPI 状态和 API Base URL。
- [x] 3.4 API Base URL 支持运行时配置优先级。

## 4. Tauri Shell

- [x] 4.1 在当前 frontend 项目中新增最小 Tauri 配置。
- [x] 4.2 新增 Tauri Rust shell 文件。
- [x] 4.3 新增 `npm run tauri dev` 脚本。
- [x] 4.4 确认 Tauri dev 配置加载 `http://localhost:3000`。

## 5. Documentation

- [x] 5.1 新增 Tauri Shell MVP 开发运行文档。
- [x] 5.2 文档记录三终端启动方式。
- [x] 5.3 文档记录手动验证项和已知风险。

## 6. Verification

- [x] 6.1 运行后端测试。
- [x] 6.2 运行前端 lint。
- [x] 6.3 运行前端 build。
- [x] 6.4 如本机缺少 Rust，记录无法运行 `npm run tauri dev`。
