# Commands

Incoming:
```json
{ "id": "cmd_1", "device": "android_...", "action": "get_battery", "parameters": {}, "confirm": false }
```
Result: `{ "type":"command_result", "id":..., "success":true, "result":{...} }`
Errors are structured: `permission_required`, `capability_unavailable`, `unsupported_action`, `invalid_parameters`, `device_locked`, `authentication_failed`, `not_connected`, `timeout`, `confirmation_required`, `internal_error`.

## Supported actions
- `battery` → `{battery, charging, percentage}`
- `device_info` → `{manufacturer, model, android_version, sdk, device_id, name, app_version, brand, product}`
- `apps.open_app`/`apps` (`package` or `name`); `apps.list`
- `url`/`open_url` (`url`, http/https)
- `media` (`command`: play/pause/play_pause/next/previous/stop/fast_forward/rewind)
- `volume.up|down|mute|unmute|set|status` (`value` 0-100 for set)
- `hardware.flashlight_on|off|vibrate|status` (`duration_ms`); `brightness` → `permission_required`
- `notifications.list` (needs notification access)
- `calendar.list` (`days`), `calendar.search` (`query`), `calendar.create` (`title,start,end?,...`), `calendar.reschedule|cancel` (`event_id`, requires `confirm:true`)
- `alarms.set_alarm` (`hour,minute,label?`), `alarms.set_timer` (`seconds,label?`)
- `clipboard.set` (`text`), `clipboard.get` (background read blocked on Android 10+)
- `shortcuts.define|list|run|delete` (`name`, `steps[]` of `open_app`/`open_url`)
- `accessibility.back|home|recents|tap(x,y)|swipe(...)|click_text(text)` (opt-in)

## Registration (sent on connect)
`{type:"register", device_id, name, device_type:"android", capabilities:[{id,state}], app_version, android_version, manufacturer, model, auth_token?}`

## Pairing
Agent sends `{type:"pair", code, name}`; Hub replies `{type:"pair_response", success, auth_token, device_id?}`. Token is stored encrypted.

## Events
`{type:"event", event, device, data, ts}` — `battery_changed`, `charging_started/stopped`, `device_connected/disconnected`, `notification_received`.

## Honest limitations
Brightness (WRITE_SETTINGS/background), media seek, cross-app alarm cancel, background clipboard read are not available to ordinary apps and return `permission_required`/`capability_unavailable` rather than pretending to work.
