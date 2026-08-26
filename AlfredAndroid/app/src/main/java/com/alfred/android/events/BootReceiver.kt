package com.alfred.android.events

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.alfred.android.service.AlfredAgentService
import com.alfred.android.storage.SettingsRepository
import com.alfred.android.util.Logger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class BootReceiver : BroadcastReceiver() {
    private val tag = "ALFRED-Boot"
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED) return
        val pending = goAsync()
        CoroutineScope(Dispatchers.Default).launch {
            try {
                val prefs = context.getSharedPreferences("alfred_service_prefs", Context.MODE_PRIVATE)
                if (!prefs.getBoolean("service_enabled", false)) return@launch
                val settings = SettingsRepository(context).settings.first()
                if (settings.hubUrl.isBlank()) return@launch
                Logger.i(tag, "Restarting agent after boot")
                AlfredAgentService.start(context)
            } finally { pending.finish() }
        }
    }
}
