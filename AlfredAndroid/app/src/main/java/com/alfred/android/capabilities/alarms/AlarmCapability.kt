package com.alfred.android.capabilities.alarms

import android.content.Context
import android.content.Intent
import android.provider.AlarmClock
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull

class AlarmCapability : BaseCapability() {
    override val id = "alarms"
    override val displayName = "Alarms & Timers"
    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult {
        return when (val a = command.action.substringAfter('.', "set_alarm").lowercase()) {
            "set_alarm" -> setAlarm(context, command)
            "set_timer" -> setTimer(context, command)
            "list_alarms", "cancel_alarm", "cancel_timer" -> CommandResult.failure(
                command.id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE,
                "$a is not supported: Android only exposes setting alarms/timers via the clock app", id))
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown: $a", id))
        }
    }

    private fun setAlarm(context: Context, command: Command): CommandResult {
        val hour = command.parameters["hour"]?.jsonPrimitive?.intOrNull
            ?: return fail(command.id, "'hour' (0-23) required")
        val minute = command.parameters["minute"]?.jsonPrimitive?.intOrNull
            ?: return fail(command.id, "'minute' (0-59) required")
        if (hour !in 0..23 || minute !in 0..59) return fail(command.id, "Invalid hour/minute")
        val message = command.parameters["label"]?.jsonPrimitive?.content
        val intent = Intent(AlarmClock.ACTION_SET_ALARM).apply {
            putExtra(AlarmClock.EXTRA_HOUR, hour); putExtra(AlarmClock.EXTRA_MINUTES, minute)
            putExtra(AlarmClock.EXTRA_SKIP_UI, false)
            message?.let { putExtra(AlarmClock.EXTRA_MESSAGE, it) }
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        return try {
            context.startActivity(intent)
            CommandResult.success(command.id, buildJsonObject { put("hour", JsonPrimitive(hour)); put("minute", JsonPrimitive(minute)); put("created", JsonPrimitive(true)) })
        } catch (t: Throwable) { fail(command.id, t.message ?: "Failed") }
    }

    private fun setTimer(context: Context, command: Command): CommandResult {
        val seconds = command.parameters["seconds"]?.jsonPrimitive?.longOrNull
            ?: command.parameters["duration_s"]?.jsonPrimitive?.longOrNull
            ?: return fail(command.id, "'seconds' required")
        if (seconds <= 0) return fail(command.id, "Timer must be > 0")
        val label = command.parameters["label"]?.jsonPrimitive?.content
        val intent = Intent(AlarmClock.ACTION_SET_TIMER).apply {
            putExtra(AlarmClock.EXTRA_LENGTH, seconds.toInt()); putExtra(AlarmClock.EXTRA_SKIP_UI, false)
            label?.let { putExtra(AlarmClock.EXTRA_MESSAGE, it) }
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        return try {
            context.startActivity(intent)
            CommandResult.success(command.id, buildJsonObject { put("seconds", JsonPrimitive(seconds)); put("created", JsonPrimitive(true)) })
        } catch (t: Throwable) { fail(command.id, t.message ?: "Failed") }
    }

    private fun fail(id: String, msg: String) = CommandResult.failure(id, CommandError(ErrorCodes.INVALID_PARAMETERS, msg, id))
}
