package com.alfred.android.ai

import com.alfred.android.voice.CommandIntent

object AiCommandMapper {

    fun map(
        command: AiCommand,
        originalText: String
    ): CommandIntent {

        return when (
            command.intent
        ) {

            AiCommand.IntentType.BATTERY ->
                CommandIntent.Battery


            AiCommand.IntentType.FLASHLIGHT -> {

                val enabled =
                    command.enabled
                        ?: return CommandIntent.Unknown(
                            originalText
                        )

                CommandIntent.Flashlight(
                    enabled = enabled
                )
            }


            AiCommand.IntentType.VOLUME -> {

                val direction =
                    when (
                        command.direction
                    ) {

                        AiCommand.Direction.UP ->
                            CommandIntent.Volume.Direction.UP

                        AiCommand.Direction.DOWN ->
                            CommandIntent.Volume.Direction.DOWN

                        null ->
                            return CommandIntent.Unknown(
                                originalText
                            )
                    }

                CommandIntent.Volume(
                    direction = direction,
                    amount =
                        command.amount
                            ?.coerceIn(1, 15)
                )
            }


            AiCommand.IntentType.OPEN_SETTINGS ->
                CommandIntent.OpenSettings


            AiCommand.IntentType.OPEN_APP -> {

                val app =
                    when (
                        command.app
                    ) {

                        AiCommand.AppType.YOUTUBE ->
                            CommandIntent.App.YOUTUBE

                        AiCommand.AppType.WHATSAPP ->
                            CommandIntent.App.WHATSAPP

                        AiCommand.AppType.SPOTIFY ->
                            CommandIntent.App.SPOTIFY

                        null ->
                            return CommandIntent.Unknown(
                                originalText
                            )
                    }

                CommandIntent.OpenApp(
                    app
                )
            }


            AiCommand.IntentType.YOUTUBE_SEARCH -> {

                val query =
                    command.query
                        ?.trim()

                if (query.isNullOrBlank()) {

                    CommandIntent.Unknown(
                        originalText
                    )

                } else {

                    CommandIntent.YouTubeSearch(
                        query
                    )
                }
            }


            AiCommand.IntentType.WEB_SEARCH -> {

                val query =
                    command.query
                        ?.trim()

                if (query.isNullOrBlank()) {

                    CommandIntent.Unknown(
                        originalText
                    )

                } else {

                    CommandIntent.WebSearch(
                        query
                    )
                }
            }


            AiCommand.IntentType.SPOTIFY_SEARCH -> {

                val query =
                    command.query
                        ?.trim()

                if (query.isNullOrBlank()) {

                    CommandIntent.Unknown(
                        originalText
                    )

                } else {

                    CommandIntent.SpotifySearch(
                        query
                    )
                }
            }


            AiCommand.IntentType.MESSAGE -> {

                val channel =
                    when (
                        command.channel
                    ) {

                        AiCommand.ChannelType.SMS ->
                            CommandIntent.Message.Channel.SMS

                        AiCommand.ChannelType.WHATSAPP ->
                            CommandIntent.Message.Channel.WHATSAPP

                        null ->
                            return CommandIntent.Unknown(
                                originalText
                            )
                    }

                val contactName =
                    command.contactName
                        ?.trim()

                val message =
                    command.message
                        ?.trim()

                if (
                    contactName.isNullOrBlank() ||
                    message.isNullOrBlank()
                ) {

                    CommandIntent.Unknown(
                        originalText
                    )

                } else {

                    CommandIntent.Message(
                        channel = channel,
                        contactName = contactName,
                        message = message
                    )
                }
            }


            AiCommand.IntentType.GREETING ->
                CommandIntent.Greeting


            AiCommand.IntentType.HELP ->
                CommandIntent.Help


            AiCommand.IntentType.UNKNOWN ->
                CommandIntent.Unknown(
                    originalText
                )
        }
    }
}