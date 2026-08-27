package com.alfred.android.capabilities.settings

import android.content.Context
import android.content.Intent
import android.provider.Settings

import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.ErrorCodes

import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject


class SettingsCapability : BaseCapability() {

    override val id = "settings"

    override val displayName = "System Settings"


    override fun refresh(
        context: Context
    ) {

        setState(
            CapabilityState.AVAILABLE
        )
    }


    override suspend fun handle(
        command: Command,
        context: Context
    ): CommandResult {

        val action =
            command.action
                .substringAfter(
                    ".",
                    "main"
                )
                .lowercase()


        val intent =
            when (action) {

                "main",
                "open" ->
                    Intent(
                        Settings.ACTION_SETTINGS
                    )

                "wifi" ->
                    Intent(
                        Settings.ACTION_WIFI_SETTINGS
                    )

                "bluetooth" ->
                    Intent(
                        Settings.ACTION_BLUETOOTH_SETTINGS
                    )

                "sound" ->
                    Intent(
                        Settings.ACTION_SOUND_SETTINGS
                    )

                "display" ->
                    Intent(
                        Settings.ACTION_DISPLAY_SETTINGS
                    )

                "accessibility" ->
                    Intent(
                        Settings.ACTION_ACCESSIBILITY_SETTINGS
                    )

                "apps",
                "applications" ->
                    Intent(
                        Settings.ACTION_APPLICATION_SETTINGS
                    )

                "battery" ->
                    Intent(
                        Settings.ACTION_BATTERY_SAVER_SETTINGS
                    )

                "location" ->
                    Intent(
                        Settings.ACTION_LOCATION_SOURCE_SETTINGS
                    )

                "network" ->
                    Intent(
                        Settings.ACTION_WIRELESS_SETTINGS
                    )

                else ->
                    return CommandResult.failure(
                        command.id,
                        CommandError(
                            ErrorCodes.UNSUPPORTED_ACTION,
                            "Unknown settings action: $action",
                            id
                        )
                    )
            }


        intent.addFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK
        )


        return try {

            context.startActivity(
                intent
            )


            CommandResult.success(
                command.id,
                buildJsonObject {

                    put(
                        "opened",
                        JsonPrimitive(
                            action
                        )
                    )
                }
            )

        } catch (
            error: Throwable
        ) {

            CommandResult.failure(
                command.id,
                CommandError(
                    ErrorCodes.INTERNAL_ERROR,
                    error.message
                        ?: "Failed to open settings",
                    id
                )
            )
        }
    }
}
