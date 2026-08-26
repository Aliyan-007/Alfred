package com.alfred.android.capabilities.media

import android.content.Context
import android.media.AudioManager
import android.view.KeyEvent
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.capabilities.invalidParametersError
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull

class MediaCapability : BaseCapability() {
    override val id = "media"
    override val displayName = "Media"
    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult {
        val cmd = command.parameters["command"]?.toString()?.trim('"')?.lowercase()
            ?: command.action.substringAfter('.', "").lowercase().takeIf { it.isNotEmpty() }
            ?: return CommandResult.failure(command.id, invalidParametersError("'command' required"))
        val keyCode = when (cmd) {
            "play", "resume" -> KeyEvent.KEYCODE_MEDIA_PLAY
            "pause" -> KeyEvent.KEYCODE_MEDIA_PAUSE
            "play_pause", "toggle" -> KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
            "next", "skip" -> KeyEvent.KEYCODE_MEDIA_NEXT
            "previous", "prev" -> KeyEvent.KEYCODE_MEDIA_PREVIOUS
            "stop" -> KeyEvent.KEYCODE_MEDIA_STOP
            "fast_forward" -> KeyEvent.KEYCODE_MEDIA_FAST_FORWARD
            "rewind" -> KeyEvent.KEYCODE_MEDIA_REWIND
            "seek" -> return CommandResult.failure(command.id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE,
                "Seeking requires MediaSession/notification-listener access (not available to a standard app)", id))
            else -> return CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown media command: $cmd", id))
        }
        val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        return try {
            am.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, keyCode))
            am.dispatchMediaKeyEvent(KeyEvent(KeyEvent.ACTION_UP, keyCode))
            CommandResult.success(command.id, buildJsonObject { put("command", JsonPrimitive(cmd)); put("dispatched", JsonPrimitive(true)) })
        } catch (t: Throwable) {
            CommandResult.failure(command.id, CommandError(ErrorCodes.INTERNAL_ERROR, t.message ?: "dispatch failed", id))
        }
    }
}
