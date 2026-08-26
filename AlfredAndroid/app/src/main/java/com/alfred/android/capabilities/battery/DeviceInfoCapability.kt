package com.alfred.android.capabilities.battery

import android.content.Context
import android.os.Build
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.registry.DeviceIdentity
import com.alfred.android.util.DeviceInfo
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

class DeviceInfoCapability : BaseCapability() {
    override val id = "device_info"
    override val displayName = "Device Info"
    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult {
        val identity = DeviceIdentity(context)
        val pInfo = context.packageManager.getPackageInfo(context.packageName, 0)
        return CommandResult.success(command.id, buildJsonObject {
            put("manufacturer", JsonPrimitive(DeviceInfo.manufacturer))
            put("model", JsonPrimitive(DeviceInfo.model))
            put("android_version", JsonPrimitive(DeviceInfo.androidVersion))
            put("sdk", JsonPrimitive(DeviceInfo.sdkInt))
            put("device_id", JsonPrimitive(identity.deviceId))
            put("name", JsonPrimitive(identity.deviceName))
            put("app_version", JsonPrimitive(pInfo.versionName ?: "unknown"))
            put("brand", JsonPrimitive(Build.BRAND))
            put("product", JsonPrimitive(Build.PRODUCT))
        })
    }
}
