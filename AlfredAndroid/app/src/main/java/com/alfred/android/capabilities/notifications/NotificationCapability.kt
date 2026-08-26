package com.alfred.android.capabilities.notifications

import android.content.Context
import android.provider.Settings
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject

class NotificationCapability : BaseCapability() {
    override val id = "notifications"
    override val displayName = "Notifications"

    override fun refresh(context: Context) {
        setState(if (enabled(context)) CapabilityState.AVAILABLE else CapabilityState.PERMISSION_REQUIRED)
    }

    override suspend fun handle(command: Command, context: Context): CommandResult {
        val action = command.action.substringAfter('.', "list").lowercase()
        if (!enabled(context)) return CommandResult.failure(command.id, CommandError(ErrorCodes.PERMISSION_REQUIRED,
            "Notification access not granted", id, mapOf("setting" to Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)))
        return when (action) {
            "list", "recent" -> {
                val arr: JsonArray = buildJsonArray {
                    NotificationState.snapshot().take(10).forEach { e ->
                        add(buildJsonObject {
                            put("package", JsonPrimitive(e.pkg)); put("title", JsonPrimitive(e.title ?: ""))
                            put("text", JsonPrimitive(e.text ?: "")); put("post_time", JsonPrimitive(e.postTime))
                        })
                    }
                }
                CommandResult.success(command.id, buildJsonObject { put("notifications", arr) })
            }
            "clear_all" -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Bulk clear disabled", id))
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown: $action", id))
        }
    }

    private fun enabled(context: Context): Boolean {
        val flat = Settings.Secure.getString(context.contentResolver, "enabled_notification_listeners") ?: return false
        return flat.contains(context.packageName)
    }
}
