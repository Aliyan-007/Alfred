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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.alfred.android.ui.theme.AlfredError
import com.alfred.android.ui.theme.AlfredOnSurfaceMuted
import com.alfred.android.ui.theme.AlfredPrimary

@Composable
fun PermissionRow(status: PermissionStatus, modifier: Modifier = Modifier) {
    val valueText = when { status.granted -> "Granted"; status.note != null -> status.note; else -> "Not granted" }
    val color = when { status.granted -> AlfredPrimary; status.note == "Disabled" -> AlfredOnSurfaceMuted; else -> AlfredError }
    Row(modifier = modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        Text(status.name, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurface)
        Text(valueText, style = MaterialTheme.typography.labelLarge, color = color, textAlign = TextAlign.End)
    }
}
