# Architecture

```
Compose UI → ViewModel/StateFlow → Domain/Settings
   → Foreground Service (AlfredAgentService)
   → AlfredAgent → ConnectionManager (OkHttp WebSocket, backoff, heartbeat)
   → Protocol (Command/CommandResult/Registration/Events)
   → CapabilityRegistry → Capability handlers → Android APIs
```

## Key packages
- `ui/` — Compose Material 3 screens (dashboard, settings, pairing, logs, permissions), theme, reusable components.
- `viewmodel/` — `DashboardViewModel` exposes a single `DashboardUiState`.
- `service/` — `AlfredAgentService` (foreground) + `ConnectionState`.
- `agent/` — `AlfredAgent` (protocol loop), `AppContainer` (manual DI).
- `websocket/` — `WsTransport`/`OkHttpWsTransport` and `ConnectionManager` (reconnect, ping).
- `protocol/` — wire models + `ErrorCodes`.
- `capabilities/` — `Capability` interface, `CapabilityRegistry`, and one subpackage per feature.
- `pairing/` — Keystore-backed `CredentialStore`.
- `registry/` — per-install `DeviceIdentity`.
- `events/` — event bus, battery receiver, boot receiver.
- `permissions/` — central runtime-permission catalogue.
- `storage/` — DataStore `SettingsRepository`.
- `util/` — redacting `Logger`, `Constants`, `DeviceInfo`.

## Adding a capability
1. Implement `BaseCapability` in `capabilities/<name>/`.
2. Set state in `refresh()` based on API level + permissions.
3. Implement `handle()`: validate params, check permissions, call Android API, return `CommandResult`.
4. Register in `CapabilityProvider.populate()`.
It then appears on the dashboard and in registration automatically.
