package com.alfred.android.voice

import com.alfred.android.protocol.Command
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import java.util.UUID

object LocalCommandParser {

    fun parse(
        text: String,
    ): Command? {

        val input =
            text
                .trim()
                .lowercase()

        if (
            input.isBlank()
        ) {
            return null
        }


        // =================================================
        // BATTERY
        // =================================================

        if (
            input.contains("battery")
        ) {

            return command(
                action = "battery"
            )
        }


        // =================================================
        // DEVICE INFO
        // =================================================

        if (
            input.contains("device info") ||
            input.contains("phone info") ||
            input.contains("device information")
        ) {

            return command(
                action = "device_info"
            )
        }


        // =================================================
        // OPEN APPLICATION
        // =================================================

        if (
            input.startsWith("open ")
        ) {

            val appName =
                input
                    .removePrefix("open ")
                    .trim()

            if (
                appName.isNotBlank()
            ) {

                return command(
                    action = "apps.open_app",
                    parameters =
                        buildJsonObject {

                            put(
                                "app_name",
                                JsonPrimitive(
                                    appName
                                )
                            )
                        }
                )
            }
        }


        // =================================================
        // SPECIFIC APPS
        // =================================================

        val knownApps =
            mapOf(

                "youtube" to "youtube",

                "spotify" to "spotify",

                "whatsapp" to "whatsapp",

                "instagram" to "instagram",

                "facebook" to "facebook",

                "chrome" to "chrome",

                "google" to "chrome",

                "gmail" to "gmail",

                "telegram" to "telegram",

                "settings" to "settings",

                "camera" to "camera",
            )

        for (
            (spokenName, appName)
            in knownApps
        ) {

            if (
                input.contains(
                    "open $spokenName"
                )
            ) {

                return command(
                    action =
                        "apps.open_app",

                    parameters =
                        buildJsonObject {

                            put(
                                "app_name",

                                JsonPrimitive(
                                    appName
                                )
                            )
                        }
                )
            }
        }


        // =================================================
        // VOLUME UP
        // =================================================

        if (

            input.contains("volume up") ||

            input.contains("increase volume") ||

            input.contains("louder")
        ) {

            return command(
                action =
                    "volume.up"
            )
        }


        // =================================================
        // VOLUME DOWN
        // =================================================

        if (

            input.contains("volume down") ||

            input.contains("decrease volume") ||

            input.contains("lower volume") ||

            input.contains("quieter")
        ) {

            return command(
                action =
                    "volume.down"
            )
        }


        // =================================================
        // MUTE
        // =================================================

        if (

            input == "mute" ||

            input.contains("mute phone") ||

            input.contains("mute volume")
        ) {

            return command(
                action =
                    "volume.mute"
            )
        }


        // =================================================
        // MEDIA PLAY
        // =================================================

        if (

            input == "play" ||

            input.contains("resume music") ||

            input.contains("play music")
        ) {

            return command(
                action =
                    "media.play"
            )
        }


        // =================================================
        // MEDIA PAUSE
        // =================================================

        if (

            input == "pause" ||

            input.contains("pause music") ||

            input.contains("stop music")
        ) {

            return command(
                action =
                    "media.pause"
            )
        }


        // =================================================
        // NEXT
        // =================================================

        if (

            input == "next" ||

            input.contains("next song") ||

            input.contains("skip song")
        ) {

            return command(
                action =
                    "media.next"
            )
        }


        // =================================================
        // PREVIOUS
        // =================================================

        if (

            input == "previous" ||

            input.contains("previous song") ||

            input.contains("go back song")
        ) {

            return command(
                action =
                    "media.previous"
            )
        }


        // =================================================
        // FLASHLIGHT ON
        // =================================================

        if (

            input.contains("flashlight on") ||

            input.contains("turn on flashlight") ||

            input.contains("torch on")
        ) {

            return command(
                action =
                    "hardware.flashlight_on"
            )
        }


        // =================================================
        // FLASHLIGHT OFF
        // =================================================

        if (

            input.contains("flashlight off") ||

            input.contains("turn off flashlight") ||

            input.contains("torch off")
        ) {

            return command(
                action =
                    "hardware.flashlight_off"
            )
        }


        // =================================================
        // VIBRATE
        // =================================================

        if (

            input == "vibrate" ||

            input.contains("vibrate phone")
        ) {

            return command(
                action =
                    "hardware.vibrate",

                parameters =
                    buildJsonObject {

                        put(
                            "duration",

                            JsonPrimitive(
                                500
                            )
                        )
                    }
            )
        }


        // =================================================
        // OPEN URL
        // =================================================

        if (

            input.startsWith("go to ")
        ) {

            var url =
                input
                    .removePrefix(
                        "go to "
                    )
                    .trim()


            if (
                !url.startsWith(
                    "http://"
                ) &&

                !url.startsWith(
                    "https://"
                )
            ) {

                url =
                    "https://$url"
            }


            return command(
                action =
                    "url.open",

                parameters =
                    buildJsonObject {

                        put(
                            "url",

                            JsonPrimitive(
                                url
                            )
                        )
                    }
            )
        }


        return null
    }


    // =====================================================
    // CREATE COMMAND
    // =====================================================

    private fun command(

        action: String,

        parameters:
            kotlinx.serialization.json.JsonObject =
                buildJsonObject {},

    ): Command {

        return Command(

            id =
                "local_"
                    + UUID
                        .randomUUID()
                        .toString(),

            device = null,

            action =
                action,

            parameters =
                parameters,

            confirm =
                false,
        )
    }
}
