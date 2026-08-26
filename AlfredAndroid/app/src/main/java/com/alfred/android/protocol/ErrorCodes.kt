package com.alfred.android.protocol

import kotlinx.serialization.Serializable

object ErrorCodes {
    const val PERMISSION_REQUIRED = "permission_required"
    const val CAPABILITY_UNAVAILABLE = "capability_unavailable"
    const val UNSUPPORTED_ACTION = "unsupported_action"
    const val INVALID_PARAMETERS = "invalid_parameters"
    const val DEVICE_LOCKED = "device_locked"
    const val AUTHENTICATION_FAILED = "authentication_failed"
    const val NOT_CONNECTED = "not_connected"
    const val TIMEOUT = "timeout"
    const val CONFIRMATION_REQUIRED = "confirmation_required"
    const val INTERNAL_ERROR = "internal_error"
}

@Serializable
data class CommandError(
    val code: String,
    val message: String,
    val capability: String? = null,
    val data: Map<String, String>? = null,
)
