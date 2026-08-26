package com.alfred.android.events

import com.alfred.android.protocol.DeviceEvent
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.serialization.json.JsonObject

object DeviceEvents {
    private val _bus = MutableSharedFlow<DeviceEvent>(extraBufferCapacity = 64)
    val bus: SharedFlow<DeviceEvent> = _bus.asSharedFlow()

    fun emit(event: String, deviceId: String, data: JsonObject = JsonObject(emptyMap())) {
        _bus.tryEmit(DeviceEvent(event = event, device = deviceId, data = data, ts = System.currentTimeMillis()))
    }
}

object EventNames {
    const val BATTERY_CHANGED = "battery_changed"
    const val CHARGING_STARTED = "charging_started"
    const val CHARGING_STOPPED = "charging_stopped"
    const val DEVICE_CONNECTED = "device_connected"
    const val DEVICE_DISCONNECTED = "device_disconnected"
    const val NOTIFICATION_RECEIVED = "notification_received"
}
