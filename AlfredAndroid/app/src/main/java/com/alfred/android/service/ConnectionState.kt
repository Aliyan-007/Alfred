package com.alfred.android.service

enum class ConnectionState {
    DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, AUTHENTICATION_FAILED;

    val displayName: String
        get() = when (this) {
            DISCONNECTED -> "Disconnected"
            CONNECTING -> "Connecting"
            CONNECTED -> "Connected to Hub"
            RECONNECTING -> "Reconnecting"
            AUTHENTICATION_FAILED -> "Authentication failed"
        }
}
