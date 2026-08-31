package com.alfred.android.ai

import com.alfred.android.BuildConfig
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class AiService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }

    suspend fun parseCommand(text: String): AiCommand {

        if (text.isBlank()) {
            return unknownCommand()
        }

        val apiKey = BuildConfig.GROQ_API_KEY

        if (apiKey.isBlank()) {
            throw IllegalStateException(
                "GROQ_API_KEY is not configured"
            )
        }

        val requestJson = """
            {
              "model": "openai/gpt-oss-20b",
              "messages": [
                {
                  "role": "system",
                  "content": ${quote(AiPrompt.SYSTEM_PROMPT)}
                },
                {
                  "role": "user",
                  "content": ${quote(text)}
                }
              ],
              "temperature": 0,
              "max_tokens": 300
            }
        """.trimIndent()

        val body = requestJson
            .toRequestBody(
                "application/json".toMediaType()
            )

        val request = Request.Builder()
            .url("https://api.groq.com/openai/v1/chat/completions")
            .addHeader(
                "Authorization",
                "Bearer $apiKey"
            )
            .addHeader(
                "Content-Type",
                "application/json"
            )
            .post(body)
            .build()

        client.newCall(request).execute().use { response ->

            val responseBody = response.body?.string().orEmpty()

            if (!response.isSuccessful) {
                throw IllegalStateException(
                    "Groq request failed: " +
                        "${response.code} $responseBody"
                )
            }

            if (responseBody.isBlank()) {
                throw IllegalStateException(
                    "Groq returned an empty response"
                )
            }

            return parseGroqResponse(responseBody)
        }
    }

    private fun parseGroqResponse(
        responseBody: String
    ): AiCommand {

        val root = json.parseToJsonElement(responseBody)
            .jsonObject

        val choices = root["choices"]
            ?.jsonArray
            ?: throw IllegalStateException(
                "Groq response does not contain choices"
            )

        if (choices.isEmpty()) {
            throw IllegalStateException(
                "Groq returned no choices"
            )
        }

        val firstChoice = choices[0].jsonObject

        val message = firstChoice["message"]
            ?.jsonObject
            ?: throw IllegalStateException(
                "Groq response does not contain message"
            )

        val content = message["content"]
            ?.toString()
            ?.trim('"')
            ?.trim()
            ?: throw IllegalStateException(
                "Groq response does not contain content"
            )

        val cleanedJson = cleanJson(content)

        return json.decodeFromString<AiCommand>(
            cleanedJson
        )
    }

    private fun cleanJson(text: String): String {

        var result = text.trim()

        if (result.startsWith("```")) {
            result = result
                .removePrefix("```json")
                .removePrefix("```JSON")
                .removePrefix("```")
                .trim()

            if (result.endsWith("```")) {
                result = result
                    .removeSuffix("```")
                    .trim()
            }
        }

        val start = result.indexOf('{')
        val end = result.lastIndexOf('}')

        if (start >= 0 && end > start) {
            result = result.substring(
                start,
                end + 1
            )
        }

        return result
    }

    private fun quote(value: String): String {
        return buildString {
            append('"')

            value.forEach { char ->
                when (char) {
                    '\\' -> append("\\\\")
                    '"' -> append("\\\"")
                    '\n' -> append("\\n")
                    '\r' -> append("\\r")
                    '\t' -> append("\\t")
                    else -> append(char)
                }
            }

            append('"')
        }
    }

    private fun unknownCommand(): AiCommand {
        return AiCommand(
            intent = AiCommand.IntentType.UNKNOWN
        )
    }
}