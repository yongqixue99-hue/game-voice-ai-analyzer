# Tasks — FunASR Provider 稳定化与 Beta 交接

## 0. OpenSpec

- [x] 0.1 创建 proposal / design / tasks 文档。

## 1. Fake FunASR Server

- [x] 1.1 新增 `scripts/fake_funasr_server.py`。
- [x] 1.2 支持 `/health`。
- [x] 1.3 支持 `/recognize` 与 `/asr` multipart 音频识别响应。

## 2. 后端 FunASR 稳定化

- [x] 2.1 加固 `parse_funasr_response`，兼容 `segments` / `sentence_info` / `result` / list wrapper。
- [x] 2.2 加固时间戳秒/毫秒转换。
- [x] 2.3 更新 `/api/asr/status`，返回 provider/configured/reachable/error 且不可达不崩溃。
- [x] 2.4 增加后端测试覆盖新增响应格式和状态字段。

## 3. 前端状态提示

- [x] 3.1 设置页兼容新的 ASR status 字段。
- [x] 3.2 provider=aliyun 且 `PUBLIC_BASE_URL` 为本地时显示明确警告。

## 4. 文档与 Smoke Check

- [x] 4.1 更新 `docs/asr-providers.md`。
- [x] 4.2 新增 `docs/funasr-http-provider-handoff.md`。
- [x] 4.3 新增 `scripts/asr_provider_smoke_check.sh`。

## 5. 验证

- [x] 5.1 后端 pytest 通过。
- [x] 5.2 前端 lint 通过。
- [x] 5.3 前端 build 通过。
- [x] 5.4 Tauri/Rust `cargo test` 通过或记录原因。
- [x] 5.5 ASR provider smoke check 通过。

## 6. 提交与交接

- [x] 6.1 检查 git status，确认无 `.env`、数据库、音频、日志、build/dist、二进制产物入库。
- [x] 6.2 安全后提交 `完善 FunASR HTTP Provider 工程闭环`。
- [x] 6.3 输出当前进度、已完成、未完成、下一步指令、关键文件路径/命令。
