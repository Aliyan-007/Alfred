# Testing

## Automated: `./gradlew testDebugUnitTest`
| Suite | Covers |
|---|---|
| ProtocolModelsTest | Command/result/registration/pair/event JSON, defaults, error codes |
| CapabilityRegistryTest | Routing, unknown/unavailable, namespaced actions, duplicates, error helpers |
| ShortcutWorkflowTest | Workflow store CRUD |
| LoggerRedactionTest | Token/pairing-code redaction |

## Manual (real device)
1. Configure Hub IP in Settings → Save → Start Agent → verify Connected and Hub sees device online.
2. Pair with code; verify token persists across restart; revoke re-prompts.
3. Toggle Wi-Fi/stop Hub → Reconnecting with backoff; recovers automatically.
4. Issue each command in docs/COMMANDS.md and verify structured results.
5. Calendar mutate without `confirm` → `confirmation_required`; with `confirm:true` applies.
6. Notifications/accessibility only work after enabling in system Settings.
7. Logcat (`adb logcat -s ALFRED`) never shows token/code.
8. Two phones register distinct IDs; a command for one is ignored by the other.

## Instrumented
`./gradlew connectedDebugAndroidTest` (device/emulator API 26+).
