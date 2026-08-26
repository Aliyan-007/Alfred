package com.alfred.android.capabilities.apps

import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.capabilities.invalidParametersError
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject

class AppCapability : BaseCapability() {
    override val id = "apps"
    override val displayName = "Apps"
    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult = when (
        command.action.substringAfter('.', "open_app")) {
        "open_app", "open" -> openApp(command, context)
        "list_apps", "list" -> listApps(command, context)
        else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown apps action", id))
    }

    private fun openApp(command: Command, context: Context): CommandResult {
        val pkg = command.parameters["package"]?.toString()?.trim('"')
        val name = command.parameters["name"]?.toString()?.trim('"')
        val target = when {
            !pkg.isNullOrBlank() -> pkg
            !name.isNullOrBlank() -> resolvePackageByName(context, name)
            else -> return CommandResult.failure(command.id, invalidParametersError("Provide 'package' or 'name'"))
        } ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "No app matching: ${name ?: pkg}", id))

        val launch = context.packageManager.getLaunchIntentForPackage(target)
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE, "App '$target' has no launchable activity", id))
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return try {
            context.startActivity(launch)
            CommandResult.success(command.id, buildJsonObject { put("package", JsonPrimitive(target)); put("launched", JsonPrimitive(true)) })
        } catch (t: Throwable) {
            CommandResult.failure(command.id, CommandError(ErrorCodes.INTERNAL_ERROR, t.message ?: "Failed to launch", id))
        }
    }

    private fun listApps(command: Command, context: Context): CommandResult {
        val pm = context.packageManager
        val main = Intent(Intent.ACTION_MAIN, null).addCategory(Intent.CATEGORY_LAUNCHER)
        val apps = pm.queryIntentActivities(main, 0).mapNotNull { it.activityInfo.applicationInfo }
            .distinctBy { it.packageName }
            .sortedBy { pm.getApplicationLabel(it).toString().lowercase() }
            .map { ai -> buildJsonObject { put("package", JsonPrimitive(ai.packageName)); put("name", JsonPrimitive(pm.getApplicationLabel(ai).toString())) } }
        return CommandResult.success(command.id, buildJsonObject { put("apps", JsonArray(apps)) })
    }

    private fun resolvePackageByName(context: Context, name: String): String? {
        val pm = context.packageManager
        val lower = name.trim().lowercase()
        val main = Intent(Intent.ACTION_MAIN, null).addCategory(Intent.CATEGORY_LAUNCHER)
        val apps = pm.queryIntentActivities(main, 0).mapNotNull { it.activityInfo.applicationInfo }.distinctBy { it.packageName }
        return apps.firstOrNull { pm.getApplicationLabel(it).toString().lowercase() == lower }?.packageName
            ?: apps.firstOrNull { pm.getApplicationLabel(it).toString().lowercase().contains(lower) }?.packageName
            ?: apps.firstOrNull { it.packageName.lowercase().contains(lower) }?.packageName
    }
}
