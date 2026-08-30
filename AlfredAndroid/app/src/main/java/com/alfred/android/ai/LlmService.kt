package com.alfred.android.ai

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

class LlmService(
    private val apiKey: String,
    private val model: String
) {

    private val client =
        OkHttpClient.Builder()
            .connectTimeout(20, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(20, TimeUnit.SECONDS)
            .build()

    private val json =
        Json {
            ignoreUnknownKeys = true
            isLenient = true
        }

    private val mediaType =
        "application/json; charset=utf-8".toMediaType()

    suspend fun understand(
        spokenText: String
    ): AiCommand? {

        if (apiKey.isBlank()) {
            return null
        }

        if (spokenText.isBlank()) {
            return null
        }

        val systemPrompt = """
            You are Alfred, a voice command understanding engine.

            Your ONLY job is to understand the user's spoken command
            and convert it into the exact JSON structure requested below.

            Do NOT answer the user.
            Do NOT explain anything.
            Do NOT add markdown.
            Do NOT add code fences.
            Return ONLY valid JSON.

            The user may speak:
            - English
            - Roman Urdu
            - Urdu-English mixed speech
            - Hindi/Urdu mixed speech
            - informal speech
            - Pakistani English
            - different accents
            - imperfect speech recognition transcripts
            - phonetic spellings
            - casual words such as:
              karo, kar do, kardo, krdo, kholo, khol do,
              bhejo, send karo, badhao, barhao, barao,
              kam karo, ghatao, jalao, chalao, dhundo,
              batao, btao, zara, please, bhai, yaar, etc.

            Understand the MEANING, not exact wording.

            Supported intents:

            BATTERY
            FLASHLIGHT
            VOLUME
            OPEN_SETTINGS
            OPEN_APP
            YOUTUBE_SEARCH
            WEB_SEARCH
            SPOTIFY_SEARCH
            MESSAGE
            GREETING
            HELP
            UNKNOWN

            For VOLUME:
            direction must be UP or DOWN.
            amount should be a number from 1 to 15 if explicitly requested.
            Otherwise amount must be null.

            Examples:
            "awaz badhao"
            -> VOLUME UP

            "awaaz barha do"
            -> VOLUME UP

            "sound thora loud karo"
            -> VOLUME UP

            "volume 5 steps kam karo"
            -> VOLUME DOWN amount 5

            "awaz zara kam"
            -> VOLUME DOWN

            For FLASHLIGHT:
            enabled=true means ON.
            enabled=false means OFF.

            Examples:
            "torch jalao"
            -> FLASHLIGHT enabled=true

            "light band kar do"
            -> FLASHLIGHT enabled=false

            For OPEN_APP:
            supported apps are:
            YOUTUBE
            WHATSAPP
            SPOTIFY

            For MESSAGE:
            channel must be SMS or WHATSAPP.
            Extract the person's name separately from the message.
            Do not include words like "ko", "par", "pe", "bhai",
            "please", "zara", "message", "bhejo", "send" in contactName.

            Examples:

            "Ali ko WhatsApp par message karo kal aa raha hoon"

            -> MESSAGE
            -> channel WHATSAPP
            -> contactName Ali
            -> message kal aa raha hoon

            "Ali ko WhatsApp pe keh do ke main ghar aa raha hoon"

            -> MESSAGE
            -> channel WHATSAPP
            -> contactName Ali
            -> message main ghar aa raha hoon

            "Ali ko SMS kar do main late ho jaunga"

            -> MESSAGE
            -> channel SMS
            -> contactName Ali
            -> message main late ho jaunga

            If the contact name or message is missing,
            return UNKNOWN instead of guessing.

            For searches:
            Put only the actual search query in query.

            Example:
            "youtube pe spider man search karo"
            -> YOUTUBE_SEARCH
            -> query "spider man"

            "google pe weather in Islamabad search karo"
            -> WEB_SEARCH
            -> query "weather in Islamabad"

            "spotify pe Atif Aslam search karo"
            -> SPOTIFY_SEARCH
            -> query "Atif Aslam"

            For GREETING:
            examples include:
            hello
            hi
            hey
            salam
            assalamualaikum

            For HELP:
            examples include:
            help
            madad
            tum kya kar sakte ho
            commands batao

            If the command cannot confidently be mapped to one
            of the supported intents, return UNKNOWN.

            JSON schema:

            {
              "intent": "BATTERY | FLASHLIGHT | VOLUME | OPEN_SETTINGS | OPEN_APP | YOUTUBE_SEARCH | WEB_SEARCH | SPOTIFY_SEARCH | MESSAGE | GREETING | HELP | UNKNOWN",
              "direction": "UP | DOWN | null",
              "amount": "number | null",
              "enabled": "boolean | null",
              "app": "YOUTUBE | WHATSAPP | SPOTIFY | null",
              "channel": "SMS | WHATSAPP | null",
              "contactName": "string | null",
              "message": "string | null",
              "query": "string | null"
            }
        """.trimIndent()

        val requestPayload =
            ChatCompletionRequest(
                model = model,
                messages = listOf(
                    ChatMessage(
                        role = "system",
                        content = systemPrompt
                    ),
                    ChatMessage(
                        role = "user",
                        content = spokenText
                    )
                ),
                temperature = 0.0,
                maxTokens = 300
            )

        val requestJson =
            json.encodeToString(
                ChatCompletionRequest.serializer(),
                requestPayload
            )

        val request =
            Request.Builder()
                .url(
                    "https://api.groq.com/openai/v1/chat/completions"
                )
                .addHeader(
                    "Authorization",
                    "Bearer $apiKey"
                )
                .addHeader(
                    "Content-Type",
                    "application/json"
                )
                .post(
                    requestJson.toRequestBody(
                        mediaType
                    )
                )
                .build()

        return try {

            val response =
                client
                    .newCall(request)
                    .execute()

            response.use {

                if (!it.isSuccessful) {
                    return null
                }

                val responseBody =
                    it.body?.string()
                        ?: return null

                val completion =
                    json.decodeFromString(
                        ChatCompletionResponse.serializer(),
                        responseBody
                    )

                val content =
                    completion
                        .choices
                        .firstOrNull()
                        ?.message
                        ?.content
                        ?.trim()
                        ?: return null

                parseAiCommand(
                    content
                )
            }

        } catch (
            exception: IOException
        ) {

            null

        } catch (
            exception: Exception
        ) {

            null
        }
    }

    private fun parseAiCommand(
        content: String
    ): AiCommand? {

        val cleaned =
            content
                .trim()
                .removePrefix("```json")
                .removePrefix("```")
                .removeSuffix("```")
                .trim()

        return runCatching {

            json.decodeFromString(
                AiCommand.serializer(),
                cleaned
            )

        }.getOrNull()
    }
}


@Serializable
private data class ChatCompletionRequest(

    val model: String,

    val messages: List<ChatMessage>,

    val temperature: Double,

    @kotlinx.serialization.SerialName("max_tokens")
    val maxTokens: Int
)


@Serializable
private data class ChatMessage(

    val role: String,

    val content: String
)


@Serializable
private data class ChatCompletionResponse(

    val choices: List<ChatChoice> = emptyList()
)


@Serializable
private data class ChatChoice(

    val message: ChatMessage
)