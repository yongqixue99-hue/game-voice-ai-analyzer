## ADDED Requirements

### Requirement: Tauri shell development window
The system SHALL provide a minimal Tauri shell that loads the existing Next.js development server.

#### Scenario: Tauri dev window opens current frontend
- **WHEN** the developer runs the Tauri development command
- **THEN** the Tauri window loads `http://localhost:3000`
- **AND** it reuses the existing frontend UI instead of a copied UI

### Requirement: Backend health endpoint
The backend SHALL expose a health endpoint for desktop shell connection checks.

#### Scenario: Backend health is available
- **WHEN** the client requests `GET /api/health`
- **THEN** the backend returns status `ok`, service `fastapi`, and a version string

### Requirement: Runtime environment display
The frontend SHALL display whether it is running in a browser or Tauri WebView.

#### Scenario: Runtime display appears in settings
- **WHEN** the user opens Settings
- **THEN** the page shows `Browser` or `Tauri` as the runtime environment

### Requirement: FastAPI connection status display
The frontend SHALL display FastAPI connection status without crashing when the backend is unavailable.

#### Scenario: Backend is connected
- **WHEN** `GET /api/health` succeeds
- **THEN** Settings shows FastAPI status as connected

#### Scenario: Backend is disconnected
- **WHEN** `GET /api/health` fails
- **THEN** Settings shows `后端未连接，请先启动 FastAPI 服务`
- **AND** the page remains usable

### Requirement: Runtime API base URL strategy
The frontend SHALL support a runtime API base URL strategy for future Tauri injection.

#### Scenario: Runtime config is present
- **WHEN** `window.__LUNARIS_CONFIG__.apiBaseUrl` is present
- **THEN** API requests use that URL before falling back to build-time configuration

#### Scenario: Runtime config is absent
- **WHEN** no runtime API base URL is present
- **THEN** API requests fall back to `NEXT_PUBLIC_API_BASE_URL` or `http://127.0.0.1:8000`

### Requirement: Browser compatibility preservation
The Tauri shell MVP SHALL preserve current browser usage.

#### Scenario: Browser page still opens
- **WHEN** the developer runs the Next.js development server in a browser
- **THEN** the Web UI remains usable as before

### Requirement: Development documentation
The project SHALL document how to run the Tauri shell MVP in development mode.

#### Scenario: Developer reads Tauri docs
- **WHEN** the developer opens the Tauri shell MVP documentation
- **THEN** it lists backend, frontend, and Tauri development commands
- **AND** it records manual verification items and known limitations
