# ALFRED — Android Agent App — Project Brain

> Antigravity: read this file at the start of every session instead of
> re-scanning the whole repo. Update the "Session Log" section at the bottom
> after any meaningful change so future sessions stay in sync.

## What this app is
Alfred Android is a **device agent app**. It pairs with a "Hub" (a PC/server)
over a WebSocket connection, exposes device capabilities (notifications,
accessibility automation, etc.) to that Hub, and runs a foreground service to
stay connected in the background. It is a controls/status app, not a
content app — most screens are dashboards, settings forms, and status lists.

## Tech stack (do not change without being asked)
- Kotlin, Jetpack Compose, Material 3 (`androidx.compose.material3`)
- Single-Activity, Navigation-Compose (`ui/navigation/AlfredNavHost.kt`)
- MVVM: `DashboardViewModel` (in `viewmodel/`) exposes `StateFlow` state
  (`DashboardUiState`) consumed via `collectAsStateWithLifecycle()`
- `SettingsRepository` (in `storage/`) persists Hub connection settings
- No DI framework visible beyond a manual `container` on `AlfredApplication`

## Package map
```
com.alfred.android/
  agent/          background agent logic, LogLevel/log entries
  capabilities/   CapabilityState enum + capability registry
  events/         event bus / device event plumbing
  pairing/        pairing/handshake logic with the Hub
  permissions/    Android permission helpers
  protocol/       wire protocol to the Hub (WebSocket messages)
  registry/       capability registry
  service/        foreground service, ConnectionState enum
  storage/        SettingsRepository (DataStore-backed settings)
  ui/
    components/   shared composables: AlfredLogo, SectionCard, StatusPill,
                   InfoRow (reused across every screen — style once, applies
                   everywhere)
    dashboard/    DashboardScreen (home), CapabilityRow, PermissionRow,
                   DashboardUiState, CapabilityStatus, PermissionStatus
    logs/         LogsScreen — raw scrolling log viewer
    navigation/   AlfredNavHost, Routes object (dashboard/pairing/
                   permissions/settings/logs)
    pairing/      PairingScreen — enter pairing code from the Hub
    permissions/  PermissionsScreen — deep-links to Android system settings
    settings/     SettingsScreen — Hub host/port/scheme + device name form
    theme/        Color.kt (AlfredPrimary etc.), Theme.kt (AlfredTheme,
                   dark-only colorScheme), Type.kt (AlfredTypography)
  viewmodel/      DashboardViewModel (single source of truth for dashboard,
                   pairing, and logs screens)
  AlfredApplication.kt, MainActivity.kt
```

## Screens (5 total, all reachable from Routes)
| Route | File | Purpose |
|---|---|---|
| `dashboard` | `ui/dashboard/DashboardScreen.kt` | Home. Connection status, device info, battery, capabilities, permissions, service start/stop, action shortcuts. |
| `pairing` | `ui/pairing/PairingScreen.kt` | Enter a numeric pairing code shown on the Hub PC. |
| `permissions` | `ui/permissions/PermissionsScreen.kt` | Deep-links to system settings: notification access, accessibility, battery optimization, app info. |
| `settings` | `ui/settings/SettingsScreen.kt` | Form: Hub host/IP, port, scheme (ws/wss), device display name. |
| `logs` | `ui/logs/LogsScreen.kt` | Reverse-chronological monospace log stream with a Clear action. |

## Current visual system (theme/)
- Dark theme only, near-black background (`#0B0E14`), mint-green primary
  accent (`#3DDC97`), sky-blue secondary (`#5BC0EB`)
- Flat cards (`SectionCard`) with 16dp rounded corners, no elevation/shadow
- Typography is plain `FontFamily.SansSerif` + `FontFamily.Monospace` for
  data values, fairly conservative sizing
- Status communicated via `StatusPill` (colored dot + label) and per-row
  colored text (`PermissionRow`, `CapabilityRow`)
- Motion: Compose `AnimatedVisibility`/`AnimatedContent`/`animateColorAsState`
  already added for staggered section entrance, press-scale on buttons, and
  a pulsing dot on transitional connection states — this is a **starting
  point**, not the finished motion language.

## Design direction for the redesign
Target **Material 3 Expressive** (Google's 2025–2026 evolution of Material
You — bolder color, springy physics-based motion, morphing shapes, larger
expressive type scale, used in the redesigned Gmail/Photos/Phone apps).
Concretely:
- Replace flat `SectionCard` styling with M3 Expressive shape/elevation
  tokens; vary corner radii and card treatment per section instead of one
  uniform card everywhere
- Adopt `MaterialTheme.motionScheme` / spring-based transitions as the
  default motion, not just tween fades
- Each of the 5 screens should feel like part of one family but have a
  distinct visual identity/hero moment (not five copies of the same
  Column-of-cards layout) — see per-screen notes an agent should propose
  before writing code
- Keep dark-only theming and the existing brand colors as the seed palette;
  expressive ≠ discard the brand

## Hard constraints — do not break
- `DashboardViewModel`, `SettingsRepository`, and all files outside `ui/`
  are business logic — **do not modify their public signatures**. UI-only
  changes consume their existing `StateFlow`/`suspend fun` contracts.
- `DashboardUiState`, `CapabilityStatus`, `PermissionStatus` field names are
  used by the ViewModel — do not rename fields, only change how they render.
- `Routes` string constants are referenced by `AlfredNavHost` — do not
  rename without updating the nav graph.
- No new Gradle dependencies without checking `build.gradle.kts` first and
  confirming there's a real need (avoid adding animation/UI libraries;
  Compose's built-in `androidx.compose.animation` covers everything needed).
- App is Kotlin/Compose only — never introduce GSAP, JS, WebView-based UI,
  or any web tooling.

## Session Log
_(Antigravity: append a one-line dated entry here after each session so the
next session knows what's already been done and doesn't redo it.)_
- YYYY-MM-DD: (example) Redesigned DashboardScreen hero + connection card.
- 2026-09-06: Fixed pre-existing AlfredAgentService compile errors by restoring the missing android.util.Log import; full build now reaches a separate release R8 missing-class error for com.google.errorprone.annotations.Immutable.
- 2026-09-06: Added the requested Tink/R8 -dontwarn rule; assembleRelease passes, but the aggregate build remains blocked by the existing camera-permission lint error in AndroidManifest.xml.
- 2026-09-06: Fixed camera-permission lint by declaring android.hardware.camera as optional; full build and assembleRelease both pass.
