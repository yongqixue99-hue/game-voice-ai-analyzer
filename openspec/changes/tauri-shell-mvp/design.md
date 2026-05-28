# tauri-shell-mvp 设计

## Goal

实现最小 Tauri Shell MVP：在 Tauri 开发模式中打开当前 Next.js Web UI，并在 UI 中显示运行环境、FastAPI 连接状态和 API Base URL。该阶段只验证桌面壳可行性，不做完整桌面端产品。

## Background

当前项目已经完成 Web MVP 主链路、桌面风格 Web UI 和 `desktop-app-architecture-research`。架构结论是 Tauri 优先、Electron 兜底。`tauri-shell-mvp` 是 Tauri 路线的第一个可运行验证点。

## Architecture

```text
Terminal 1: FastAPI
  backend/.venv + uvicorn app.main:app --reload

Terminal 2: Next.js
  frontend/npm run dev

Terminal 3: Tauri
  frontend/npm run tauri dev
      -> Tauri WebView loads http://localhost:3000
      -> Web UI fetches http://127.0.0.1:8000/api/health
      -> Settings page shows Browser/Tauri + backend status
```

This MVP keeps FastAPI as the local API service and keeps Next.js as the only frontend. Tauri is only the desktop shell.

## Requirements

- Tauri shell MUST reuse the existing `frontend/` app.
- Tauri shell MUST load `http://localhost:3000` in development mode.
- Tauri shell MUST NOT copy or fork the frontend UI.
- Tauri shell MUST NOT start FastAPI in this phase.
- The backend MUST expose `GET /api/health`.
- The frontend MUST show runtime environment and backend health in Settings.
- Browser usage MUST remain available.

## Development Mode Behavior

Development mode uses three processes:

1. FastAPI manually started by developer.
2. Next.js manually started by developer.
3. Tauri manually started by developer.

Tauri config should not attempt to solve production packaging in this stage. Production build/export risk is documented only.

## Backend Health Check

Endpoint:

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "service": "fastapi",
  "version": "0.1.0"
}
```

Existing `/health` can remain for compatibility.

When the request fails, the frontend displays:

```text
后端未连接，请先启动 FastAPI 服务
```

## API Base URL Strategy

Current browser mode can continue using:

```text
NEXT_PUBLIC_API_BASE_URL
```

For desktop mode, the frontend should also support runtime config:

```ts
window.__LUNARIS_CONFIG__?.apiBaseUrl
```

Priority:

1. Tauri/runtime injected `window.__LUNARIS_CONFIG__.apiBaseUrl`
2. `NEXT_PUBLIC_API_BASE_URL`
3. `http://127.0.0.1:8000`

This MVP may not yet inject runtime config from Rust, but the frontend should be ready for it.

## Acceptance Criteria

1. OpenSpec change exists.
2. Tauri config exists under the current frontend project.
3. `npm run tauri dev` script exists.
4. Tauri development config points to `http://localhost:3000`.
5. Backend exposes `GET /api/health`.
6. Settings page shows runtime environment: Browser / Tauri.
7. Settings page shows FastAPI status: checking / connected / disconnected.
8. Settings page shows API Base URL.
9. Browser version of the Web UI still works.
10. Existing frontend lint/build passes.
11. Backend tests pass.
12. Docs explain the three-terminal development startup.

## Out of Scope

- System audio recording.
- Microphone + system audio mixing.
- Tray.
- True floating mini recorder window.
- Startup at login.
- Python sidecar.
- FastAPI packaging.
- Production installer.
- FunASR local deployment.
- OSS upload.
- Database refactor.
- ASR/LLM provider refactor.
- UI redesign.

## Risks / Trade-offs

- Tauri requires Rust toolchain; without `rustc`/`cargo`, `npm run tauri dev` cannot run.
- Tauri WebView MediaRecorder support must be tested manually.
- File upload and audio playback in Tauri WebView must be tested manually.
- Production Next.js loading is unresolved; it requires a later static export spike.
- FastAPI is manually started in this MVP, so the desktop app is not yet self-contained.

## Task List

See `tasks.md`.
