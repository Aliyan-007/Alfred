package com.alfred.android.ai

import kotlinx.serialization.Serializable

@Serializable
data class AiCommand(

    val intent: IntentType,

    val direction: Direction? = null,

    val amount: Int? = null,

    val enabled: Boolean? = null,

    val app: AppType? = null,

    val channel: ChannelType? = null,

    val contactName: String? = null,

    val message: String? = null,

    val query: String? = null
) {

    @Serializable
    enum class IntentType {
        BATTERY,
        FLASHLIGHT,
        VOLUME,
        OPEN_SETTINGS,
        OPEN_APP,
        YOUTUBE_SEARCH,
        WEB_SEARCH,
        SPOTIFY_SEARCH,
        MESSAGE,
        GREETING,
        HELP,
        UNKNOWN
    }

    @Serializable
    enum class Direction {
        UP,
        DOWN
    }

    @Serializable
    enum class AppType {
        YOUTUBE,
        WHATSAPP,
        SPOTIFY
    }

    @Serializable
    enum class ChannelType {
        SMS,
        WHATSAPP
    }
}