# ALFRED — Android Device Agent

The Android companion for the **ALFRED** personal AI ecosystem. This is a **device agent** — it connects to the ALFRED Hub over WebSocket, registers the device and its capabilities, receives commands, executes supported Android actions, and reports structured results and events. It is NOT the AI brain.

## Features (all phases implemented)
- WebSocket connection with exponential-backoff reconnect, ping/pong heartbeat, and a foreground service.
- Pairing with a PC-displayed code; auth token stored in **Android Keystore-encrypted** storage.
- Device registration (id, name, manufacturer/model/Android/app version, capability states).
- Capability-based command router:
  - **battery**, **device_info**
  - **apps** (open by package/friendly name, list), **url** (http/https only)
  - **media** play/pause/next/previous/stop/ff/rew
  - **volume** up/down/set/mute, **hardware** flashlight & vibration
  - **notifications** (opt-in listener), **calendar** (list/search/create/mutate with confirmation)
  - **alarms/timers**, **clipboard**, **shortcuts/workflows**
  - **accessibility** (opt-in: back/home/recents/tap/swipe/click-by-text)
- Device events (battery/charging/connection) forwarded to the Hub.
- Multi-device: stable per-install UUID; Hub addresses each device.
- Dark futuristic Material 3 dashboard with Settings, Pairing, Permissions, and Logs screens.

Local-network first — no cloud, no hardcoded PC IP.

## Build
- Android Studio Koala+ (AGP 8.5 / JDK 17), SDK Platform 34.
```bash
./gradlew assembleDebug        # app/build/outputs/apk/debug/app-debug.apk
./gradlew installDebug
./gradlew testDebugUnitTest     # 24 unit tests
```

## Setup
1. Install and open ALFRED.
2. **Settings** → enter PC LAN IP/port (e.g. `192.168.1.100`, `8765`, scheme `ws`), device name → Save.
3. (Optional) **Permissions** for notifications/calendar/accessibility/battery.
4. **Start Agent** → dashboard shows Connected.
5. On PC start pairing; enter the code in **Pair**. Once paired, ALFRED can issue commands.

## Docs
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/COMMANDS.md](docs/COMMANDS.md)
- [docs/PERMISSIONS.md](docs/PERMISSIONS.md)
- [docs/TESTING.md](docs/TESTING.md)
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- [docs/PHASES.md](docs/PHASES.md)

## Security
No shell/arbitrary code execution; token encrypted at rest and redacted from logs; capability & permission checks; confirmation for destructive calendar edits; accessibility strictly opt-in; URLs restricted to http/https.
