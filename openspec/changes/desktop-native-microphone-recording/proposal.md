## Why

The current desktop app cannot rely on Web `MediaRecorder` because macOS WKWebView support is unavailable or unstable. Now that upload -> Win FunASR -> DashScope analysis works end to end, the next bottleneck is letting the Tauri app record microphone audio directly without leaving the app.

## What Changes

- Add a Tauri/Rust native microphone recorder for desktop builds.
- Return a WAV recording to the frontend after stop, then reuse the existing upload, playback, ASR, and AI summary flow.
- Add Tauri-only UI controls for native microphone recording with clear status and error states.
- Keep browser recording unchanged for web/dev-browser use.
- Do not implement system audio capture, game output capture, mixed microphone/system recording, or realtime ASR in this change.

## Capabilities

### New Capabilities

- `desktop-native-microphone-recording`: Tauri desktop users can record microphone audio natively, upload it through the existing recordings API, and use the existing analysis workflow.

### Modified Capabilities

- None.

## Impact

- `frontend/src-tauri/`: add Rust audio capture dependencies and Tauri commands.
- `frontend/src/app/page.tsx`: add desktop-only native microphone recording controls and upload handoff.
- `docs/`: update beta status and known issues to reflect microphone recording progress.
- Build/runtime: macOS users may be prompted for microphone permission by the app process.
