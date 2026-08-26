package com.alfred.android.util

import android.os.Build

object DeviceInfo {
    val manufacturer: String = Build.MANUFACTURER?.replaceFirstChar { it.uppercase() } ?: "Unknown"
    val model: String = Build.MODEL ?: "Unknown"
    val androidVersion: String = Build.VERSION.RELEASE ?: "Unknown"
    val sdkInt: Int = Build.VERSION.SDK_INT

    fun defaultDisplayName(): String = "$manufacturer $model".trim()
}
