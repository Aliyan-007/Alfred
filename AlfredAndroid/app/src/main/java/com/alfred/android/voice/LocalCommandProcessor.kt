package com.alfred.android.voice

import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.net.Uri
import android.os.BatteryManager
import android.provider.Settings
import android.widget.Toast
import com.alfred.android.agent.AlfredAgent
import java.net.URLEncoder

class LocalCommandProcessor(
    private val context: Context,
    private val agent: AlfredAgent
) {

    private val parser = CommandParser()

    suspend fun execute(
        spokenText: String
    ): String {

        val intents = parser.parse(spokenText)

        val responses = mutableListOf<String>()

        for (intent in intents) {

            val response = executeIntent(intent)

            responses += response

            // Stop executing after an unknown command.
            if (intent is CommandIntent.Unknown) {
                break
            }
        }

        return responses.joinToString(" ")
            .ifBlank {
                "Sir, mujhe command samajh nahi aayi."
            }
    }

    private fun executeIntent(
        intent: CommandIntent
    ): String {

        return when (intent) {

            CommandIntent.Battery ->
                getBatteryResponse()

            is CommandIntent.Flashlight ->
                if (intent.enabled) {
                    flashlightOn()
                } else {
                    flashlightOff()
                }

            is CommandIntent.Volume ->
                changeVolume(intent)

            CommandIntent.OpenSettings ->
                openSettings()

            is CommandIntent.OpenApp ->
                when (intent.app) {
                    CommandIntent.App.YOUTUBE ->
                        openApp(
                            "com.google.android.youtube",
                            "YouTube"
                        )

                    CommandIntent.App.WHATSAPP ->
                        openApp(
                            "com.whatsapp",
                            "WhatsApp"
                        )

                    CommandIntent.App.SPOTIFY ->
                        openApp(
                            "com.spotify.music",
                            "Spotify"
                        )
                }

            is CommandIntent.YouTubeSearch ->
                youtubeSearch(intent.query)

            is CommandIntent.WebSearch ->
                webSearch(intent.query)

            is CommandIntent.SpotifySearch ->
                spotifySearch(intent.query)

            is CommandIntent.WhatsAppShare ->
                whatsappShare(intent.message)

            CommandIntent.Greeting ->
                "Ji Sir, main yahan hoon."

            CommandIntent.Help ->
                helpResponse()

            is CommandIntent.Unknown ->
                unknownCommand(intent.originalText)
        }
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

    private fun flashlightOn(): String {

        return try {

            val cameraManager =
                context.getSystemService(
                    Context.CAMERA_SERVICE
                ) as android.hardware.camera2.CameraManager

            val cameraId =
                cameraManager.cameraIdList.firstOrNull()

            if (cameraId == null) {
                "Sir, flashlight available nahi hai."
            } else {

                cameraManager.setTorchMode(
                    cameraId,
                    true
                )

                "Ji Sir, torch on kar di."
            }

        } catch (exception: Exception) {
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
                cameraManager.cameraIdList.firstOrNull()

            if (cameraId == null) {
                "Sir, flashlight available nahi hai."
            } else {

                cameraManager.setTorchMode(
                    cameraId,
                    false
                )

                "Ji Sir, torch off kar di."
            }

        } catch (exception: Exception) {
            "Sir, torch off nahi ho saki."
        }
    }

    private fun changeVolume(
        command: CommandIntent.Volume
    ): String {

        return try {

            val audioManager =
                context.getSystemService(
                    Context.AUDIO_SERVICE
                ) as AudioManager

            val amount =
                command.amount ?: 1

            repeat(amount.coerceAtMost(15)) {

                when (command.direction) {

                    CommandIntent.Volume.Direction.UP ->
                        audioManager.adjustVolume(
                            AudioManager.ADJUST_RAISE,
                            AudioManager.FLAG_SHOW_UI
                        )

                    CommandIntent.Volume.Direction.DOWN ->
                        audioManager.adjustVolume(
                            AudioManager.ADJUST_LOWER,
                            AudioManager.FLAG_SHOW_UI
                        )
                }
            }

            if (command.amount != null) {
                "Ji Sir, volume ${command.amount} steps adjust kar diya."
            } else if (
                command.direction ==
                CommandIntent.Volume.Direction.UP
            ) {
                "Ji Sir, volume barha diya."
            } else {
                "Ji Sir, volume kam kar diya."
            }

        } catch (exception: Exception) {
            "Sir, volume change nahi kar saka."
        }
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

            context.startActivity(intent)

            "Ji Sir, settings open kar raha hoon."

        } catch (exception: Exception) {
            "Sir, settings open nahi ho sakin."
        }
    }

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

                context.startActivity(intent)

                "Ji Sir, $appName open kar raha hoon."

            } else {
                "$appName is phone mein installed nahi hai, Sir."
            }

        } catch (exception: Exception) {
            "Sir, $appName open nahi ho saka."
        }
    }

    private fun youtubeSearch(
        query: String
    ): String {

        if (query.isBlank()) {
            return "Sir, YouTube par kya search karna hai?"
        }

        return try {

            val encoded =
                URLEncoder.encode(
                    query,
                    "UTF-8"
                )

            val uri =
                Uri.parse(
                    "https://www.youtube.com/results?search_query=$encoded"
                )

            val youtubeIntent =
                Intent(
                    Intent.ACTION_VIEW,
                    uri
                ).apply {
                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                    setPackage(
                        "com.google.android.youtube"
                    )
                }

            try {

                context.startActivity(
                    youtubeIntent
                )

                "Ji Sir, YouTube par $query search kar raha hoon."

            } catch (youtubeException: Exception) {

                val browserIntent =
                    Intent(
                        Intent.ACTION_VIEW,
                        uri
                    ).apply {
                        addFlags(
                            Intent.FLAG_ACTIVITY_NEW_TASK
                        )
                    }

                context.startActivity(
                    browserIntent
                )

                "Ji Sir, browser mein YouTube par $query search kar raha hoon."
            }

        } catch (exception: Exception) {
            "Sir, YouTube search open nahi ho saki."
        }
    }

    private fun webSearch(
        query: String
    ): String {

        if (query.isBlank()) {
            return "Sir, kya search karna hai?"
        }

        return try {

            val encoded =
                URLEncoder.encode(
                    query,
                    "UTF-8"
                )

            val uri =
                Uri.parse(
                    "https://www.google.com/search?q=$encoded"
                )

            val intent =
                Intent(
                    Intent.ACTION_VIEW,
                    uri
                ).apply {
                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

            context.startActivity(intent)

            "Ji Sir, Google par $query search kar raha hoon."

        } catch (exception: Exception) {
            "Sir, Google search open nahi ho saki."
        }
    }

    private fun spotifySearch(
        query: String
    ): String {

        if (query.isBlank()) {
            return "Sir, Spotify par kya search karna hai?"
        }

        return try {

            val encoded =
                URLEncoder.encode(
                    query,
                    "UTF-8"
                )

            val uri =
                Uri.parse(
                    "https://open.spotify.com/search/$encoded"
                )

            val spotifyIntent =
                Intent(
                    Intent.ACTION_VIEW,
                    uri
                ).apply {
                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                    setPackage(
                        "com.spotify.music"
                    )
                }

            try {

                context.startActivity(
                    spotifyIntent
                )

                "Ji Sir, Spotify par $query search kar raha hoon."

            } catch (spotifyException: Exception) {

                val browserIntent =
                    Intent(
                        Intent.ACTION_VIEW,
                        uri
                    ).apply {
                        addFlags(
                            Intent.FLAG_ACTIVITY_NEW_TASK
                        )
                    }

                context.startActivity(
                    browserIntent
                )

                "Ji Sir, browser mein Spotify search open kar raha hoon."
            }

        } catch (exception: Exception) {
            "Sir, Spotify search open nahi ho saki."
        }
    }

    private fun whatsappShare(
        message: String
    ): String {

        if (message.isBlank()) {
            return "Sir, WhatsApp par kya message bhejna hai?"
        }

        return try {

            val intent =
                Intent(
                    Intent.ACTION_SEND
                ).apply {

                    type = "text/plain"

                    putExtra(
                        Intent.EXTRA_TEXT,
                        message
                    )

                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

            val chooser =
                Intent.createChooser(
                    intent,
                    "Send with WhatsApp"
                ).apply {
                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

            context.startActivity(chooser)

            "Ji Sir, WhatsApp message ready kar diya."

        } catch (exception: Exception) {
            "Sir, WhatsApp message open nahi ho saka."
        }
    }

    private fun helpResponse(): String {

        return "Sir, main battery check, torch control, volume control, settings open, YouTube search, Google search, Spotify search, WhatsApp message sharing, aur YouTube, WhatsApp aur Spotify launch kar sakta hoon."
    }

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
}
