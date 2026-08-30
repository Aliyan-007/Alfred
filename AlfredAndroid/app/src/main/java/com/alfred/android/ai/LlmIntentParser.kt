package com.alfred.android.ai

class LlmIntentParser(
    private val llmService: LlmService
) {

    suspend fun parse(
        spokenText: String
    ): AiCommand? {

        if (spokenText.isBlank()) {
            return null
        }

        return llmService.understand(
            spokenText
        )
    }
}