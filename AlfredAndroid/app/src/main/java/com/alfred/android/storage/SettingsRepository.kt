package com.alfred.android.storage

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.alfred.android.util.Constants
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = Constants.DATASTORE_NAME)

data class ConnectionSettings(
    val hubHost: String,
    val hubPort: Int,
    val hubScheme: String,
    val deviceName: String,
    val deviceIdOverride: String,
) {
    val hubUrl: String get() = if (hubHost.isBlank()) "" else "$hubScheme://$hubHost:$hubPort"
}

class SettingsRepository(private val context: Context) {
    private object Keys {
        val HUB_HOST = stringPreferencesKey("hub_host")
        val HUB_PORT = intPreferencesKey("hub_port")
        val HUB_SCHEME = stringPreferencesKey("hub_scheme")
        val DEVICE_NAME = stringPreferencesKey("device_name")
        val DEVICE_ID_OVERRIDE = stringPreferencesKey("device_id_override")
    }

    val settings: Flow<ConnectionSettings> = context.dataStore.data.map { p ->
        ConnectionSettings(
            hubHost = p[Keys.HUB_HOST] ?: "",
            hubPort = p[Keys.HUB_PORT] ?: Constants.DEFAULT_HUB_PORT,
            hubScheme = p[Keys.HUB_SCHEME] ?: Constants.DEFAULT_HUB_SCHEME,
            deviceName = p[Keys.DEVICE_NAME] ?: "",
            deviceIdOverride = p[Keys.DEVICE_ID_OVERRIDE] ?: "",
        )
    }

    suspend fun setHubHost(host: String) = context.dataStore.edit { it[Keys.HUB_HOST] = host.trim() }
    suspend fun setHubPort(port: Int) = context.dataStore.edit { it[Keys.HUB_PORT] = port.coerceIn(1, 65535) }
    suspend fun setHubScheme(scheme: String) {
        val clean = scheme.lowercase().trim()
        require(clean == "ws" || clean == "wss")
        context.dataStore.edit { it[Keys.HUB_SCHEME] = clean }
    }
    suspend fun setDeviceName(name: String) = context.dataStore.edit { it[Keys.DEVICE_NAME] = name.trim() }
}
