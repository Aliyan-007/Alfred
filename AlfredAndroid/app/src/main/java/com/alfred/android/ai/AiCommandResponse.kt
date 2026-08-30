package com.alfred.android.ai

import kotlinx.serialization.Serializable

@Serializable
data class AiCommandResponse(

    val success: Boolean = false,

    val command: AiCommand? = null,

    val confidence: Double = 0.0,

    val clarification: String? = null,

    val error: String? = null
)