package com.alfred.android.voice

import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.os.BatteryManager
import android.provider.Settings
import android.widget.Toast
import com.alfred.android.agent.AlfredAgent

class LocalCommandProcessor(
    private val context: Context,
    private val agent: AlfredAgent
) {

    suspend fun execute(
        spokenText: String
    ): String {

        val command =
            normalize(spokenText)

        if (command.isBlank()) {
            return "Sir, mujhe command samajh nahi aayi."
        }

        return when {

            // -----------------------------------------
            // BATTERY
            // -----------------------------------------

            isBatteryCommand(command) ->
                getBatteryResponse()

            // -----------------------------------------
            // FLASHLIGHT
            // -----------------------------------------

            isFlashlightOnCommand(command) ->
                flashlightOn()

            isFlashlightOffCommand(command) ->
                flashlightOff()

            // -----------------------------------------
            // VOLUME
            // -----------------------------------------

            isVolumeUpCommand(command) ->
                volumeUp()

            isVolumeDownCommand(command) ->
                volumeDown()

            // -----------------------------------------
            // SETTINGS
            // -----------------------------------------

            isOpenSettingsCommand(command) ->
                openSettings()

            // -----------------------------------------
            // APPS
            // -----------------------------------------

            isOpenYoutubeCommand(command) ->
                openApp(
                    packageName = "com.google.android.youtube",
                    appName = "YouTube"
                )

            isOpenWhatsappCommand(command) ->
                openApp(
                    packageName = "com.whatsapp",
                    appName = "WhatsApp"
                )

            isOpenSpotifyCommand(command) ->
                openApp(
                    packageName = "com.spotify.music",
                    appName = "Spotify"
                )

            // -----------------------------------------
            // GREETING
            // -----------------------------------------

            isGreeting(command) ->
                greetingResponse()

            // -----------------------------------------
            // HELP
            // -----------------------------------------

            isHelpCommand(command) ->
                helpResponse()

            // -----------------------------------------
            // UNKNOWN
            // -----------------------------------------

            else ->
                unknownCommand(spokenText)
        }
    }

    // =================================================
    // NORMALIZATION
    // =================================================

    private fun normalize(
        text: String
    ): String {

        var command =
            text
                .lowercase()
                .trim()

        // -----------------------------------------
        // Common speech recognition variations
        // -----------------------------------------

        command =
            command
                .replace(
                    "assalam o alaikum",
                    "salam"
                )
                .replace(
                    "assalamu alaikum",
                    "salam"
                )
                .replace(
                    "assalamualaikum",
                    "salam"
                )
                .replace(
                    "al salam alaikum",
                    "salam"
                )

        // -----------------------------------------
        // Remove punctuation
        // -----------------------------------------

        command =
            command.replace(
                Regex("[,\\.?!:;]"),
                " "
            )

        // -----------------------------------------
        // Wake words
        // -----------------------------------------

        val wakeWords =
            listOf(
                "hey alfred",
                "hello alfred",
                "hi alfred",
                "oye alfred",
                "ok alfred",
                "okay alfred",
                "alfred",

                "hey friday",
                "hello friday",
                "hi friday",
                "oye friday",
                "ok friday",
                "okay friday",
                "friday"
            )

        wakeWords.forEach { wakeWord ->

            command =
                command.replace(
                    wakeWord,
                    " "
                )
        }

        // -----------------------------------------
        // Common Roman Urdu variations
        // -----------------------------------------

        command =
            command
                .replace(
                    "karo na",
                    "karo"
                )
                .replace(
                    "kr do",
                    "karo"
                )
                .replace(
                    "krdo",
                    "karo"
                )
                .replace(
                    "kardo",
                    "karo"
                )
                .replace(
                    "kar do",
                    "karo"
                )
                .replace(
                    "kholo na",
                    "kholo"
                )
                .replace(
                    "khol do",
                    "kholo"
                )
                .replace(
                    "kholna",
                    "kholo"
                )
                .replace(
                    "chala do",
                    "chalao"
                )
                .replace(
                    "chalao na",
                    "chalao"
                )
                .replace(
                    "jala do",
                    "jalao"
                )
                .replace(
                    "bata do",
                    "batao"
                )
                .replace(
                    "btao",
                    "batao"
                )
                .replace(
                    "btana",
                    "batao"
                )

        // -----------------------------------------
        // Normalize multiple spaces
        // -----------------------------------------

        return command
            .replace(
                Regex("\\s+"),
                " "
            )
            .trim()
    }

    // =================================================
    // BATTERY
    // =================================================

    private fun isBatteryCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "battery",

                "battery kitni",
                "battery kitna",

                "battery percentage",
                "battery percent",
                "battery level",

                "battery kitni hai",
                "battery kitna hai",

                "charge kitna",
                "charge kitni",

                "charge kitna hai",
                "charge kitni hai",

                "phone charge",

                "phone ki battery",
                "phone ki charge",

                "kitni battery",
                "kitna battery",

                "kitna charge",
                "kitni charge",

                "battery batao",
                "battery btao",

                "charge batao",
                "charge btao",

                "phone ki battery batao",
                "phone ki battery kitni hai",

                "mera charge kitna hai",
                "meri battery kitni hai"
            )
        )
    }

    private fun getBatteryResponse(): String {

        val batteryManager =
            context.getSystemService(
                Context.BATTERY_SERVICE
            ) as BatteryManager

        val level =
            batteryManager.getIntProperty(
                BatteryManager.BATTERY_PROPERTY_CAPACITY
            )

        return if (level >= 0) {

            "Sir, battery $level percent hai."

        } else {

            "Sir, main battery level read nahi kar saka."
        }
    }

    // =================================================
    // FLASHLIGHT
    // =================================================

    private fun isFlashlightOnCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "flashlight on",
                "flashlight chalao",
                "flashlight jalao",
                "flashlight kholo",
                "flashlight chalu",
                "flashlight start",

                "torch on",
                "torch chalao",
                "torch jalao",
                "torch kholo",
                "torch chalu",
                "torch start",

                "torch laga do",
                "torch laga",

                "light on",
                "light chalao",
                "light jalao",
                "light kholo",
                "light chalu",

                "flash on",
                "flash chalao"
            )
        )
    }

    private fun isFlashlightOffCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "flashlight off",
                "flashlight band",
                "flashlight bandh",
                "flashlight band karo",
                "flashlight bandh karo",

                "torch off",
                "torch band",
                "torch bandh",
                "torch band karo",
                "torch bandh karo",

                "light off",
                "light band",
                "light bandh",
                "light band karo",
                "light bandh karo",

                "flash off",
                "flash band",
                "flash bandh"
            )
        )
    }

    private fun flashlightOn(): String {

        return try {

            val cameraManager =
                context.getSystemService(
                    Context.CAMERA_SERVICE
                ) as android.hardware.camera2.CameraManager

            val cameraId =
                cameraManager.cameraIdList
                    .firstOrNull()

            if (cameraId == null) {

                "Sir, flashlight available nahi hai."

            } else {

                cameraManager.setTorchMode(
                    cameraId,
                    true
                )

                "Ji Sir, torch on kar di."
            }

        } catch (
            exception: Exception
        ) {

            "Sir, torch on nahi ho saki."
        }
    }

    private fun flashlightOff(): String {

        return try {

            val cameraManager =
                context.getSystemService(
                    Context.CAMERA_SERVICE
                ) as android.hardware.camera2.CameraManager

            val cameraId =
                cameraManager.cameraIdList
                    .firstOrNull()

            if (cameraId == null) {

                "Sir, flashlight available nahi hai."

            } else {

                cameraManager.setTorchMode(
                    cameraId,
                    false
                )

                "Ji Sir, torch off kar di."
            }

        } catch (
            exception: Exception
        ) {

            "Sir, torch off nahi ho saki."
        }
    }

    // =================================================
    // VOLUME
    // =================================================

    private fun isVolumeUpCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "volume up",
                "volume barhao",
                "volume barao",
                "volume increase",
                "volume zyada",
                "volume tez",

                "awaz barhao",
                "awaz barao",
                "awaz badhao",
                "awaz tez karo",

                "sound barhao",
                "sound barao",
                "sound badhao",
                "sound tez karo",

                "loud karo",
                "awaz loud karo"
            )
        )
    }

    private fun isVolumeDownCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "volume down",
                "volume kam",
                "volume kam karo",
                "volume decrease",
                "volume ghatao",

                "awaz kam",
                "awaz kam karo",
                "awaz ghatao",
                "awaz dheemi karo",

                "sound kam",
                "sound kam karo",
                "sound ghatao",
                "sound dheemi karo",

                "quiet karo",
                "awaz quiet karo"
            )
        )
    }

    private fun volumeUp(): String {

        return try {

            val audioManager =
                context.getSystemService(
                    Context.AUDIO_SERVICE
                ) as AudioManager

            audioManager.adjustVolume(
                AudioManager.ADJUST_RAISE,
                AudioManager.FLAG_SHOW_UI
            )

            "Ji Sir, volume barha diya."

        } catch (
            exception: Exception
        ) {

            "Sir, volume barha nahi saka."
        }
    }

    private fun volumeDown(): String {

        return try {

            val audioManager =
                context.getSystemService(
                    Context.AUDIO_SERVICE
                ) as AudioManager

            audioManager.adjustVolume(
                AudioManager.ADJUST_LOWER,
                AudioManager.FLAG_SHOW_UI
            )

            "Ji Sir, volume kam kar diya."

        } catch (
            exception: Exception
        ) {

            "Sir, volume kam nahi kar saka."
        }
    }

    // =================================================
    // SETTINGS
    // =================================================

    private fun isOpenSettingsCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "open settings",
                "settings kholo",
                "settings khol",
                "settings open",
                "settings chalao",

                "phone settings",
                "phone ki settings",

                "setting kholo",
                "setting khol",
                "setting open",

                "settings khol do",
                "setting khol do"
            )
        )
    }

    private fun openSettings(): String {

        return try {

            val intent =
                Intent(
                    Settings.ACTION_SETTINGS
                ).apply {

                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

            context.startActivity(
                intent
            )

            "Ji Sir, settings open kar raha hoon."

        } catch (
            exception: Exception
        ) {

            "Sir, settings open nahi ho sakin."
        }
    }

    // =================================================
    // YOUTUBE
    // =================================================

    private fun isOpenYoutubeCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "open youtube",
                "youtube kholo",
                "youtube khol",
                "youtube open",
                "youtube chalao",
                "youtube chala",
                "youtube start",
                "youtube khol do",

                "youtube kholo na",
                "youtube chala do"
            )
        )
    }

    // =================================================
    // WHATSAPP
    // =================================================

    private fun isOpenWhatsappCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "open whatsapp",
                "whatsapp kholo",
                "whatsapp khol",
                "whatsapp open",
                "whatsapp chalao",
                "whatsapp chala",
                "whatsapp start",
                "whatsapp khol do",

                "whatsapp kholo na",
                "whatsapp chala do"
            )
        )
    }

    // =================================================
    // SPOTIFY
    // =================================================

    private fun isOpenSpotifyCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "open spotify",
                "spotify kholo",
                "spotify khol",
                "spotify open",
                "spotify chalao",
                "spotify chala",
                "spotify start",
                "spotify khol do",

                "spotify kholo na",
                "spotify chala do"
            )
        )
    }

    // =================================================
    // OPEN APP
    // =================================================

    private fun openApp(
        packageName: String,
        appName: String
    ): String {

        return try {

            val intent =
                context.packageManager
                    .getLaunchIntentForPackage(
                        packageName
                    )

            if (intent != null) {

                intent.addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK
                )

                context.startActivity(
                    intent
                )

                "Ji Sir, $appName open kar raha hoon."

            } else {

                "$appName is phone mein installed nahi hai, Sir."
            }

        } catch (
            exception: Exception
        ) {

            "Sir, $appName open nahi ho saka."
        }
    }

    // =================================================
    // GREETING
    // =================================================

    private fun isGreeting(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "hello",
                "hi",
                "hey",

                "salam",
                "salaam",

                "assalamualaikum",
                "assalamu alaikum",
                "assalam o alaikum"
            )
        )
    }

    private fun greetingResponse(): String {

        return "Ji Sir, main yahan hoon."
    }

    // =================================================
    // HELP
    // =================================================

    private fun isHelpCommand(
        command: String
    ): Boolean {

        return containsAny(
            command,
            listOf(

                "help",
                "madad",

                "kya kar sakte ho",
                "tum kya kar sakte ho",
                "aap kya kar sakte ho",

                "kya kya kar sakte ho",

                "commands",
                "command list",

                "kya commands hain",
                "commands batao",

                "tumhare commands"
            )
        )
    }

    private fun helpResponse(): String {

        return """
            Sir, main battery check kar sakta hoon,
            torch on ya off kar sakta hoon,
            volume control kar sakta hoon,
            settings open kar sakta hoon,
            aur YouTube, WhatsApp aur Spotify launch kar sakta hoon.
        """.trimIndent()
    }

    // =================================================
    // UNKNOWN COMMAND
    // =================================================

    private fun unknownCommand(
        originalText: String
    ): String {

        Toast.makeText(
            context,
            "Command: $originalText",
            Toast.LENGTH_SHORT
        ).show()

        return "Sir, mujhe yeh command samajh nahi aayi. Dobara try karein."
    }

    // =================================================
    // HELPER
    // =================================================

    private fun containsAny(
        command: String,
        keywords: List<String>
    ): Boolean {

        return keywords.any { keyword ->

            command.contains(
                keyword,
                ignoreCase = true
            )
        }
    }
}
