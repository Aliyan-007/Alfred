package com.alfred.android.ui.dashboard

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.alfred.android.service.ConnectionState
import com.alfred.android.ui.components.AlfredLogo
import com.alfred.android.ui.components.InfoRow
import com.alfred.android.ui.components.SectionCard
import com.alfred.android.ui.components.StatusLevel
import com.alfred.android.ui.components.StatusPill
import com.alfred.android.ui.theme.AlfredOnSurfaceMuted
import com.alfred.android.ui.theme.AlfredPrimary
import com.alfred.android.viewmodel.DashboardViewModel
import kotlinx.coroutines.delay

@Composable
fun DashboardScreen(onNavigate: (String) -> Unit, viewModel: DashboardViewModel = viewModel()) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    Scaffold(containerColor = MaterialTheme.colorScheme.background) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).padding(16.dp, 20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                AlfredLogo()
                Spacer(Modifier.width(14.dp))
                Column {
                    Text("ALFRED", style = MaterialTheme.typography.displayLarge, color = MaterialTheme.colorScheme.onBackground, fontWeight = FontWeight.Bold)
                    Text("Android Device Agent", style = MaterialTheme.typography.titleMedium, color = AlfredPrimary)
                }
            }
            var sectionIndex = 0
            Staggered(sectionIndex++) { ConnectionSection(state) }
            Staggered(sectionIndex++) { DeviceSection(state) }
            Staggered(sectionIndex++) { BatterySection(state) }
            Staggered(sectionIndex++) { CapabilitiesSection(state) }
            Staggered(sectionIndex++) { PermissionsSection(state) }
            Staggered(sectionIndex++) { ServiceSection(state, viewModel) }
            Staggered(sectionIndex++) { ActionsSection(onNavigate, viewModel) }
            Staggered(sectionIndex) {
                SectionCard(title = "Status") {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.Build, null, tint = AlfredPrimary)
                        Spacer(Modifier.width(8.dp))
                        Text("Configure Hub in Settings, then Start Agent and Pair. Commands route through the capability registry.",
                            style = MaterialTheme.typography.bodyMedium, color = AlfredOnSurfaceMuted)
                    }
                }
            }
        }
    }
}

/**
 * Fades + slides a section in shortly after the screen appears, staggered by
 * [index] so sections cascade into place rather than popping in all at once.
 */
@Composable
private fun Staggered(index: Int, content: @Composable () -> Unit) {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        delay(index * 55L)
        visible = true
    }
    AnimatedVisibility(
        visible = visible,
        enter = fadeIn(animationSpec = tween(350)) + slideInVertically(
            initialOffsetY = { it / 5 },
            animationSpec = spring(dampingRatio = Spring.DampingRatioLowBouncy, stiffness = Spring.StiffnessMediumLow),
        ),
    ) {
        content()
    }
}

/** Subtle press-in feedback shared by every outlined action button on the dashboard. */
@Composable
private fun rememberPressScale(): Pair<MutableInteractionSource, Float> {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.95f else 1f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessHigh),
        label = "pressScale",
    )
    return interactionSource to scale
}

@Composable
private fun ConnectionSection(state: DashboardUiState) {
    val (label, level) = when (state.connectionState) {
        ConnectionState.CONNECTED -> "Connected to Hub" to StatusLevel.OK
        ConnectionState.CONNECTING -> "Connecting…" to StatusLevel.NEUTRAL
        ConnectionState.RECONNECTING -> "Reconnecting…" to StatusLevel.WARNING
        ConnectionState.AUTHENTICATION_FAILED -> "Authentication failed" to StatusLevel.ERROR
        ConnectionState.DISCONNECTED -> "Disconnected" to StatusLevel.OFF
    }
    SectionCard(title = "Connection") {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Status", color = AlfredOnSurfaceMuted, style = MaterialTheme.typography.bodyMedium)
            StatusPill(label, level)
        }
        InfoRow("Hub address", state.hubUrl.ifBlank { "Not configured" }, monospaceValue = state.hubUrl.isNotBlank())
        InfoRow("Authenticated", if (state.authenticated) "Yes" else "No")
        InfoRow("Paired", if (state.paired) "Yes" else "No")
    }
}

