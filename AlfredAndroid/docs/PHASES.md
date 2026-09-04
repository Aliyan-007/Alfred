# Phase Status

| Phase | Status |
|---|---|
| 0 Foundation | ✅ |
| 1 WebSocket + foreground service | ✅ |
| 2 Registration + pairing (Keystore token) | ✅ |
| 3 Battery/device_info/open_app/open_url/media | ✅ |
| 4 Hardware (volume/flashlight/vibration) | ✅ |
| 5 App management | ✅ |
| 6 Notifications | ✅ |
| 7 Calendar | ✅ |
| 8 Alarms/timers | ✅ |
| 9 Clipboard | ✅ |
| 10 Expanded media | ✅ |
| 11 Shortcuts/workflows | ✅ |
| 12 Accessibility (opt-in) | ✅ |
| 13 Events | ✅ |
| 14 Multi-device | ✅ |
| 15 Dashboard/logs | ✅ |
| 16 Reliability | ✅ |
| 17 Security hardening | ✅ |
| 18 Tests | ✅ |
| 19 Documentation | ✅ |

OS limitations are reported honestly (brightness, media seek, cross-app alarm cancel, background clipboard read).

## Phase 1.1 — Local Wake-Word Foundation

- Added `WakeWordEngine` abstraction.
- Added `OpenWakeWordEngineAdapter` using on-device ONNX wake-word detection.
- `SpeechRecognizer` is now command-only; it is no longer used to detect "Alfred".
- Wake-word engine is stopped before TTS/command listening to prevent microphone contention and self-triggering.
- Added an 18-second conversation timeout and continuous command session.
- Production `alfred.onnx` is intentionally not bundled until a real Alfred classifier is available.

