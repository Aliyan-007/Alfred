package com.alfred.android.registry

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.alfred.android.util.DeviceInfo
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking

private val Context.identityDataStore by preferencesDataStore(name = "alfred_identity")

class DeviceIdentity(private val context: Context) {
    private object Keys {
        val DEVICE_ID = stringPreferencesKey("device_id")
        val DEVICE_NAME = stringPreferencesKey("device_name")
    }

    val deviceId: String
        get() = runBlocking {
            context.identityDataStore.data.first()[Keys.DEVICE_ID] ?: generateAndStoreId()
        }

    val deviceName: String
        get() = runBlocking {
            context.identityDataStore.data.first()[Keys.DEVICE_NAME] ?: DeviceInfo.defaultDisplayName()
        }

    private suspend fun generateAndStoreId(): String {
        val id = "android_" + java.util.UUID.randomUUID().toString().take(12).replace("-", "")
        context.identityDataStore.edit { it[Keys.DEVICE_ID] = id }
        return id
    }

    suspend fun setDeviceName(name: String) {
        val clean = name.trim().ifBlank { DeviceInfo.defaultDisplayName() }
        context.identityDataStore.edit { it[Keys.DEVICE_NAME] = clean }
    }

    suspend fun reset() { context.identityDataStore.edit { it.clear() } }
}
