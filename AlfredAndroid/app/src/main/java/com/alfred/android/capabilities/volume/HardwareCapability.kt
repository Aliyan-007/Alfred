package com.alfred.android.capabilities.volume

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.camera2.CameraManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
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

class HardwareCapability : BaseCapability() {
    override val id = "hardware"
    override val displayName = "Hardware"
    @Volatile private var torchOn = false

    override fun refresh(context: Context) {
        val hasFlash = context.packageManager.hasSystemFeature(PackageManager.FEATURE_CAMERA_FLASH)
        setState(if (hasFlash) CapabilityState.AVAILABLE else CapabilityState.UNSUPPORTED)
    }

    override suspend fun handle(command: Command, context: Context): CommandResult =
        when (command.action.substringAfter('.', "status").lowercase()) {
            "flashlight_on" -> setTorch(context, true, command.id)
            "flashlight_off" -> setTorch(context, false, command.id)
            "vibrate" -> vibrate(context, command)
            "brightness" -> CommandResult.failure(command.id, CommandError(ErrorCodes.PERMISSION_REQUIRED,
                "Brightness needs WRITE_SETTINGS and is restricted in background. Grant in system settings.", id,
                mapOf("setting" to "android.settings.action.MANAGE_WRITE_SETTINGS")))
            "status" -> CommandResult.success(command.id, buildJsonObject {
                put("flashlight", JsonPrimitive(if (torchOn) "on" else "off"))
                put("flash_supported", JsonPrimitive(context.packageManager.hasSystemFeature(PackageManager.FEATURE_CAMERA_FLASH)))
            })
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown hardware action", id))
        }

    private fun setTorch(context: Context, on: Boolean, id: String): CommandResult {
        val cm = context.getSystemService(Context.CAMERA_SERVICE) as? CameraManager
            ?: return CommandResult.failure(id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE, "No camera service", id))
        val cam = cm.cameraIdList.firstOrNull()
            ?: return CommandResult.failure(id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "No flash camera", id))
        return try {
            cm.setTorchMode(cam, on); torchOn = on
            CommandResult.success(id, buildJsonObject { put("flashlight", JsonPrimitive(if (on) "on" else "off")) })
        } catch (t: Throwable) {
            CommandResult.failure(id, CommandError(ErrorCodes.INTERNAL_ERROR, t.message ?: "torch failed", id))
        }
    }

    @Suppress("DEPRECATION", "MissingPermission")
    private fun vibrate(context: Context, command: Command): CommandResult {
        if (context.checkSelfPermission(Manifest.permission.VIBRATE) != PackageManager.PERMISSION_GRANTED)
            return CommandResult.failure(command.id, CommandError(ErrorCodes.PERMISSION_REQUIRED, "VIBRATE not granted", id,
                mapOf("permission" to Manifest.permission.VIBRATE)))
        val ms = command.parameters["duration_ms"]?.jsonPrimitive?.intOrNull ?: 300
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
            (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
        else context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            vibrator.vibrate(VibrationEffect.createOneShot(ms.toLong().coerceAtMost(5000), VibrationEffect.DEFAULT_AMPLITUDE))
        else vibrator.vibrate(ms.toLong().coerceAtMost(5000))
        return CommandResult.success(command.id, buildJsonObject { put("vibrated_ms", JsonPrimitive(ms)) })
    }
}
