package com.alfred.android.events

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.BatteryManager
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

class BatteryEventReceiver(private val deviceId: String) : BroadcastReceiver() {
    @Volatile private var lastLevel = -1
    @Volatile private var lastCharging: Boolean? = null

    override fun onReceive(context: Context, intent: Intent) {
        if (Intent.ACTION_BATTERY_CHANGED != intent.action) return
        val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
        val status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
        val pct = if (level >= 0 && scale > 0) level * 100 / scale else -1
        val charging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
        if (pct >= 0 && pct != lastLevel) {
            DeviceEvents.emit(EventNames.BATTERY_CHANGED, deviceId, buildJsonObject {
                put("battery", JsonPrimitive(pct)); put("charging", JsonPrimitive(charging))
            })
            lastLevel = pct
        }
        if (lastCharging != null && lastCharging != charging) {
            DeviceEvents.emit(if (charging) EventNames.CHARGING_STARTED else EventNames.CHARGING_STOPPED, deviceId,
                buildJsonObject { put("battery", JsonPrimitive(pct)) })
        }
        lastCharging = charging
    }
}
