package com.alfred.android.util

object Constants {
    const val DEFAULT_HUB_PORT = 8765
    const val DEFAULT_HUB_SCHEME = "ws"
    const val DEFAULT_CONNECT_TIMEOUT_MS = 10_000L
    const val DEFAULT_RECONNECT_BASE_DELAY_MS = 1_000L
    const val DEFAULT_RECONNECT_MAX_DELAY_MS = 60_000L
    const val DEFAULT_HEARTBEAT_INTERVAL_MS = 25_000L
    const val DATASTORE_NAME = "alfred_settings"
    const val NOTIF_CHANNEL_CONNECTION = "alfred_connection"
    const val NOTIF_ID_CONNECTION = 1001
}
