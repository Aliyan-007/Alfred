package com.alfred.android.protocol

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class Command(
    val id: String,
    val device: String? = null,
    val action: String,
    val parameters: JsonObject = JsonObject(emptyMap()),
    val confirm: Boolean = false,
)

@Serializable
data class CommandResult(
    val type: String = "command_result",
    val id: String,
    val success: Boolean,
    val result: JsonObject? = null,
    val error: CommandError? = null,
) {
    companion object {
        fun success(id: String, result: JsonObject) = CommandResult(id = id, success = true, result = result)
        fun failure(id: String, error: CommandError) = CommandResult(id = id, success = false, error = error)
    }
}

@Serializable
data class RegistrationMessage(
    val type: String = "register",
    @SerialName("device_id") val deviceId: String,
    val name: String,
    @SerialName("device_type") val deviceType: String = "android",
    val capabilities: List<CapabilityWireInfo> = emptyList(),
    val permissions: List<String> = emptyList(),
    @SerialName("app_version") val appVersion: String,
    @SerialName("android_version") val androidVersion: String,
    val manufacturer: String,
    val model: String,
    @SerialName("auth_token") val authToken: String? = null,
)

@Serializable
data class CapabilityWireInfo(val id: String, val state: String)

@Serializable
data class RegistrationResponse(
    val type: String = "registered",
    val success: Boolean = true,
    val reason: String? = null,
    @SerialName("device_id") val deviceId: String? = null,
)

@Serializable
data class PairRequest(
    val type: String = "pair",
    val code: String,
    val name: String,
    @SerialName("device_type") val deviceType: String = "android",
)

@Serializable
data class PairResponse(
    val type: String = "pair_response",
    val success: Boolean,
    @SerialName("auth_token") val authToken: String? = null,
    @SerialName("device_id") val deviceId: String? = null,
    val reason: String? = null,
)

@Serializable
data class DeviceEvent(
    val type: String = "event",
    val event: String,
    val device: String,
    val data: JsonObject = JsonObject(emptyMap()),
    val ts: Long = 0,
)
