package com.alfred.android.ui.components

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.togetherWith
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.alfred.android.ui.theme.AlfredError
import com.alfred.android.ui.theme.AlfredPrimary
import com.alfred.android.ui.theme.AlfredSecondary
import com.alfred.android.ui.theme.AlfredSurfaceVariant
import com.alfred.android.ui.theme.AlfredWarning

enum class StatusLevel { OK, NEUTRAL, WARNING, ERROR, OFF }

@Composable
fun StatusPill(text: String, status: StatusLevel, modifier: Modifier = Modifier) {
    val targetColor = when (status) {
        StatusLevel.OK -> AlfredPrimary; StatusLevel.NEUTRAL -> AlfredSecondary
        StatusLevel.WARNING -> AlfredWarning; StatusLevel.ERROR -> AlfredError
        StatusLevel.OFF -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    // Smoothly morph the dot color instead of hard-cutting between states.
    val color by animateColorAsState(targetColor, animationSpec = tween(350), label = "statusColor")

    // Pulse the dot while the connection is in a transitional state, so
    // "Connecting…" / "Reconnecting…" reads as active rather than stuck.
    val isTransitional = status == StatusLevel.NEUTRAL || status == StatusLevel.WARNING
    val infiniteTransition = rememberInfiniteTransition(label = "statusPulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = if (isTransitional) 0.35f else 1f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(700),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "statusPulseAlpha",
    )
    val dotAlpha = if (isTransitional) pulseAlpha else 1f

    Row(
        modifier = modifier.clip(RoundedCornerShape(50)).background(AlfredSurfaceVariant)
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(Modifier.size(8.dp).clip(CircleShape).background(color.copy(alpha = dotAlpha))) {}
        AnimatedContent(
            targetState = text,
            transitionSpec = { fadeIn(tween(200)) togetherWith fadeOut(tween(150)) },
            label = "statusText",
        ) { t ->
            Text(t, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}
