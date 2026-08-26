package com.alfred.android.viewmodel

import android.app.Application
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.alfred.android.AlfredApplication
import com.alfred.android.agent.LogEntry
import com.alfred.android.capabilities.accessibility.AccessibilityState
import com.alfred.android.capabilities.notifications.NotificationState
import com.alfred.android.events.BatteryEventReceiver
import com.alfred.android.events.DeviceEvents
import com.alfred.android.events.EventNames
import com.alfred.android.permissions.AlfredPermissions
import com.alfred.android.registry.DeviceIdentity
import com.alfred.android.service.AlfredAgentService
import com.alfred.android.service.ConnectionState
import com.alfred.android.ui.dashboard.CapabilityStatus
import com.alfred.android.ui.dashboard.DashboardUiState
import com.alfred.android.ui.dashboard.PermissionStatus
import com.alfred.android.util.DeviceInfo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class DashboardViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as AlfredApplication
    private val agent = app.container.agent
    private val identity = DeviceIdentity(application)
    private val settingsRepository = app.container.settingsRepository
    private val servicePrefs = application.getSharedPreferences("alfred_service_prefs", Context.MODE_PRIVATE)
    private val batteryReceiver = BatteryEventReceiver(identity.deviceId)

    private val _logs = MutableStateFlow<List<LogEntry>>(emptyList())
    val logs: StateFlow<List<LogEntry>> = _logs.asStateFlow()
    private val _serviceRunning = MutableStateFlow(servicePrefs.getBoolean("service_enabled", false))

    val uiState: StateFlow<DashboardUiState> = combine(
        agent.connectionState, agent.authenticated, agent.paired,
        agent.lastCommand, agent.lastResult, _serviceRunning, settingsRepository.settings,
    ) { values ->
        @Suppress("UNCHECKED_CAST")
        buildState(
            conn = values[0] as ConnectionState, authed = values[1] as Boolean, paired = values[2] as Boolean,
            lastCmd = values[3] as String?, lastRes = values[4] as String?,
            svc = values[5] as Boolean, settings = values[6] as com.alfred.android.storage.ConnectionSettings,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), DashboardUiState())

    init {
        application.registerReceiver(batteryReceiver, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        viewModelScope.launch {
            agent.logs.collect { _logs.update { l -> (l + it).takeLast(200) } }
        }
        viewModelScope.launch {
            agent.connectionState.collect { s ->
                if (s == ConnectionState.CONNECTED) DeviceEvents.emit(EventNames.DEVICE_CONNECTED, identity.deviceId)
                else if (s == ConnectionState.DISCONNECTED) DeviceEvents.emit(EventNames.DEVICE_DISCONNECTED, identity.deviceId)
            }
        }
    }

    private fun buildState(
        conn: ConnectionState, authed: Boolean, paired: Boolean,
        lastCmd: String?, lastRes: String?, svc: Boolean,
        settings: com.alfred.android.storage.ConnectionSettings,
    ): DashboardUiState {
        val ctx: Context = app
        agent.refreshCapabilities()
        val caps = agent.registry.all().map {
            CapabilityStatus(it.id, it.displayName.replaceFirstChar { c -> c.uppercase() }, it.state.value)
        }
        val perms = AlfredPermissions.ALL.map { PermissionStatus(it.displayName, it.isGranted(ctx)) } + listOf(
            PermissionStatus("Notification access", NotificationState.listenerConnected, if (!NotificationState.listenerConnected) "Disabled" else null),
            PermissionStatus("Accessibility", AccessibilityState.connected, if (!AccessibilityState.connected) "Disabled" else null),
        )
        val (level, charging) = readBattery(ctx)
        return DashboardUiState(
            connectionState = conn, authenticated = authed, paired = paired,
            hubUrl = settings.hubUrl, deviceId = identity.deviceId,
            deviceName = settings.deviceName.ifBlank { DeviceInfo.defaultDisplayName() },
            manufacturer = DeviceInfo.manufacturer, model = DeviceInfo.model,
            androidVersion = DeviceInfo.androidVersion,
            appVersion = app.packageManager.getPackageInfo(app.packageName, 0).versionName ?: "0.1.0",
            batteryLevel = level, isCharging = charging, foregroundServiceRunning = svc,
            lastCommand = lastCmd, lastResult = lastRes, capabilities = caps, permissions = perms,
        )
    }

    fun startService() { servicePrefs.edit().putBoolean("service_enabled", true).apply(); _serviceRunning.value = true; AlfredAgentService.start(app) }
    fun stopService() { servicePrefs.edit().putBoolean("service_enabled", false).apply(); _serviceRunning.value = false; AlfredAgentService.stop(app) }
    fun testConnection() { if (uiState.value.hubUrl.isBlank()) { logError("Hub URL not configured") } else startService() }
    fun pairWithCode(code: String) { if (!agent.sendPairRequest(code)) logError("Cannot pair: not connected. Start agent and configure Hub first.") }
    fun revokePairing() = agent.unpair()
    fun clearLogs() { _logs.value = emptyList() }

    private fun logError(m: String) { _logs.update { it + LogEntry(System.currentTimeMillis(), com.alfred.android.agent.LogLevel.ERROR, m) } }

    private fun readBattery(context: Context): Pair<Int?, Boolean?> {
        val i = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED)) ?: return null to null
        val level = i.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        val scale = i.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
        val pct = if (level >= 0 && scale > 0) level * 100 / scale else null
        val status = i.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
        return pct to (status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL)
    }

    override fun onCleared() { runCatching { app.unregisterReceiver(batteryReceiver as BroadcastReceiver) }; super.onCleared() }
}
