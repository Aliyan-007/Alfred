package com.alfred.android.permissions

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat

data class PermissionRequirement(
    val permission: String,
    val displayName: String,
    val description: String,
    val capabilityId: String,
) {
    fun isGranted(context: Context): Boolean =
        ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
}

object AlfredPermissions {
    val ALL: List<PermissionRequirement> = listOf(
        PermissionRequirement(Manifest.permission.POST_NOTIFICATIONS, "Notifications", "Foreground service notification.", "notifications"),
        PermissionRequirement(Manifest.permission.READ_CALENDAR, "Calendar (read)", "Read upcoming events.", "calendar"),
        PermissionRequirement(Manifest.permission.WRITE_CALENDAR, "Calendar (write)", "Create/modify events.", "calendar"),
        PermissionRequirement(Manifest.permission.VIBRATE, "Vibration", "Haptic feedback.", "hardware"),
        PermissionRequirement(Manifest.permission.CAMERA, "Camera", "Flashlight on some devices.", "hardware"),
    )
}
