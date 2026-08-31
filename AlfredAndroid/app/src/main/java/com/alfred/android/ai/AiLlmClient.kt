package com.alfred.android.ai

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class AiLlmClient {

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

    suspend fun understandCommand(
        spokenText: String,
        apiKey: String
    ): AiCommand? {

        if (
            spokenText.isBlank() ||
            apiKey.isBlank()
        ) {
            return null
        }

        return withContext(Dispatchers.IO) {

            try {

                val requestBody =
                    """
                    {
                      "model": "llama-3.1-8b-instant",
                      "messages": [
                        {
                          "role": "system",
                          "content": "${buildSystemPrompt()}"
                        },
                        {
                          "role": "user",
                          "content": ${json.encodeToString(
                              kotlinx.serialization.serializer<String>(),
                              spokenText
                          )}
                        }
                      ],
                      "temperature": 0,
                      "response_format": {
                        "type": "json_object"
                      }
                    }
                    """.trimIndent()

                val request =
                    Request.Builder()
                        .url("https://api.groq.com/openai/v1/chat/completions")
                        .addHeader(
                            "Authorization",
                            "Bearer $apiKey"
                        )
                        .addHeader(
                            "Content-Type",
                            "application/json"
                        )
                        .post(
                            requestBody
                                .toRequestBody(
                                    "application/json".toMediaType()
                                )
                        )
                        .build()

                client
                    .newCall(request)
                    .execute()
                    .use { response ->

                        if (!response.isSuccessful) {
                            return@withContext null
                        }

                        val body =
                            response.body?.string()
                                ?: return@withContext null

                        val completion =
                            json.decodeFromString<GroqResponse>(
                                body
                            )

                        val content =
                            completion
                                .choices
                                .firstOrNull()
                                ?.message
                                ?.content
                                ?: return@withContext null

                        json.decodeFromString<AiCommand>(
                            content.trim()
                        )
                    }

            } catch (
                exception: Exception
            ) {

                null
            }
        }
    }

    private fun buildSystemPrompt(): String {

        return """
            You are Alfred, a voice command understanding engine.

            Your job is NOT to answer the user.

            Your job is to understand the user's spoken command
            and convert it into exactly one AiCommand JSON object.

            The user may speak:

            - English
            - Urdu
            - Roman Urdu
            - Urdu-English mixed language
            - Pakistani English
            - different accents
            - imperfect speech recognition
            - slang
            - shortened words
            - phonetic spellings
            - words such as:
              badhao
              barao
              barhao
              barha do
              tez karo
              kam karo
              ghatao
              bhejo
              send karo
              karo
              kar do
              kholo
              khol do
              chalao
              chala do

            Understand the intended meaning instead of requiring
            exact phrases.

            Available intents:

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

            Direction values:

            UP
            DOWN

            App values:

            YOUTUBE
            WHATSAPP
            SPOTIFY

            Channel values:

            SMS
            WHATSAPP

            Return ONLY valid JSON.

            Never return markdown.

            Never explain your reasoning.

            Never add extra fields.

            For volume:

            "volume badhao"
            "volume barao"
            "awaz badhao"
            "awaz barhao"
            "awaz tez karo"
            "sound loud karo"

            should become:

            {
              "intent": "VOLUME",
              "direction": "UP"
            }

            For volume down:

            {
              "intent": "VOLUME",
              "direction": "DOWN"
            }

            If a number is explicitly given,
            put it into amount.

            Example:

            "volume 5 steps badhao"

            becomes:

            {
              "intent": "VOLUME",
              "direction": "UP",
              "amount": 5
            }

            For messages, identify:

            1. channel
            2. contact name
            3. message text

            Example:

            "Ali ko WhatsApp pe keh do kal meeting hai"

            becomes:

            {
              "intent": "MESSAGE",
              "channel": "WHATSAPP",
              "contactName": "Ali",
              "message": "kal meeting hai"
            }

            Example:

            "Sara ko SMS karo main ghar aa raha hoon"

            becomes:

            {
              "intent": "MESSAGE",
              "channel": "SMS",
              "contactName": "Sara",
              "message": "main ghar aa raha hoon"
            }

            Preserve the person's name exactly as understood.

            Do not put the contact name inside message.

            For searches, put only the search query in query.

            If the command cannot reasonably be understood,
            use:

            {
              "intent": "UNKNOWN"
            }

            Optional fields must be omitted or null when
            they are not needed.

            The output must always be a single AiCommand JSON object.
        """.trimIndent()
    }
}

@Serializable
private data class GroqResponse(
    val choices: List<GroqChoice> = emptyList()
)

@Serializable
private data class GroqChoice(
    val message: GroqMessage
)

@Serializable
private data class GroqMessage(
    val content: String
)