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
import com.alfred.android.agent.LogLevel
import com.alfred.android.capabilities.accessibility.AccessibilityState
import com.alfred.android.capabilities.notifications.NotificationState
import com.alfred.android.events.BatteryEventReceiver
import com.alfred.android.events.DeviceEvents
import com.alfred.android.events.EventNames
import com.alfred.android.permissions.AlfredPermissions
import com.alfred.android.registry.DeviceIdentity
import com.alfred.android.service.AlfredAgentService
import com.alfred.android.service.ConnectionState
import com.alfred.android.storage.ConnectionSettings
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

class DashboardViewModel(
    application: Application
) : AndroidViewModel(application) {

    private val app =
        application as AlfredApplication

    private val agent =
        app.container.agent

    private val identity =
        DeviceIdentity(app)

    private val settingsRepository =
        app.container.settingsRepository

    private val servicePrefs =
        app.getSharedPreferences(
            "alfred_service_prefs",
            Context.MODE_PRIVATE
        )

    private val batteryReceiver =
        BatteryEventReceiver(
            identity.deviceId
        )

    private val _logs =
        MutableStateFlow<List<LogEntry>>(
            emptyList()
        )

    val logs:
        StateFlow<List<LogEntry>> =
        _logs.asStateFlow()

    private val _serviceRunning =
        MutableStateFlow(
            servicePrefs.getBoolean(
                "service_enabled",
                false
            )
        )

    val uiState:
        StateFlow<DashboardUiState> =
        combine(
            agent.connectionState,
            agent.authenticated,
            agent.paired,
            agent.lastCommand,
            agent.lastResult,
            _serviceRunning,
            settingsRepository.settings,
            AlfredAgentService.voiceListening,
            AlfredAgentService.lastVoiceText,
            AlfredAgentService.voiceStatus
        ) { values ->

            @Suppress("UNCHECKED_CAST")

            buildState(
                connectionState =
                    values[0] as ConnectionState,

                authenticated =
                    values[1] as Boolean,

                paired =
                    values[2] as Boolean,

                lastCommand =
                    values[3] as String?,

                lastResult =
                    values[4] as String?,

                serviceRunning =
                    values[5] as Boolean,

                settings =
                    values[6] as ConnectionSettings,

                voiceListening =
                    values[7] as Boolean,

                lastVoiceText =
                    values[8] as String,

                voiceStatus =
                    values[9] as String
            )

        }.stateIn(
            scope = viewModelScope,
            started =
                SharingStarted.WhileSubscribed(
                    5_000
                ),
            initialValue =
                DashboardUiState()
        )

    init {

        registerBatteryReceiver()

        observeAgentLogs()

        observeConnectionEvents()

        observeServiceState()
    }

    private fun observeServiceState() {

        viewModelScope.launch {

            AlfredAgentService
                .serviceRunning
                .collect { running ->

                    _serviceRunning.value =
                        running
                }
        }
    }

    fun toggleVoiceListening() {

        if (
            AlfredAgentService
                .voiceListening
                .value
        ) {

            stopVoiceListening()

        } else {

            startVoiceListening()
        }
    }

    fun startVoiceListening() {

        if (
            !_serviceRunning.value
        ) {

            logError(
                "Start the Alfred Agent service before using voice control."
            )

            return
        }

        AlfredAgentService
            .startVoice(
                app
            )
    }

    fun stopVoiceListening() {

        AlfredAgentService
            .stopVoice(
                app
            )
    }

    private fun registerBatteryReceiver() {

        app.registerReceiver(
            batteryReceiver,
            IntentFilter(
                Intent.ACTION_BATTERY_CHANGED
            )
        )
    }

    private fun observeAgentLogs() {

        viewModelScope.launch {

            agent.logs.collect { entry ->

                _logs.update { currentLogs ->

                    (
                        currentLogs + entry
                    ).takeLast(200)
                }
            }
        }
    }

    private fun observeConnectionEvents() {

        viewModelScope.launch {

            agent.connectionState
                .collect { state ->

                    when (state) {

                        ConnectionState.CONNECTED -> {

                            DeviceEvents.emit(
                                EventNames.DEVICE_CONNECTED,
                                identity.deviceId
                            )
                        }

                        ConnectionState.DISCONNECTED -> {

                            DeviceEvents.emit(
                                EventNames.DEVICE_DISCONNECTED,
                                identity.deviceId
                            )
                        }

                        else -> Unit
                    }
                }
        }
    }

    private fun buildState(
        connectionState: ConnectionState,
        authenticated: Boolean,
        paired: Boolean,
        lastCommand: String?,
        lastResult: String?,
        serviceRunning: Boolean,
        settings: ConnectionSettings,
        voiceListening: Boolean,
        lastVoiceText: String,
        voiceStatus: String
    ): DashboardUiState {

        val context: Context =
            app

        agent.refreshCapabilities()

        val capabilities =
            agent.registry
                .all()
                .sortedBy {
                    it.displayName
                }
                .map { capability ->

                    CapabilityStatus(
                        id =
                            capability.id,

                        displayName =
                            capability.displayName,

                        state =
                            capability.state.value
                    )
                }

        val permissions =
            AlfredPermissions.ALL.map {
                permission ->

                PermissionStatus(
                    name =
                        permission.displayName,

                    granted =
                        permission.isGranted(
                            context
                        )
                )

            } +
                listOf(

                    PermissionStatus(
                        name =
                            "Notification access",

                        granted =
                            NotificationState
                                .listenerConnected,

                        note =
                            if (
                                !NotificationState
                                    .listenerConnected
                            ) {
                                "Disabled"
                            } else {
                                null
                            }
                    ),

                    PermissionStatus(
                        name =
                            "Accessibility",

                        granted =
                            AccessibilityState
                                .connected,

                        note =
                            if (
                                !AccessibilityState
                                    .connected
                            ) {
                                "Disabled"
                            } else {
                                null
                            }
                    )
                )

        val battery =
            readBattery(
                context
            )

        return DashboardUiState(

            connectionState =
                connectionState,

            authenticated =
                authenticated,

            paired =
                paired,

            hubUrl =
                settings.hubUrl,

            deviceId =
                identity.deviceId,

            deviceName =
                settings.deviceName.ifBlank {
                    DeviceInfo
                        .defaultDisplayName()
                },

            manufacturer =
                DeviceInfo.manufacturer,

            model =
                DeviceInfo.model,

            androidVersion =
                DeviceInfo.androidVersion,

            appVersion =
                getAppVersion(),

            batteryLevel =
                battery.first,

            isCharging =
                battery.second,

            foregroundServiceRunning =
                serviceRunning,

            lastCommand =
                lastCommand,

            lastResult =
                lastResult,

            capabilities =
                capabilities,

            permissions =
                permissions,

            voiceListening =
                voiceListening,

            lastVoiceText =
                lastVoiceText,

            voiceStatus =
                voiceStatus
        )
    }

    private fun getAppVersion(): String {

        return runCatching {

            app.packageManager
                .getPackageInfo(
                    app.packageName,
                    0
                )
                .versionName

        }.getOrNull()
            ?: "0.1.0"
    }

    fun startService() {

        servicePrefs
            .edit()
            .putBoolean(
                "service_enabled",
                true
            )
            .apply()

        _serviceRunning.value =
            true

        logInfo(
            "Starting Alfred Agent..."
        )

        AlfredAgentService.start(
            app
        )
    }

    fun stopService() {

        servicePrefs
            .edit()
            .putBoolean(
                "service_enabled",
                false
            )
            .apply()

        _serviceRunning.value =
            false

        logInfo(
            "Stopping Alfred Agent..."
        )

        AlfredAgentService.stop(
            app
        )
    }

    fun testConnection() {

        val hubUrl =
            uiState.value.hubUrl

        if (
            hubUrl.isBlank()
        ) {

            logError(
                "Hub URL not configured"
            )

            return
        }

        logInfo(
            "Testing connection to Hub..."
        )

        startService()
    }

    fun pairWithCode(
        code: String
    ) {

        if (
            code.isBlank()
        ) {

            logError(
                "Pairing code is empty"
            )

            return
        }

        val sent =
            agent.sendPairRequest(
                code.trim()
            )

        if (!sent) {

            logError(
                "Cannot pair: not connected. Start the Agent and configure the Hub first."
            )

        } else {

            logInfo(
                "Pair request sent"
            )
        }
    }

    fun revokePairing() {

        agent.unpair()

        logInfo(
            "Pairing revoked"
        )
    }

    fun clearLogs() {

        _logs.value =
            emptyList()
    }

    private fun logInfo(
        message: String
    ) {

        addLog(
            LogLevel.INFO,
            message
        )
    }

    private fun logError(
        message: String
    ) {

        addLog(
            LogLevel.ERROR,
            message
        )
    }

    private fun addLog(
        level: LogLevel,
        message: String
    ) {

        _logs.update { currentLogs ->

            (
                currentLogs +
                    LogEntry(
                        ts =
                            System.currentTimeMillis(),

                        level =
                            level,

                        message =
                            message
                    )
            ).takeLast(200)
        }
    }

    private fun readBattery(
        context: Context
    ): Pair<Int?, Boolean?> {

        val intent =
            context.registerReceiver(
                null,
                IntentFilter(
                    Intent.ACTION_BATTERY_CHANGED
                )
            )
                ?: return null to null

        val level =
            intent.getIntExtra(
                BatteryManager.EXTRA_LEVEL,
                -1
            )

        val scale =
            intent.getIntExtra(
                BatteryManager.EXTRA_SCALE,
                -1
            )

        val percentage =
            if (
                level >= 0 &&
                scale > 0
            ) {

                level * 100 / scale

            } else {

                null
            }

        val status =
            intent.getIntExtra(
                BatteryManager.EXTRA_STATUS,
                -1
            )

        val charging =
            status ==
                BatteryManager
                    .BATTERY_STATUS_CHARGING ||
            status ==
                BatteryManager
                    .BATTERY_STATUS_FULL

        return percentage to charging
    }

    override fun onCleared() {

        runCatching {

            app.unregisterReceiver(
                batteryReceiver
            )
        }

        super.onCleared()
    }
}