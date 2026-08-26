package com.alfred.android.pairing

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import com.alfred.android.util.Logger

class CredentialStore(context: Context) {
    private val tag = "ALFRED-Creds"
    private val prefs: SharedPreferences? = try {
        val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
        EncryptedSharedPreferences.create(
            "alfred_credentials", masterKeyAlias, context,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    } catch (t: Throwable) {
        Logger.e(tag, "Encrypted storage unavailable: ${t.message}")
        null
    }

    fun saveToken(token: String) {
        prefs?.edit()?.putString(KEY_TOKEN, token)?.apply()
    }
    fun getToken(): String? = prefs?.getString(KEY_TOKEN, null)
    fun clearToken() { prefs?.edit()?.remove(KEY_TOKEN)?.apply() }
    fun isPaired(): Boolean = !getToken().isNullOrBlank()

    companion object { private const val KEY_TOKEN = "hub_auth_token" }
}
