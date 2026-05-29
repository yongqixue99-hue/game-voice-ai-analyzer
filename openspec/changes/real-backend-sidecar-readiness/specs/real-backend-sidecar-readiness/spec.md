# real-backend-sidecar-readiness 能力规格

## Goal

新增能力 `real-backend-sidecar-readiness`：以审计 + 设计文档形式，约束真实业务后端进 Tauri sidecar 前必须确认的就绪项（结构、依赖、数据目录、配置/密钥、ASR 公网 URL、PyInstaller 打包、分阶段迁移），作为 P4–P8 实现 change 的输入。

## Requirements

1. 必须产出 `proposal.md`、`design.md`、`spec.md`、`tasks.md` 四份文档，并新增 `docs/real-backend-sidecar-readiness.md`。
2. 必须基于真实代码（非臆测）输出后端入口、模块、路由、依赖清单。
3. 必须指出真实后端相对源码树的路径假设（`Path(__file__).parents[2]`）在 PyInstaller frozen 下失效，并给出数据目录注入方案。
4. 必须为 db / audio / exports / logs / config 五类数据给出 macOS 落盘位置，Windows/Linux 至少占位，并定义解析优先级。
5. 必须明确阿里云 fun-asr 的异步文件回源机制与公网 URL 风险，给出至少三种正式方案候选。
6. 必须给出独立入口 `backend/desktop_entry.py` 的设计动机与草案（不实现）。
7. 必须给出 hello→real 分阶段迁移路线，并标注每步归属。
8. 必须只新增文档与只读脚本，不引入业务代码改动。
9. 必须不破坏现有 Web 入口、Tauri+hello sidecar 链路、`scripts/dev-all.sh`。
10. 新增的 readiness 检查脚本必须是只读的（不写文件、不建/改数据库、不发起 ASR/LLM 请求）。

## Out of Scope

数据目录重构、`desktop_entry.py` 实现、真实后端 PyInstaller 打包、sidecar 替换、生产 build、ASR 正式方案、keychain、OSS、数据迁移，均由后续 change 承接，不在本能力内。
