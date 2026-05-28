## ADDED Requirements

### Requirement: Tauri-first desktop recommendation
The research SHALL recommend whether Tauri or Electron should be prioritized as the first formal desktop route for this project.

#### Scenario: Desktop route recommendation is reviewed
- **WHEN** the desktop architecture research is opened
- **THEN** it states that Tauri is the recommended first formal route
- **AND** it explains why Electron remains a fallback option

### Requirement: Tauri vs Electron comparison
The research SHALL compare Tauri and Electron in the context of this application.

#### Scenario: Runtime comparison is reviewed
- **WHEN** the comparison section is read
- **THEN** it covers package size, memory profile, Web compatibility, backend process management, long-running background usage, and future migration cost

### Requirement: Current Next.js frontend reuse
The research SHALL define how the current Next.js frontend is reused in a Tauri desktop app.

#### Scenario: Frontend reuse strategy is reviewed
- **WHEN** the frontend reuse plan is read
- **THEN** it describes development mode loading via localhost
- **AND** it describes production mode preference for Next.js static export
- **AND** it describes fallback options if static export is not viable

### Requirement: FastAPI local backend retention
The research SHALL keep FastAPI as the local backend service for the desktop route.

#### Scenario: Backend strategy is reviewed
- **WHEN** the backend packaging plan is read
- **THEN** it states that FastAPI remains the local API service
- **AND** it describes manual backend startup for the Tauri shell MVP
- **AND** it describes later Tauri-managed Python sidecar or child process startup

### Requirement: Desktop data directory strategy
The research SHALL define where SQLite, audio files, export files, logs, and local config should live after desktop packaging.

#### Scenario: Desktop data paths are reviewed
- **WHEN** the local data directory plan is read
- **THEN** it lists Windows AppData, macOS Application Support, and Linux app data directory strategies
- **AND** it states that packaged desktop data MUST NOT be stored in the source tree

### Requirement: API key and provider config storage
The research SHALL define how provider config and API keys are stored without hard-coding secrets.

#### Scenario: Secret storage strategy is reviewed
- **WHEN** the API key and config storage plan is read
- **THEN** it states that API keys MUST NOT be hard-coded
- **AND** it states that API keys MUST NOT be committed to git
- **AND** it distinguishes non-sensitive local config from sensitive keychain-backed secrets

### Requirement: Aliyun ASR public URL risk
The research SHALL explicitly document the public URL constraint for Aliyun ASR in a desktop app.

#### Scenario: Cloud ASR local file risk is reviewed
- **WHEN** the ASR risk section is read
- **THEN** it states that desktop local files and localhost URLs cannot be fetched by Aliyun ASR
- **AND** it identifies development tunnels, OSS/Object Storage, and local FunASR as possible paths

### Requirement: Desktop audio capture roadmap
The research SHALL define staged plans for microphone recording, system audio capture, mixed capture, tray, and mini recorder window.

#### Scenario: Audio and desktop feature roadmap is reviewed
- **WHEN** the audio capture roadmap is read
- **THEN** it states that browser microphone recording is reused first
- **AND** it states that system audio, mixed recording, tray, and real floating mini window are out of scope for the first Tauri shell MVP

### Requirement: FunASR Local Provider roadmap
The research SHALL define a future FunASR Local integration route without bundling the large model into the first Tauri build.

#### Scenario: FunASR route is reviewed
- **WHEN** the FunASR roadmap is read
- **THEN** it recommends a future HTTP provider connected to a Win 3070 FunASR service
- **AND** it states that bundling FunASR model and GPU dependencies is out of scope for the first Tauri shell MVP

### Requirement: Tauri shell MVP scope
The research SHALL define the first Tauri shell MVP scope and next implementation steps.

#### Scenario: Tauri shell MVP scope is reviewed
- **WHEN** the next implementation steps are read
- **THEN** they describe a minimal Tauri shell that loads the current Next.js dev server and detects the local FastAPI backend
- **AND** they explicitly exclude packaging, system audio, tray, floating window, and bundled FunASR
