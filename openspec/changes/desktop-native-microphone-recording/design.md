## Context

The web recording path uses `MediaRecorder`, but the macOS Tauri shell is backed by WKWebView where that API is unavailable or unreliable. The desktop app now has a working sidecar backend, local data directory configuration, Win 3070 FunASR HTTP transcription, and DashScope analysis. The remaining desktop blocker for game self-test is capturing microphone audio from inside the app.

## Goals / Non-Goals

**Goals:**

- Add a Tauri-native microphone recorder that works independently of WKWebView `MediaRecorder`.
- Capture microphone input to a WAV file and upload it through the existing `/api/recordings/upload` API.
- Keep the existing recording database, playback, transcription, speaker-label, and AI analysis flows unchanged.
- Present a desktop-only recording control with clear states and errors.

**Non-Goals:**

- System audio capture, game output capture, teammate voice capture, or microphone/system mixed recording.
- Realtime ASR or streaming partial transcript display.
- Long-session chunking changes.
- Replacing the existing browser recording implementation.

## Decisions

1. Use native Rust audio capture through `cpal`.

   `cpal` gives cross-platform microphone access from the Tauri process and bypasses WKWebView limitations. The alternative was continuing to rely on `MediaRecorder`, which has already proven unsuitable for the desktop shell.

2. Write WAV output with `hound`.

   WAV is broadly accepted by the existing backend and current Win FunASR path. The alternative was WebM/Opus, but the current Win FunASR service has already shown WebM decode failures.

3. Store recording bytes in a temporary WAV file and upload from Tauri.

   Returning base64 audio to the frontend would be simple for short clips, but it can become heavy for 10-30 minute game tests. The Tauri command will instead return metadata after stop, and a second command will send multipart form data to the existing backend upload endpoint.

4. Reuse the existing backend upload and analysis flow.

   The backend already persists files, detects duration, serves playback, triggers ASR, and stores analysis. Adding a separate native import API would duplicate behavior and increase test surface.

5. Start with a single active native microphone recording.

   The recorder state lives in a managed Tauri `Mutex<Option<...>>`. Starting while another native recording is active returns a clear error. Browser recording and long-session recording remain separate UI paths.

## Risks / Trade-offs

- OS microphone permission can be denied -> show a clear desktop microphone permission error and leave the recorder idle.
- Input sample formats differ by device -> convert `f32`, `i16`, and `u16` samples into `i16` WAV output.
- Long recordings can create large WAV files -> avoid frontend base64 IPC and upload from Tauri; system audio/mix and chunking stay separate future work.
- Upload can fail after recording succeeds -> keep the temporary WAV path until upload succeeds or the app restarts, and surface upload failure in the UI.
- macOS app bundle microphone usage metadata may still need packaging verification -> validate under `npm run tauri dev` first, then revisit bundle metadata before distributable beta.
