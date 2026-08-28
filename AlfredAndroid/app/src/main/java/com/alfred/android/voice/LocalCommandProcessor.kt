package com.alfred.android.voice

import android.content.Context
import com.alfred.android.agent.AlfredAgent
import com.alfred.android.protocol.Command
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.util.UUID

class LocalCommandProcessor(
    private val context: Context,
    private val agent: AlfredAgent,
) {

    suspend fun execute(
        spokenText: String
    ): String {

        val command = parseCommand(spokenText)

        if (command == null) {
            return "Sorry Sir, I do not understand that command yet"
        }

        val result = try {
            agent.registry.dispatch(
                command,
                context
            )
        } catch (error: Exception) {
            return error.message ?: "Something went wrong"
        }

        if (!result.success) {
            return result.error?.message
                ?: "The command failed"
        }

        return successMessage(
            action = command.action,
            result = result.result?.toString()
        )
    }

    private fun parseCommand(
        spokenText: String
    ): Command? {

        val text = spokenText
            .trim()
            .lowercase()

        if (text.isBlank()) {
            return null
        }

        fun command(
            action: String,
            parameters: JsonObject = buildJsonObject {}
        ): Command {

            return Command(
                id = UUID.randomUUID().toString(),
                device = null,
                action = action,
                parameters = parameters,
                confirm = false,
            )
        }

        // =================================================
        // BATTERY
        // =================================================

        if (
            text.contains("battery")
        ) {

            return command(
                action = "battery.status"
            )
        }

        // =================================================
        // DEVICE INFORMATION
        // =================================================

        if (
            text.contains("device info") ||
            text.contains("phone info") ||
            text.contains("device information")
        ) {

            return command(
                action = "device_info.status"
            )
        }

        // =================================================
        // FLASHLIGHT
        // =================================================

        if (
            text.contains("flashlight on") ||
            text.contains("turn on flashlight") ||
            text.contains("turn flashlight on") ||
            text.contains("torch on")
        ) {

            return command(
                action = "hardware.flashlight_on"
            )
        }

        if (
            text.contains("flashlight off") ||
            text.contains("turn off flashlight") ||
            text.contains("turn flashlight off") ||
            text.contains("torch off")
        ) {

            return command(
                action = "hardware.flashlight_off"
            )
        }

        // =================================================
        // VIBRATE
        // =================================================

        if (
            text == "vibrate" ||
            text.contains("vibrate phone") ||
            text.contains("make phone vibrate")
        ) {

            return command(
                action = "hardware.vibrate",
                parameters = buildJsonObject {
                    put(
                        "duration_ms",
                        500
                    )
                }
            )
        }

        // =================================================
        // VOLUME
        // =================================================

        if (
            text.contains("volume up") ||
            text.contains("increase volume") ||
            text.contains("make it louder") ||
            text.contains("louder")
        ) {

            return command(
                action = "volume.up"
            )
        }

        if (
            text.contains("volume down") ||
            text.contains("decrease volume") ||
            text.contains("lower volume") ||
            text.contains("make it quieter") ||
            text.contains("quieter")
        ) {

            return command(
                action = "volume.down"
            )
        }

        if (
            text == "mute" ||
            text.contains("mute phone") ||
            text.contains("mute volume")
        ) {

            return command(
                action = "volume.mute"
            )
        }

        if (
            text.contains("unmute")
        ) {

            return command(
                action = "volume.unmute"
            )
        }

        // =================================================
        // MEDIA
        // =================================================

        if (
            text == "play" ||
            text.contains("play music") ||
            text.contains("resume music") ||
            text.contains("resume")
        ) {

            return command(
                action = "media.play"
            )
        }

        if (
            text == "pause" ||
            text.contains("pause music")
        ) {

            return command(
                action = "media.pause"
            )
        }

        if (
            text == "next" ||
            text.contains("next song") ||
            text.contains("next track") ||
            text.contains("skip song")
        ) {

            return command(
                action = "media.next"
            )
        }

        if (
            text == "previous" ||
            text.contains("previous song") ||
            text.contains("previous track")
        ) {

            return command(
                action = "media.previous"
            )
        }

        // =================================================
        // OPEN WEBSITE
        // =================================================

        if (
            text.contains("open youtube website") ||
            text.contains("go to youtube")
        ) {

            return command(
                action = "url.open",
                parameters = buildJsonObject {
                    put(
                        "url",
                        "https://www.youtube.com"
                    )
                }
            )
        }

        if (
            text.contains("open google website") ||
            text.contains("go to google")
        ) {

            return command(
                action = "url.open",
                parameters = buildJsonObject {
                    put(
                        "url",
                        "https://www.google.com"
                    )
                }
            )
        }

        // =================================================
        // OPEN APPLICATION
        // =================================================

        if (
            text.startsWith("open ")
        ) {

            val appName = spokenText
                .trim()
                .substringAfter(
                    "open ",
                    ""
                )
                .trim()

            if (appName.isNotBlank()) {

                return command(
                    action = "apps.open",
                    parameters = buildJsonObject {
                        put(
                            "name",
                            appName
                        )
                    }
                )
            }
        }

        return null
    }

    private fun successMessage(
        action: String,
        result: String?
    ): String {

        return when {

            action.contains("battery") ->
                "Here is your battery information"

            action.contains("flashlight_on") ->
                "Flashlight turned on"

            action.contains("flashlight_off") ->
                "Flashlight turned off"

            action.contains("vibrate") ->
                "Done Sir"

            action == "volume.up" ->
                "Volume increased"

            action == "volume.down" ->
                "Volume decreased"

            action == "volume.mute" ->
                "Phone muted"

            action == "volume.unmute" ->
                "Phone unmuted"

            action.startsWith("media") ->
                "Done Sir"

            action == "url.open" ->
                "Opening it now"

            action.startsWith("apps") ->
                "Opening the app"

            else ->
                result ?: "Done Sir"
        }
    }
}