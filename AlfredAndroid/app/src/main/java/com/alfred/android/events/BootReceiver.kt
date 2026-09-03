package com.alfred.android.events

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.alfred.android.util.Logger

class BootReceiver : BroadcastReceiver() {

    private val tag = "ALFRED-Boot"

    override fun onReceive(
        context: Context,
        intent: Intent
    ) {

        if (
            intent.action !=
            Intent.ACTION_BOOT_COMPLETED
        ) {
            return
        }

        val prefs =
            context.getSharedPreferences(
                "alfred_service_prefs",
                Context.MODE_PRIVATE
            )

        val serviceEnabled =
            prefs.getBoolean(
                "service_enabled",
                false
            )

        if (serviceEnabled) {

            Logger.i(
                tag,
                "Device boot completed. ALFRED is enabled; waiting for user-visible startup."
            )

        } else {

            Logger.i(
                tag,
                "Device boot completed. ALFRED service is disabled."
            )
        }
    }
}