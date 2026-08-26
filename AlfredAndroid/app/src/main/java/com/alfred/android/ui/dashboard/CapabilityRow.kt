package com.alfred.android.ui.dashboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.ui.components.StatusLevel
import com.alfred.android.ui.components.StatusPill

@Composable
fun CapabilityRow(status: CapabilityStatus, modifier: Modifier = Modifier) {
    val (label, level) = when (status.state) {
        CapabilityState.AVAILABLE -> "Available" to StatusLevel.OK
        CapabilityState.PERMISSION_REQUIRED -> "Permission needed" to StatusLevel.WARNING
        CapabilityState.UNSUPPORTED -> "Unsupported" to StatusLevel.ERROR
        CapabilityState.DISABLED -> "Disabled" to StatusLevel.OFF
        CapabilityState.UNAVAILABLE -> "Not implemented" to StatusLevel.OFF
    }
    Row(modifier = modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        Text(status.displayName, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Medium)
        StatusPill(text = label, status = level)
    }
}
