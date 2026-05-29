# real-backend-sidecar-readiness

## Goal

对真实业务后端（`backend/app`）做"能否/如何/分几步"进 Tauri sidecar 的就绪审计，并输出最小迁移设计：结构清单、依赖与 PyInstaller 打包风险、桌面端数据目录方案、配置/密钥方案、阿里云 ASR 公网 URL 风险结论、独立入口设计、hello→real 分阶段迁移路线。本 change 只产出文档与一个只读检查脚本，不打包、不改业务代码、不动现有 sidecar 链路。

## Background

P2 已用 `experiments/hello-backend` 打通 PyInstaller → Tauri sidecar → Rust spawn/kill/status → 前端按钮的完整链路并真机验证。真实后端是多模块 FastAPI（SQLite + 文件存储 + 阿里云 ASR + LLM），存在三类结构性阻塞点尚未核实：`__file__`/相对路径在 frozen 下失效、阿里云 ASR 需要公网回源 URL、依赖/hidden imports 未针对打包核对。前序高层设计见 `tauri-prod-backend-launch-design`；本 change 把它落到真实后端代码层面。

## Requirements

1. 本 change MUST 只产出文档（OpenSpec change + `docs/real-backend-sidecar-readiness.md`）与**只读**检查脚本，MUST NOT 修改任何业务代码、Rust 代码、前端 UI、数据库 schema、数据库内容或 `storage/audio`。允许仅追加 `.gitignore` 忽略规则。
2. MUST 输出真实后端结构清单：入口、模块、路由、数据/文件接触点。
3. MUST 输出依赖审计：声明依赖 vs 实际 import，并指出 PyInstaller 打包风险（hidden imports、pydantic_core、sqlite dialect、uvicorn 动态导入）。
4. MUST 给出桌面端数据目录方案，覆盖 db / audio / exports / logs / config，并给出 macOS/Windows/Linux 路径与注入优先级。
5. MUST 给出配置与密钥方案：dev 用 `.env`，桌面端用 config 文件/后续 keychain；API Key 不入代码、不入 git、前端不持完整 key。
6. MUST 明确阿里云 ASR 公网 URL 风险，并列出正式方案候选（OSS 签名 URL / 本地 FunASR / 支持上传的 provider），同时说明开发期 localtunnel 非正式方案。
7. MUST 给出真实后端 PyInstaller 打包计划，包含独立入口 `backend/desktop_entry.py` 的设计动机（`app.main:app` 无 `__main__`）。
8. MUST 给出从 hello-backend sidecar 到 real-backend sidecar 的分阶段迁移路线（P3–P8），并标注每步是否在本 change 内。
9. MUST NOT 直接 PyInstaller 打包真实后端、MUST NOT 替换 hello-backend sidecar、MUST NOT 修改 Tauri externalBin 指向、MUST NOT 引入 OSS、MUST NOT 重构 ASR/LLM provider。
10. MUST 不破坏现有 Web 浏览器 dev、Tauri dev、hello-backend sidecar 链路、`scripts/dev-all.sh`。
11. SHOULD 列出仍需用户决策的 open questions（数据迁移、ASR 正式方案、onefile/onedir、keychain 时机）。

## Out of Scope

实施工作（数据目录重构、`desktop_entry.py`、真实后端 PyInstaller spike、sidecar 替换、生产 build、ASR 正式方案、keychain、OSS）由后续独立 change（P4–P8）承接，不在本能力内。
