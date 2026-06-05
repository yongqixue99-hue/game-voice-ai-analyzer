## 1. Tauri Native Recording Core

- [x] 1.1 Add Rust dependencies for microphone capture, WAV writing, and multipart upload.
- [x] 1.2 Implement managed native microphone recorder state with start/stop/status Tauri commands.
- [x] 1.3 Write stopped recordings as WAV files in an app-owned temporary directory with duration and size metadata.
- [x] 1.4 Implement a Tauri upload command that posts the WAV file to the existing backend `/api/recordings/upload` endpoint.

## 2. Frontend Integration

- [x] 2.1 Add TypeScript types and invoke helpers for native microphone recording commands.
- [x] 2.2 Add Tauri-only desktop microphone recording UI with status, elapsed time, start, stop, and error states.
- [x] 2.3 On successful native upload, refresh recordings and trigger existing auto-analysis when enabled.
- [x] 2.4 Keep existing browser recording, upload, long recording, playback, ASR, and AI summary flows unchanged.

## 3. Documentation and Verification

- [x] 3.1 Update desktop beta docs to mark native microphone recording as first implementation and keep system audio/mix out of scope.
- [x] 3.2 Run focused Rust, frontend lint/build, and backend regression checks.
- [ ] 3.3 Manually verify the app can start a native microphone recording, stop it, upload it, and see it in history.
