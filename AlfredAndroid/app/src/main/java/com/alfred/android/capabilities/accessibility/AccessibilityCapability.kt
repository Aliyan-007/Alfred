package com.alfred.android.capabilities.accessibility

import android.content.Context
import android.provider.Settings
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.floatOrNull
import kotlinx.serialization.json.jsonPrimitive

class AccessibilityCapability : BaseCapability() {
    override val id = "accessibility"
    override val displayName = "Accessibility"

    override fun refresh(context: Context) {
        setState(if (isEnabled(context) && AccessibilityState.connected) CapabilityState.AVAILABLE else CapabilityState.PERMISSION_REQUIRED)
    }

    override suspend fun handle(command: Command, context: Context): CommandResult {
        if (!isEnabled(context) || !AccessibilityState.connected)
            return CommandResult.failure(command.id, CommandError(ErrorCodes.PERMISSION_REQUIRED,
                "Accessibility service not enabled", id, mapOf("setting" to Settings.ACTION_ACCESSIBILITY_SETTINGS)))
        val svc = AlfredAccessibilityService.instance
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE, "Service not running", id))
        val action = command.action.substringAfter('.', "status").lowercase()
        return when (action) {
            "back" -> result(command.id, "back", svc.doBack())
            "home" -> result(command.id, "home", svc.doHome())
            "recents" -> result(command.id, "recents", svc.doRecents())
            "tap" -> {
                val x = command.parameters["x"]?.jsonPrimitive?.floatOrNull ?: return bad(command.id, "x required")
                val y = command.parameters["y"]?.jsonPrimitive?.floatOrNull ?: return bad(command.id, "y required")
                result(command.id, "tap", svc.tap(x, y))
            }
            "swipe" -> {
                val x1 = command.parameters["x1"]?.jsonPrimitive?.floatOrNull ?: return bad(command.id, "x1 required")
                val y1 = command.parameters["y1"]?.jsonPrimitive?.floatOrNull ?: return bad(command.id, "y1 required")
                val x2 = command.parameters["x2"]?.jsonPrimitive?.floatOrNull ?: return bad(command.id, "x2 required")
                val y2 = command.parameters["y2"]?.jsonPrimitive?.floatOrNull ?: return bad(command.id, "y2 required")
                result(command.id, "swipe", svc.swipe(x1, y1, x2, y2))
            }
            "click_text" -> {
                val text = command.parameters["text"]?.jsonPrimitive?.content ?: return bad(command.id, "text required")
                result(command.id, "click_text", svc.clickByText(text))
            }
            "status" -> CommandResult.success(command.id, buildJsonObject { put("enabled", JsonPrimitive(true)) })
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown: $action", id))
        }
    }

    private fun result(id: String, a: String, ok: Boolean) = CommandResult.success(
        id, buildJsonObject { put("action", JsonPrimitive(a)); put("performed", JsonPrimitive(ok)) })
    private fun bad(id: String, m: String) = CommandResult.failure(id, CommandError(ErrorCodes.INVALID_PARAMETERS, m, id))

    private fun isEnabled(context: Context): Boolean {
        val expected = context.packageName + "/" + AlfredAccessibilityService::class.java.name
        val enabled = Settings.Secure.getString(context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: return false
        return enabled.contains(expected)
    }
}