@Composable
private fun DeviceSection(s: DashboardUiState) = SectionCard(title = "Device") {
    InfoRow("Name", s.deviceName)
    InfoRow("Device ID", s.deviceId, monospaceValue = true)
    InfoRow("Model", "${s.manufacturer} ${s.model}")
    InfoRow("Android", s.androidVersion)
    InfoRow("App version", s.appVersion, monospaceValue = true)
}

@Composable
private fun BatterySection(s: DashboardUiState) = SectionCard(title = "Battery") {
    InfoRow("Level", s.batteryLevel?.let { "$it%" } ?: "Unknown")
    InfoRow("Charging", when (s.isCharging) { true -> "Yes"; false -> "No"; null -> "Unknown" })
}

@Composable
private fun CapabilitiesSection(s: DashboardUiState) = SectionCard(title = "Capabilities") {
    if (s.capabilities.isEmpty()) Text("None registered.", color = AlfredOnSurfaceMuted)
    else s.capabilities.forEach { CapabilityRow(it) }
    Spacer(Modifier.height(6.dp))
    Text("Only 'available' capabilities are usable by the Hub.",
        style = MaterialTheme.typography.labelSmall, color = AlfredOnSurfaceMuted)
}

@Composable
private fun PermissionsSection(s: DashboardUiState) = SectionCard(title = "Permissions") {
    s.permissions.forEach { PermissionRow(it) }
}

@Composable
private fun ServiceSection(s: DashboardUiState, vm: DashboardViewModel) = SectionCard(title = "Service") {
    InfoRow("Foreground service", if (s.foregroundServiceRunning) "Running" else "Stopped")
    s.lastCommand?.let { InfoRow("Last command", it) }
    s.lastResult?.let { InfoRow("Last result", it) }
    Spacer(Modifier.height(8.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        val (startSource, startScale) = rememberPressScale()
        OutlinedButton(onClick = { vm.startService() }, enabled = !s.foregroundServiceRunning,
            interactionSource = startSource,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = AlfredPrimary),
            modifier = Modifier.weight(1f).scale(startScale)) {
            Icon(Icons.Filled.PlayArrow, null, modifier = Modifier.padding(end = 6.dp)); Text("Start Agent")
        }
        val (stopSource, stopScale) = rememberPressScale()
        OutlinedButton(onClick = { vm.stopService() }, enabled = s.foregroundServiceRunning,
            interactionSource = stopSource,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error),
            modifier = Modifier.weight(1f).scale(stopScale)) {
            Icon(Icons.Filled.Stop, null, modifier = Modifier.padding(end = 6.dp)); Text("Stop Agent")
        }
    }
}

@Composable
private fun ActionsSection(onNavigate: (String) -> Unit, vm: DashboardViewModel) = SectionCard(title = "Actions") {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            ActButton("Pair", Icons.Filled.Link, Modifier.weight(1f)) { onNavigate("pairing") }
            ActButton("Test", Icons.Filled.PlayArrow, Modifier.weight(1f)) { vm.testConnection() }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            ActButton("Permissions", Icons.Filled.Lock, Modifier.weight(1f)) { onNavigate("permissions") }
            ActButton("Settings", Icons.Filled.Settings, Modifier.weight(1f)) { onNavigate("settings") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            ActButton("Logs", Icons.Filled.Description, Modifier.weight(1f)) { onNavigate("logs") }
        }
    }
}

@Composable
private fun ActButton(text: String, icon: ImageVector, modifier: Modifier = Modifier, onClick: () -> Unit) {
    val (source, scale) = rememberPressScale()
    OutlinedButton(
        onClick = onClick,
        modifier = modifier.scale(scale),
        interactionSource = source,
        colors = ButtonDefaults.outlinedButtonColors(contentColor = AlfredPrimary),
    ) {
        Icon(icon, null, modifier = Modifier.padding(end = 6.dp)); Text(text, style = MaterialTheme.typography.labelLarge)
    }
}
