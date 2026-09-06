package com.alfred.android.ui.theme

import android.app.Activity
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.SpringSpec
import androidx.compose.animation.core.spring
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.unit.dp
import androidx.core.view.WindowCompat

private val AlfredColors = darkColorScheme(
    primary = AlfredPrimary, onPrimary = AlfredBackground, primaryContainer = AlfredPrimaryDim,
    onPrimaryContainer = AlfredOnSurface, secondary = AlfredSecondary,
    onSecondary = AlfredBackground, secondaryContainer = AlfredSecondaryDim,
    onSecondaryContainer = AlfredOnSurface, tertiary = AlfredTertiary,
    onTertiary = AlfredBackground, tertiaryContainer = AlfredTertiaryDim,
    onTertiaryContainer = AlfredOnSurface,
    background = AlfredBackground, onBackground = AlfredOnSurface,
    surface = AlfredSurface, onSurface = AlfredOnSurface,
    surfaceVariant = AlfredSurfaceVariant, onSurfaceVariant = AlfredOnSurfaceMuted,
    error = AlfredError, onError = AlfredBackground, outline = AlfredBorder,
    inverseSurface = AlfredInverseSurface, inverseOnSurface = AlfredInverseOnSurface,
)

val AlfredShapes = Shapes(
    extraSmall = RoundedCornerShape(8.dp),
    small = RoundedCornerShape(12.dp),
    medium = RoundedCornerShape(20.dp),
    large = RoundedCornerShape(28.dp),
    extraLarge = RoundedCornerShape(36.dp),
)

/** Spring tokens shared by expressive screen transitions and interactions. */
object AlfredMotionScheme {
    val gentle: SpringSpec<Float> = spring(
        dampingRatio = Spring.DampingRatioNoBouncy,
        stiffness = Spring.StiffnessLow,
    )
    val expressive: SpringSpec<Float> = spring(
        dampingRatio = Spring.DampingRatioMediumBouncy,
        stiffness = Spring.StiffnessMediumLow,
    )
    val lively: SpringSpec<Float> = spring(
        dampingRatio = Spring.DampingRatioLowBouncy,
        stiffness = Spring.StiffnessMedium,
    )
}

@Composable
fun AlfredTheme(content: @Composable () -> Unit) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = AlfredColors.background.toArgb()
            window.navigationBarColor = AlfredColors.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }
    MaterialTheme(
        colorScheme = AlfredColors,
        typography = AlfredTypography,
        shapes = AlfredShapes,
        content = content,
    )
}
