package com.alfred.android.ai

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit
import kotlinx.serialization.json.doubleOrNull

class AiCommandParser(
    private val endpoint: String
) {

    private val client =
        OkHttpClient.Builder()
            .connectTimeout(
                15,
                TimeUnit.SECONDS
            )
            .readTimeout(
                30,
                TimeUnit.SECONDS
            )
            .writeTimeout(
                30,
                TimeUnit.SECONDS
            )
            .build()

    private val json =
        Json {
            ignoreUnknownKeys = true
            isLenient = true
            encodeDefaults = true
        }

    suspend fun parse(
        spokenText: String
    ): AiCommandResponse {

        if (spokenText.isBlank()) {

            return AiCommandResponse(
                success = false,
                error = "Empty command"
            )
        }

        return withContext(
            Dispatchers.IO
        ) {

            try {

                val requestJson =
                    buildRequest(
                        spokenText
                    )

                val body =
                    requestJson
                        .toRequestBody(
                            "application/json; charset=utf-8"
                                .toMediaType()
                        )

                val request =
                    Request.Builder()
                        .url(endpoint)
                        .post(body)
                        .header(
                            "Accept",
                            "application/json"
                        )
                        .build()

                client
                    .newCall(request)
                    .execute()
                    .use { response ->

                        if (!response.isSuccessful) {

                            return@withContext AiCommandResponse(
                                success = false,
                                error =
                                    "AI server returned HTTP ${response.code}"
                            )
                        }

                        val responseBody =
                            response.body?.string()

                        if (
                            responseBody.isNullOrBlank()
                        ) {

                            return@withContext AiCommandResponse(
                                success = false,
                                error =
                                    "AI server returned an empty response"
                            )
                        }

                        parseResponse(
                            responseBody
                        )
                    }

            } catch (
                exception: Exception
            ) {

                AiCommandResponse(
                    success = false,
                    error =
                        exception.message
                            ?: "AI request failed"
                )
            }
        }
    }

    private fun buildRequest(
        spokenText: String
    ): String {

        val escaped =
            spokenText
                .replace(
                    "\\",
                    "\\\\"
                )
                .replace(
                    "\"",
                    "\\\""
                )
                .replace(
                    "\n",
                    "\\n"
                )
                .replace(
                    "\r",
                    "\\r"
                )

        return """
            {
              "text": "$escaped",
              "language": "auto",
              "response_format": "alfred_command_v1"
            }
        """.trimIndent()
    }

    private fun parseResponse(
        responseBody: String
    ): AiCommandResponse {

        return try {

            json.decodeFromString(
                AiCommandResponse.serializer(),
                responseBody
            )

        } catch (
            directException: Exception
        ) {

            /*
             * Some backends may return:
             *
             * {
             *   "command": {
             *      ...
             *   }
             * }
             *
             * without wrapping it in AiCommandResponse.
             *
             * Support that format as well.
             */

            try {

                val root =
                    json
                        .parseToJsonElement(
                            responseBody
                        )
                        .jsonObject

                val commandElement =
                    root["command"]

                if (
                    commandElement != null
                ) {

                    val command =
                        json.decodeFromJsonElement(
                            AiCommand.serializer(),
                            commandElement
                        )

                    val confidence =
                        root["confidence"]
                            ?.jsonPrimitive
                            ?.doubleOrNull
                            ?: 1.0

                    AiCommandResponse(
                        success = true,
                        command = command,
                        confidence = confidence
                    )

                } else {

                    AiCommandResponse(
                        success = false,
                        error =
                            "Invalid AI response: ${directException.message}"
                    )
                }

            } catch (
                exception: Exception
            ) {

                AiCommandResponse(
                    success = false,
                    error =
                        "Invalid AI response: ${exception.message}"
                )
            }
        }
    }
}