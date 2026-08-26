# Permissions

Permissions are explicit and never granted silently. A capability is `available` only when its permission is held; otherwise `permission_required`.

## Runtime
- POST_NOTIFICATIONS (foreground notification)
- READ_CALENDAR / WRITE_CALENDAR
- VIBRATE, CAMERA (flashlight)

## Special (system Settings)
- Notification Listener → notifications
- Accessibility Service → accessibility actions (opt-in, visibly shown)
- Battery optimization exemption → reliable background
- WRITE_SETTINGS → brightness (background-restricted)

## NOT done
No SMS/contacts/location/microphone/camera-capture. No arbitrary shell/code execution. Tokens stored in Keystore-encrypted prefs and redacted from logs; backups excluded.
