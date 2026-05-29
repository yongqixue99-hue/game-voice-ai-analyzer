## 1. OpenSpec

- [x] 1.1 创建 `real-backend-sidecar-readiness` change 目录。
- [x] 1.2 编写 `proposal.md`。
- [x] 1.3 编写 `design.md`（13 节审计：Goal / Background / Inventory / Dependency / Data Dir / Config / ASR / PyInstaller / Migration / Acceptance / Out of Scope / Risks / Tasks）。
- [x] 1.4 编写根 `spec.md`。
- [x] 1.5 编写 capability spec：`specs/real-backend-sidecar-readiness/spec.md`。
- [x] 1.6 编写本任务清单。

## 2. 真实后端审计（只读）

- [x] 2.1 确认入口：`uvicorn app.main:app`，无 `__main__`/`uvicorn.run`。
- [x] 2.2 列出模块与 6 个 router。
- [x] 2.3 确认数据接触点：SQLite 路径、`storage/audio`、`project_root=parents[2]`。
- [x] 2.4 审计依赖：声明 vs 实际 import（ASR/LLM 纯 `urllib`，无 SDK；无 ffmpeg/numpy）。
- [x] 2.5 列出实际需进包的传递依赖（取自 `.venv`）。
- [x] 2.6 列出 PyInstaller 风险（pydantic_core、sqlite dialect、uvicorn 动态导入、路径假设）。

## 3. 方案设计

- [x] 3.1 数据目录方案（db/audio/exports/logs/config + 三平台路径 + 注入优先级）。
- [x] 3.2 配置/密钥方案（dev `.env` → 桌面端 config/keychain；key 不入码/不入 git/前端不持）。
- [x] 3.3 阿里云 ASR 公网 URL 风险结论 + 三候选方案。
- [x] 3.4 PyInstaller 打包计划 + `backend/desktop_entry.py` 草案（不实现）。
- [x] 3.5 hello→real 分阶段迁移路线（P3–P8）。

## 4. 只读工具与文档

- [x] 4.1 新增 `scripts/check_backend_packaging_readiness.py`（只读 readiness 检查）。
- [x] 4.2 运行脚本验证可用且不产生副作用。
- [x] 4.3 新增 `docs/real-backend-sidecar-readiness.md`（可读审计摘要）。
- [ ] 4.4 （可选）更新 `docs/hand_off_status.md` —— 视用户需要再做。

## 5. 防护栏验证

- [x] 5.1 未打包真实后端。
- [x] 5.2 未替换 hello-backend sidecar、未改 Tauri externalBin 指向。
- [x] 5.3 未改业务代码（Python/Rust/前端）、未改 DB schema、未迁移数据/音频。
- [x] 5.4 未提交 `.env` 或任何 API Key。
- [x] 5.5 `.gitignore` 追加真实后端 PyInstaller 产物忽略规则。

## 6. 后续 Change（不在本 change 内做）

- [ ] 6.1 P4：`desktop-data-directory-refactor` —— `config.py` 支持 `LUNARIS_DATA_DIR`，dev 行为不变。
- [ ] 6.2 P5：`real-backend-desktop-entry` —— `backend/desktop_entry.py` + 数据目录注入（可选只读 `/api/system/config`）。
- [ ] 6.3 P6：`real-backend-pyinstaller-spike` —— 在 `experiments/` 打包真实后端并验证。
- [ ] 6.4 P7：`tauri-sidecar-swap-real-backend` —— externalBin 切换为 real-backend。
- [ ] 6.5 P8：`production-build-spike` —— 端到端打包 + ASR 公网 URL 正式方案。
