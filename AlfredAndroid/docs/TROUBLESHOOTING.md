# Troubleshooting

- **SDK/JDK**: needs JDK 17, Platform 34, Build-Tools 34.0.0.
- **Won't connect**: phone & PC same Wi-Fi; use PC LAN IP (not localhost); allow Hub port through PC firewall; check Logs/`adb logcat -s ALFRED`.
- **Pairing fails**: revoke and re-pair with fresh code; check clock.
- **Background disconnects**: disable battery optimization, allow notifications, enable autostart on vendor ROMs.
- **Capability shows unavailable**: grant the listed permission; brightness/seek/background clipboard are OS-restricted by design.
- **Low RAM build**: set `org.gradle.workers.max=1` and `kotlin.compiler.execution.strategy=in-process` in gradle.properties.
