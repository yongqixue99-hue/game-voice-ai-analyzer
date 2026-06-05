## ADDED Requirements

### Requirement: Desktop native microphone controls
The system SHALL expose native microphone recording controls inside the Tauri desktop app without requiring browser `MediaRecorder`.

#### Scenario: Controls are available in Tauri
- **WHEN** the user opens LUNARIS in the Tauri desktop runtime
- **THEN** the dashboard shows a desktop microphone recording control

#### Scenario: Controls do not replace browser recording
- **WHEN** the user opens LUNARIS in a non-Tauri browser runtime
- **THEN** the existing browser recording and upload controls remain available

### Requirement: Start native microphone recording
The system SHALL start exactly one native microphone recording session after the user clicks the desktop microphone start button.

#### Scenario: Recording starts
- **WHEN** the user clicks the desktop microphone start button and microphone access is available
- **THEN** the system starts native microphone capture and shows a recording state with elapsed time

#### Scenario: Duplicate start is rejected
- **WHEN** a native microphone recording is already active and start is requested again
- **THEN** the system keeps the existing recording active and returns a clear error or no-op state

#### Scenario: Microphone access fails
- **WHEN** the operating system denies microphone access or no input device is available
- **THEN** the system shows a clear desktop microphone error and does not create a recording

### Requirement: Stop and upload native microphone recording
The system SHALL stop native capture, create a WAV recording, upload it through the existing recordings API, and refresh the recording list.

#### Scenario: Recording stops and uploads
- **WHEN** the user stops an active native microphone recording
- **THEN** the system creates a WAV file and uploads it to `POST /api/recordings/upload`

#### Scenario: Uploaded recording is usable
- **WHEN** the native microphone recording upload succeeds
- **THEN** the new recording appears in the existing recording list and can use existing playback, transcription, and AI summary actions

#### Scenario: Upload fails
- **WHEN** the native microphone recording is stopped but backend upload fails
- **THEN** the system shows an upload error without marking the recording as uploaded

### Requirement: Native recording scope boundaries
The system SHALL limit this change to microphone capture and MUST NOT claim support for system audio, game output audio, teammate voice capture, mixed audio, or realtime ASR.

#### Scenario: User reviews recording scope
- **WHEN** the user sees the desktop microphone recording control
- **THEN** the UI and docs identify it as microphone recording rather than system audio or mixed game audio capture
