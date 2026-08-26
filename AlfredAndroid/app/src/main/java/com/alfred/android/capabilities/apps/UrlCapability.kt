package com.alfred.android.capabilities.apps

import android.content.Context
import android.content.Intent
import android.net.Uri
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.capabilities.invalidParametersError
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

class UrlCapability : BaseCapability() {
    override val id = "url"
    override val displayName = "Open URL"
    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult {
        val url = command.parameters["url"]?.toString()?.trim('"')
        if (url.isNullOrBlank()) return CommandResult.failure(command.id, invalidParametersError("'url' required"))
        val normalized = normalize(url) ?: return CommandResult.failure(command.id, invalidParametersError("Only http/https allowed"))
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(normalized)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return try {
            context.startActivity(intent)
            CommandResult.success(command.id, buildJsonObject { put("url", JsonPrimitive(normalized)) })
        } catch (t: Throwable) {
            CommandResult.failure(command.id, CommandError(ErrorCodes.INTERNAL_ERROR, t.message ?: "No handler", id))
        }
    }

    private fun normalize(input: String): String? {
        val t = input.trim()
        return when {
            t.startsWith("http://", true) || t.startsWith("https://", true) -> t
            t.matches(Regex("^[\\w.-]+\\.[a-z]{2,}(/.*)?$", RegexOption.IGNORE_CASE)) -> "https://$t"
            else -> null
        }
    }
}
