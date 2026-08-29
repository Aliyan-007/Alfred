package com.alfred.android.voice

sealed class CommandIntent {

    data object Battery : CommandIntent()

    data class Flashlight(
        val enabled: Boolean
    ) : CommandIntent()

    data class Volume(
        val direction: Direction,
        val amount: Int? = null
    ) : CommandIntent() {

        enum class Direction {
            UP,
            DOWN
        }
    }

    data object OpenSettings : CommandIntent()

    data class OpenApp(
        val app: App
    ) : CommandIntent()

    data class YouTubeSearch(
        val query: String
    ) : CommandIntent()

    data class WebSearch(
        val query: String
    ) : CommandIntent()

    data class SpotifySearch(
        val query: String
    ) : CommandIntent()

    // =================================================
    // MESSAGING
    // =================================================

    data class Message(
        val channel: Channel,
        val contactName: String,
        val message: String
    ) : CommandIntent() {

        enum class Channel {
            SMS,
            WHATSAPP
        }
    }

    data object Greeting : CommandIntent()

    data object Help : CommandIntent()

    data class Unknown(
        val originalText: String
    ) : CommandIntent()

    enum class App {
        YOUTUBE,
        WHATSAPP,
        SPOTIFY
    }
}