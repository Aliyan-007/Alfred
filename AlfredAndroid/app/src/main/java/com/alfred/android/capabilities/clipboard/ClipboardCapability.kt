package com.alfred.android.capabilities.clipboard

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

class ClipboardCapability : BaseCapability() {
    override val id = "clipboard"
    override val displayName = "Clipboard"
    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult {
        val action = command.action.substringAfter('.', "get").lowercase()
        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        return when (action) {
            "set", "copy" -> {
                val text = command.parameters["text"]?.toString()?.trim('"')
                    ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'text' required", id))
                cm.setPrimaryClip(ClipData.newPlainText("ALFRED", text))
                CommandResult.success(command.id, buildJsonObject { put("copied", JsonPrimitive(true)); put("length", JsonPrimitive(text.length)) })
            }
            "get", "paste" -> {
                if (!cm.hasPrimaryClip()) return CommandResult.success(command.id, buildJsonObject { put("text", JsonPrimitive("")); put("empty", JsonPrimitive(true)) })
                val text = cm.primaryClip?.getItemAt(0)?.coerceToText(null)?.toString()
                    ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE,
                        "Clipboard read blocked in background on Android 10+. Open the app and retry.", id))
                CommandResult.success(command.id, buildJsonObject { put("text", JsonPrimitive(text)); put("length", JsonPrimitive(text.length)) })
            }
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown: $action", id))
        }
    }
}
