package com.alfred.android.capabilities.volume

import android.content.Context
import android.media.AudioManager
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.capabilities.invalidParametersError
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

class VolumeCapability : BaseCapability() {
    override val id = "volume"
    override val displayName = "Volume"
    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult {
        val action = command.action.substringAfter('.', "status").lowercase()
        val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        return when (action) {
            "up" -> adjust(am, AudioManager.ADJUST_RAISE, command.id)
            "down" -> adjust(am, AudioManager.ADJUST_LOWER, command.id)
            "mute" -> toggleMute(am, true, command.id)
            "unmute" -> toggleMute(am, false, command.id)
            "set" -> setVolume(am, command)
            "status", "" -> status(am, command.id)
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown: $action", id))
        }
    }

    private fun adjust(am: AudioManager, dir: Int, id: String): CommandResult {
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC, dir, 0); return status(am, id)
    }
    private fun toggleMute(am: AudioManager, mute: Boolean, id: String): CommandResult {
        runCatching { am.adjustVolume(if (mute) AudioManager.ADJUST_MUTE else AudioManager.ADJUST_UNMUTE, 0) }
        return CommandResult.success(id, buildJsonObject { put("muted", JsonPrimitive(am.isStreamMute(AudioManager.STREAM_MUSIC))) })
    }
    private fun setVolume(am: AudioManager, command: Command): CommandResult {
        val v = command.parameters["value"]?.toString()?.trim('"')?.toIntOrNull()
            ?: return CommandResult.failure(command.id, invalidParametersError("'value' 0-100 required"))
        val max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
        am.setStreamVolume(AudioManager.STREAM_MUSIC, (v.coerceIn(0, 100) * max / 100), 0)
        return status(am, command.id)
    }
    private fun status(am: AudioManager, id: String): CommandResult {
        val cur = am.getStreamVolume(AudioManager.STREAM_MUSIC)
        val max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
        return CommandResult.success(id, buildJsonObject {
            put("current", JsonPrimitive(cur)); put("max", JsonPrimitive(max))
            put("percentage", JsonPrimitive(if (max > 0) cur * 100 / max else 0))
            put("muted", JsonPrimitive(am.isStreamMute(AudioManager.STREAM_MUSIC)))
        })
    }
}
