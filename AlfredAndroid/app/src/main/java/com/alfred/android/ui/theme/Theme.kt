package com.alfred.android.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val Colors = darkColorScheme(
    primary = AlfredPrimary, onPrimary = AlfredBackground, primaryContainer = AlfredPrimaryDim,
    onPrimaryContainer = AlfredOnSurface, secondary = AlfredSecondary,
    background = AlfredBackground, onBackground = AlfredOnSurface,
    surface = AlfredSurface, onSurface = AlfredOnSurface,
    surfaceVariant = AlfredSurfaceVariant, onSurfaceVariant = AlfredOnSurfaceMuted,
    error = AlfredError, onError = AlfredBackground, outline = AlfredBorder,
)

@Composable
fun AlfredTheme(content: @Composable () -> Unit) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = Colors.background.toArgb()
            window.navigationBarColor = Colors.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }
    MaterialTheme(colorScheme = Colors, typography = AlfredTypography, content = content)
}
