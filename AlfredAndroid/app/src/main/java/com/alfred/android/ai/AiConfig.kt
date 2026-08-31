package com.alfred.android.ai

import com.alfred.android.BuildConfig

object AIConfig {

    val groqApiKey: String
        get() = BuildConfig.GROQ_API_KEY

    const val MODEL = "llama-3.1-8b-instant"

    const val BASE_URL = "https://api.groq.com/openai/v1/"
}