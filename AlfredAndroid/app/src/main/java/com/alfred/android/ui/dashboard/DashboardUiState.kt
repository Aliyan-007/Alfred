package com.alfred.android.ui.dashboard

import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.service.ConnectionState

data class DashboardUiState(
val connectionState: ConnectionState = ConnectionState.DISCONNECTED,
val authenticated: Boolean = false,
val paired: Boolean = false,
val hubUrl: String = "",
val deviceId: String = "",
val deviceName: String = "",
val manufacturer: String = "",
val model: String = "",
val androidVersion: String = "",
val appVersion: String = "",
val batteryLevel: Int? = null,
val isCharging: Boolean? = null,
val foregroundServiceRunning: Boolean = false,
val lastCommand: String? = null,
val lastResult: String? = null,
val capabilities: List<CapabilityStatus> = emptyList(),
val permissions: List<PermissionStatus> = emptyList(),
val voiceListening: Boolean = false,
val lastVoiceText: String = "",
val voiceStatus: String = "Ready"
)

data class CapabilityStatus(
val id: String,
val displayName: String,
val state: CapabilityState
)

data class PermissionStatus(
val name: String,
val granted: Boolean,
val note: String? = null
)
