package com.alfred.android.voice

import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.net.Uri
import android.os.BatteryManager
import android.provider.ContactsContract
import android.provider.Settings
import android.widget.Toast
import com.alfred.android.agent.AlfredAgent
import java.net.URLEncoder

class LocalCommandProcessor(
    private val context: Context,
    private val agent: AlfredAgent
) {

    private val parser =
        CommandParser()

    suspend fun execute(
        spokenText: String
    ): String {

        val intents =
            parser.parse(
                spokenText
            )

        val responses =
            mutableListOf<String>()

        for (intent in intents) {

            val response =
                executeIntent(
                    intent
                )

            responses += response

            if (
                intent is CommandIntent.Unknown
            ) {
                break
            }
        }

        return responses
            .joinToString(" ")
            .ifBlank {
                "Sir, mujhe command samajh nahi aayi."
            }
    }

    // =================================================
    // INTENT EXECUTION
    // =================================================

    private fun executeIntent(
        intent: CommandIntent
    ): String {

        return when (intent) {

            CommandIntent.Battery ->
                getBatteryResponse()

            is CommandIntent.Flashlight -> {

                if (intent.enabled) {
                    flashlightOn()
                } else {
                    flashlightOff()
                }
            }

            is CommandIntent.Volume ->
                changeVolume(
                    intent
                )

            CommandIntent.OpenSettings ->
                openSettings()

            is CommandIntent.OpenApp -> {

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
            }

            is CommandIntent.YouTubeSearch ->
                youtubeSearch(
                    intent.query
                )

            is CommandIntent.WebSearch ->
                webSearch(
                    intent.query
                )

            is CommandIntent.SpotifySearch ->
                spotifySearch(
                    intent.query
                )

            is CommandIntent.Message ->
                sendMessage(
                    intent
                )

            CommandIntent.Greeting ->
                "Ji Sir, main yahan hoon."

            CommandIntent.Help ->
                helpResponse()

            is CommandIntent.Unknown ->
                unknownCommand(
                    intent.originalText
                )
        }
    }

    // =================================================
    // BATTERY
    // =================================================

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

    private fun flashlightOn(): String {

        return try {

            val cameraManager =
                context.getSystemService(
                    Context.CAMERA_SERVICE
                ) as android.hardware.camera2.CameraManager

            val cameraId =
                cameraManager
                    .cameraIdList
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
                cameraManager
                    .cameraIdList
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

            repeat(
                amount.coerceAtMost(15)
            ) {

                when (
                    command.direction
                ) {

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

            if (
                command.amount != null
            ) {

                "Ji Sir, volume ${command.amount} steps adjust kar diya."

            } else if (
                command.direction ==
                CommandIntent.Volume.Direction.UP
            ) {

                "Ji Sir, volume barha diya."

            } else {

                "Ji Sir, volume kam kar diya."
            }

        } catch (
            exception: Exception
        ) {

            "Sir, volume change nahi kar saka."
        }
    }

    // =================================================
    // SETTINGS
    // =================================================

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
    // APP
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
    // CONTACT LOOKUP
    // =================================================

    private fun findContactNumber(
        contactName: String
    ): String? {

        return try {

            val resolver =
                context.contentResolver

            val uri =
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI

            val projection =
                arrayOf(
                    ContactsContract.CommonDataKinds.Phone.NUMBER,
                    ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME
                )

            val selection =
                "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?"

            val selectionArgs =
                arrayOf(
                    "%$contactName%"
                )

            resolver.query(
                uri,
                projection,
                selection,
                selectionArgs,
                null
            )?.use { cursor ->

                if (
                    cursor.moveToFirst()
                ) {

                    val numberIndex =
                        cursor.getColumnIndex(
                            ContactsContract.CommonDataKinds.Phone.NUMBER
                        )

                    if (
                        numberIndex >= 0
                    ) {
                        cursor.getString(
                            numberIndex
                        )
                    } else {
                        null
                    }

                } else {
                    null
                }
            }

        } catch (
            exception: Exception
        ) {

            null
        }
    }

    // =================================================
    // MESSAGE
    // =================================================

    private fun sendMessage(
        command: CommandIntent.Message
    ): String {

        val number =
            findContactNumber(
                command.contactName
            )

        if (
            number.isNullOrBlank()
        ) {

            return "Sir, mujhe ${command.contactName} ka contact nahi mila."
        }

        return when (
            command.channel
        ) {

            CommandIntent.Message.Channel.SMS ->
                openSms(
                    number,
                    command.contactName,
                    command.message
                )

            CommandIntent.Message.Channel.WHATSAPP ->
                openWhatsApp(
                    number,
                    command.contactName,
                    command.message
                )
        }
    }

    // =================================================
    // SMS
    // =================================================

    private fun openSms(
        number: String,
        contactName: String,
        message: String
    ): String {

        return try {

            val uri =
                Uri.parse(
                    "smsto:${Uri.encode(number)}"
                )

            val intent =
                Intent(
                    Intent.ACTION_SENDTO,
                    uri
                ).apply {

                    putExtra(
                        "sms_body",
                        message
                    )

                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

            context.startActivity(
                intent
            )

            "Ji Sir, SMS $contactName ke liye ready kar diya hai."

        } catch (
            exception: Exception
        ) {

            "Sir, SMS open nahi ho saka."
        }
    }

    // =================================================
    // WHATSAPP
    // =================================================

    private fun openWhatsApp(
        number: String,
        contactName: String,
        message: String
    ): String {

        return try {

            val cleanNumber =
                number
                    .replace(
                        Regex("[^0-9+]"),
                        ""
                    )

            val internationalNumber =
                normalizePhoneNumber(
                    cleanNumber
                )

            if (
                internationalNumber.isBlank()
            ) {

                return "Sir, $contactName ka phone number valid nahi hai."
            }

            val encodedMessage =
                URLEncoder.encode(
                    message,
                    "UTF-8"
                )

            val uri =
                Uri.parse(
                    "https://wa.me/$internationalNumber?text=$encodedMessage"
                )

            val intent =
                Intent(
                    Intent.ACTION_VIEW,
                    uri
                ).apply {

                    setPackage(
                        "com.whatsapp"
                    )

                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

            try {

                context.startActivity(
                    intent
                )

                "Ji Sir, WhatsApp message $contactName ke liye ready kar diya hai."

            } catch (
                whatsappException: Exception
            ) {

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

                "Ji Sir, WhatsApp message browser mein ready kar diya hai."
            }

        } catch (
            exception: Exception
        ) {

            "Sir, WhatsApp message open nahi ho saka."
        }
    }

    // =================================================
    // PAKISTAN PHONE NUMBER NORMALIZATION
    // =================================================

    private fun normalizePhoneNumber(
        number: String
    ): String {

        var result =
            number.trim()

        if (
            result.startsWith("+")
        ) {

            return result
                .removePrefix("+")
        }

        if (
            result.startsWith("0092")
        ) {

            return result
                .removePrefix("00")
        }

        if (
            result.startsWith("92")
        ) {

            return result
        }

        if (
            result.startsWith("0")
        ) {

            return "92" +
                result.substring(1)
        }

        return result
    }

    // =================================================
    // YOUTUBE SEARCH
    // =================================================

    private fun youtubeSearch(
        query: String
    ): String {

        if (
            query.isBlank()
        ) {

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

            } catch (
                exception: Exception
            ) {

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

        } catch (
            exception: Exception
        ) {

            "Sir, YouTube search open nahi ho saki."
        }
    }

    // =================================================
    // GOOGLE SEARCH
    // =================================================

    private fun webSearch(
        query: String
    ): String {

        if (
            query.isBlank()
        ) {

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

            context.startActivity(
                intent
            )

            "Ji Sir, Google par $query search kar raha hoon."

        } catch (
            exception: Exception
        ) {

            "Sir, Google search open nahi ho saki."
        }
    }

    // =================================================
    // SPOTIFY SEARCH
    // =================================================

    private fun spotifySearch(
        query: String
    ): String {

        if (
            query.isBlank()
        ) {

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

            val intent =
                Intent(
                    Intent.ACTION_VIEW,
                    uri
                ).apply {

                    setPackage(
                        "com.spotify.music"
                    )

                    addFlags(
                        Intent.FLAG_ACTIVITY_NEW_TASK
                    )
                }

            try {

                context.startActivity(
                    intent
                )

                "Ji Sir, Spotify par $query search kar raha hoon."

            } catch (
                exception: Exception
            ) {

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

        } catch (
            exception: Exception
        ) {

            "Sir, Spotify search open nahi ho saki."
        }
    }

    // =================================================
    // HELP
    // =================================================

    private fun helpResponse(): String {

        return """
            Sir, main battery check, torch control, volume control,
            settings open, YouTube search, Google search,
            Spotify search, WhatsApp messages aur SMS messages
            prepare kar sakta hoon.
        """.trimIndent()
    }

    // =================================================
    // UNKNOWN
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
}