package com.alfred.android.ui.dashboard

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BatteryChargingFull
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.PhoneAndroid
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.PowerSettingsNew
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
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
import com.alfred.android.ui.theme.AlfredSecondary
import com.alfred.android.ui.theme.AlfredTertiary
import com.alfred.android.viewmodel.DashboardViewModel
import kotlinx.coroutines.delay

@Composable
fun DashboardScreen(
    onNavigate: (String) -> Unit,
    viewModel: DashboardViewModel = viewModel(),
) {

    val state by
        viewModel.uiState
            .collectAsStateWithLifecycle()

    Scaffold(
        containerColor =
            MaterialTheme.colorScheme.background,
    ) { padding ->

        Column(
            modifier =
                Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .verticalScroll(
                        rememberScrollState()
                    )
                    .padding(
                        horizontal = 16.dp,
                        vertical = 16.dp
                    ),

            verticalArrangement =
                Arrangement.spacedBy(16.dp),
        ) {

            var sectionIndex = 0

            Staggered(sectionIndex++) {
                CommandCenterHero(
                    state
                )
            }

            Staggered(sectionIndex++) {
                TelemetryStrip(
                    state
                )
            }

            Staggered(sectionIndex++) {
                LiveChannelPanel(
                    state,
                    viewModel
                )
            }

            Staggered(sectionIndex++) {
                DeviceIdentityPanel(
                    state
                )
            }

            Staggered(sectionIndex++) {
                CapabilityMatrix(
                    state.capabilities
                )
            }

            Staggered(sectionIndex++) {
                PermissionMatrix(
                    state.permissions
                )
            }

            Staggered(sectionIndex++) {
                CommandDock(
                    onNavigate,
                    viewModel,
                    state
                )
            }

            Staggered(sectionIndex) {
                DashboardFooter()
            }

            Spacer(
                Modifier.height(12.dp)
            )
        }
    }
}

@Composable
private fun CommandCenterHero(state: DashboardUiState) {
    val connected = state.connectionState == ConnectionState.CONNECTED
    val statusColor = if (connected) AlfredPrimary else MaterialTheme.colorScheme.error
    val statusTitle = when {
        connected && state.authenticated -> "SYSTEMS NOMINAL"
        state.foregroundServiceRunning -> "LINK IN PROGRESS"
        else -> "AGENT STANDBY"
    }

    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.extraLarge,
        color = MaterialTheme.colorScheme.primaryContainer,
    ) {
        Box(Modifier.padding(20.dp)) {
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Top,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            text = "ALFRED / COMMAND CENTER",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.72f),
                        )
                        Spacer(Modifier.height(6.dp))
                        Text(
                            text = "${state.deviceName.ifBlank { "Android Agent" }} online.",
                            style = MaterialTheme.typography.headlineMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer,
                        )
                    }
                    Surface(
                        shape = CircleShape,
                        color = statusColor.copy(alpha = 0.18f),
                        modifier = Modifier.size(52.dp),
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Box(Modifier.size(14.dp).background(statusColor, CircleShape))
                        }
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.Bottom,
                ) {
                    Column {
                        Text(
                            text = statusTitle,
                            style = MaterialTheme.typography.titleLarge,
                            color = statusColor,
                        )
                        Text(
                            text = state.hubUrl.ifBlank { "Hub endpoint not configured" },
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    Text(
                        text = if (connected) "LIVE" else "OFFLINE",
                        style = MaterialTheme.typography.labelLarge,
                        color = statusColor,
                    )
                }
            }
        }
    }
}

@Composable
private fun TelemetryStrip(state: DashboardUiState) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        TelemetryTile(
            label = "BATTERY",
            value = state.batteryLevel?.let { "$it%" } ?: "--",
            detail = if (state.isCharging == true) "CHARGING" else "POWER",
            accent = AlfredPrimary,
            modifier = Modifier.weight(1f),
        )
        TelemetryTile(
            label = "PAIRING",
            value = if (state.paired) "READY" else "OPEN",
            detail = if (state.authenticated) "TRUSTED" else "AWAITING HUB",
            accent = AlfredSecondary,
            modifier = Modifier.weight(1f),
        )
        TelemetryTile(
            label = "NODES",
            value = state.capabilities.size.toString().padStart(2, '0'),
            detail = "CAPABILITIES",
            accent = AlfredTertiary,
            modifier = Modifier.weight(1f),
        )
    }
}

@Composable
private fun TelemetryTile(
    label: String,
    value: String,
    detail: String,
    accent: Color,
    modifier: Modifier,
) {
    Surface(
        modifier = modifier,
        shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surfaceVariant,
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(label, style = MaterialTheme.typography.labelSmall, color = accent)
            Text(value, style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSurface)
            Text(detail, style = MaterialTheme.typography.labelSmall, color = AlfredOnSurfaceMuted)
        }
    }
}

@Composable
private fun LiveChannelPanel(state: DashboardUiState, viewModel: DashboardViewModel) {
    val listening = state.voiceListening
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(
                    shape = MaterialTheme.shapes.small,
                    color = if (listening) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.secondaryContainer,
                ) {
                    Icon(
                        imageVector = if (listening) Icons.Filled.Mic else Icons.Filled.Sync,
                        contentDescription = null,
                        tint = if (listening) MaterialTheme.colorScheme.error else AlfredSecondary,
                        modifier = Modifier.padding(10.dp).size(24.dp),
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text("LIVE CHANNEL", style = MaterialTheme.typography.labelMedium, color = AlfredSecondary)
                    Text(
                        if (listening) "Voice channel open" else "Voice channel ready",
                        style = MaterialTheme.typography.titleLarge,
                    )
                }
                Text(
                    if (state.foregroundServiceRunning) "ACTIVE" else "PAUSED",
                    style = MaterialTheme.typography.labelSmall,
                    color = if (state.foregroundServiceRunning) AlfredPrimary else AlfredOnSurfaceMuted,
                )
            }
            Text(
                state.lastVoiceText.takeIf { it.isNotBlank() } ?: state.voiceStatus.ifBlank { "No recent voice activity" },
                style = MaterialTheme.typography.bodyMedium,
                color = AlfredOnSurfaceMuted,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            FilledTonalButton(
                onClick = { viewModel.toggleVoiceListening() },
                enabled = state.foregroundServiceRunning,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(if (listening) Icons.Filled.Stop else Icons.Filled.Mic, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(if (listening) "Close voice channel" else "Open voice channel")
            }
        }
    }
}

@Composable
private fun DeviceIdentityPanel(state: DashboardUiState) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.small,
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.PhoneAndroid, contentDescription = null, tint = AlfredPrimary)
                Spacer(Modifier.width(10.dp))
                Text("DEVICE IDENTITY", style = MaterialTheme.typography.labelMedium, color = AlfredPrimary)
            }
            Text(
                "${state.manufacturer} ${state.model}".trim().ifBlank { "Android device" },
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                "${state.androidVersion}  /  ${state.appVersion}  /  ${state.deviceId}",
                style = MaterialTheme.typography.labelSmall,
                color = AlfredOnSurfaceMuted,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun CapabilityMatrix(capabilities: List<CapabilityStatus>) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surfaceVariant,
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("CAPABILITY MATRIX", style = MaterialTheme.typography.labelMedium, color = AlfredTertiary)
            if (capabilities.isEmpty()) {
                Text("No capability nodes registered.", color = AlfredOnSurfaceMuted)
            } else {
                capabilities.forEach { CapabilityRow(it) }
            }
        }
    }
}

@Composable
private fun PermissionMatrix(permissions: List<PermissionStatus>) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.extraSmall,
        color = MaterialTheme.colorScheme.surface,
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("ACCESS CONTROL", style = MaterialTheme.typography.labelMedium, color = AlfredSecondary)
                Text(
                    "${permissions.count { it.granted }}/${permissions.size}",
                    style = MaterialTheme.typography.labelMedium,
                    color = AlfredPrimary,
                )
            }
            if (permissions.isEmpty()) {
                Text("No permission telemetry available.", color = AlfredOnSurfaceMuted)
            } else {
                permissions.forEach { PermissionRow(it) }
            }
        }
    }
}

@Composable
private fun CommandDock(
    onNavigate: (String) -> Unit,
    viewModel: DashboardViewModel,
    state: DashboardUiState,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.extraLarge,
        color = MaterialTheme.colorScheme.secondaryContainer,
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("COMMAND DOCK", style = MaterialTheme.typography.labelMedium, color = AlfredSecondary)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = { onNavigate("pairing") }, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Filled.Link, contentDescription = null)
                    Spacer(Modifier.width(6.dp))
                    Text("Pair")
                }
                FilledTonalButton(onClick = { viewModel.testConnection() }, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Filled.Sync, contentDescription = null)
                    Spacer(Modifier.width(6.dp))
                    Text("Ping")
                }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { onNavigate("permissions") }, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Filled.Lock, contentDescription = null)
                    Spacer(Modifier.width(6.dp))
                    Text("Access")
                }
                OutlinedButton(onClick = { onNavigate("settings") }, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Filled.Settings, contentDescription = null)
                    Spacer(Modifier.width(6.dp))
                    Text("Tune")
                }
                OutlinedButton(onClick = { onNavigate("logs") }, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Filled.Description, contentDescription = null)
                    Spacer(Modifier.width(6.dp))
                    Text("Logs")
                }
            }
            if (!state.foregroundServiceRunning) {
                Text(
                    "Start the agent service to unlock live controls.",
                    style = MaterialTheme.typography.labelSmall,
                    color = AlfredOnSurfaceMuted,
                )
            }
        }
    }
}

@Composable
private fun DashboardFooter() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Filled.Build, contentDescription = null, tint = AlfredOnSurfaceMuted, modifier = Modifier.size(16.dp))
        Spacer(Modifier.width(8.dp))
        Text("ALFRED / ANDROID AGENT", style = MaterialTheme.typography.labelSmall, color = AlfredOnSurfaceMuted)
    }
}

@Composable
private fun DashboardHeader(
    state: DashboardUiState
) {

    Row(
        modifier =
            Modifier.fillMaxWidth(),

        verticalAlignment =
            Alignment.CenterVertically,
    ) {

        AlfredLogo()

        Spacer(
            Modifier.width(14.dp)
        )

        Column(
            modifier =
                Modifier.weight(1f),
        ) {

            Text(
                text = "ALFRED",
                style =
                    MaterialTheme
                        .typography
                        .displayLarge,
                color =
                    MaterialTheme
                        .colorScheme
                        .onBackground,
                fontWeight =
                    FontWeight.Bold,
            )

            Text(
                text =
                    "Android Device Agent",
                style =
                    MaterialTheme
                        .typography
                        .titleMedium,
                color =
                    AlfredPrimary,
            )
        }

        ConnectionIndicator(
            state.connectionState
        )
    }
}

@Composable
private fun ConnectionIndicator(
    state: ConnectionState
) {

    val color =
        when (state) {

            ConnectionState.CONNECTED ->
                Color(0xFF4CAF50)

            ConnectionState.CONNECTING ->
                AlfredPrimary

            ConnectionState.RECONNECTING ->
                Color(0xFFFFA000)

            ConnectionState.AUTHENTICATION_FAILED ->
                Color(0xFFF44336)

            ConnectionState.DISCONNECTED ->
                AlfredOnSurfaceMuted
        }

    Box(
        modifier =
            Modifier
                .size(14.dp)
                .background(
                    color,
                    CircleShape
                )
    )
}

@Composable
private fun SystemStatusCard(
    state: DashboardUiState
) {

    val connected =
        state.connectionState ==
            ConnectionState.CONNECTED

    val running =
        state.foregroundServiceRunning

    val title =
        when {

            connected && running ->
                "ALFRED ONLINE"

            running ->
                "AGENT STARTING"

            else ->
                "ALFRED OFFLINE"
        }

    val description =
        when {

            connected &&
                state.authenticated ->
                "Connected and authenticated with your Alfred Hub."

            running ->
                "Agent service is running. Waiting for Hub connection."

            else ->
                "Start the agent to connect this Android device."
        }

    SectionCard(
        title = "System Status"
    ) {

        Row(
            modifier =
                Modifier.fillMaxWidth(),

            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            val icon =
                if (connected) {
                    Icons.Filled.CheckCircle
                } else {
                    Icons.Filled.PowerSettingsNew
                }

            val iconColor =
                if (connected) {
                    Color(0xFF4CAF50)
                } else {
                    AlfredPrimary
                }

            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = iconColor,
                modifier =
                    Modifier.size(38.dp),
            )

            Spacer(
                Modifier.width(12.dp)
            )

            Column(
                modifier =
                    Modifier.weight(1f)
            ) {

                Text(
                    text = title,
                    style =
                        MaterialTheme
                            .typography
                            .titleLarge,
                    fontWeight =
                        FontWeight.Bold,
                )

                Spacer(
                    Modifier.height(3.dp)
                )

                Text(
                    text = description,
                    style =
                        MaterialTheme
                            .typography
                            .bodySmall,
                    color =
                        AlfredOnSurfaceMuted,
                )
            }
        }
    }
}

@Composable
private fun Staggered(
    index: Int,
    content: @Composable () -> Unit,
) {

    var visible by
        remember {
            mutableStateOf(false)
        }

    LaunchedEffect(Unit) {

        delay(
            index * 55L
        )

        visible = true
    }

    AnimatedVisibility(
        visible = visible,

        enter =
            fadeIn(
                animationSpec =
                    tween(350)
            ) +
                slideInVertically(
                    initialOffsetY = {
                        it / 5
                    },

                    animationSpec =
                        spring(
                            dampingRatio =
                                Spring
                                    .DampingRatioMediumBouncy,

                            stiffness =
                                Spring
                                    .StiffnessMediumLow,
                        )
                )
    ) {

        content()
    }
}

@Composable
private fun rememberPressScale():
    Pair<MutableInteractionSource, Float> {

    val interactionSource =
        remember {
            MutableInteractionSource()
        }

    val isPressed by
        interactionSource
            .collectIsPressedAsState()

    val scale by
        animateFloatAsState(
            targetValue =
                if (isPressed) {
                    0.96f
                } else {
                    1f
                },

            animationSpec =
                spring(
                    dampingRatio =
                        Spring
                            .DampingRatioMediumBouncy,

                    stiffness =
                        Spring.StiffnessHigh,
                ),

            label =
                "pressScale",
        )

    return interactionSource to scale
}

@Composable
private fun ConnectionSection(
    state: DashboardUiState
) {

    val (label, level) =
        when (
            state.connectionState
        ) {

            ConnectionState.CONNECTED ->
                "Connected" to StatusLevel.OK

            ConnectionState.CONNECTING ->
                "Connecting..." to StatusLevel.NEUTRAL

            ConnectionState.RECONNECTING ->
                "Reconnecting..." to StatusLevel.WARNING

            ConnectionState.AUTHENTICATION_FAILED ->
                "Authentication Failed" to StatusLevel.ERROR

            ConnectionState.DISCONNECTED ->
                "Disconnected" to StatusLevel.OFF
        }

    SectionCard(
        title = "Connection"
    ) {

        Row(
            modifier =
                Modifier.fillMaxWidth(),

            horizontalArrangement =
                Arrangement.SpaceBetween,

            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            Text(
                text = "Hub Status",
                color =
                    AlfredOnSurfaceMuted,
                style =
                    MaterialTheme
                        .typography
                        .bodyMedium,
            )

            StatusPill(
                label,
                level
            )
        }

        InfoRow(
            "Hub address",
            state.hubUrl.ifBlank {
                "Not configured"
            },
            monospaceValue =
                state.hubUrl.isNotBlank(),
        )

        InfoRow(
            "Authenticated",
            if (state.authenticated) {
                "Yes"
            } else {
                "No"
            }
        )

        InfoRow(
            "Paired",
            if (state.paired) {
                "Yes"
            } else {
                "No"
            }
        )
    }
}

@Composable
private fun DeviceSection(
    state: DashboardUiState
) {

    SectionCard(
        title = "Device"
    ) {

        Row(
            verticalAlignment =
                Alignment.CenterVertically
        ) {

            Icon(
                imageVector =
                    Icons.Filled.PhoneAndroid,
                contentDescription = null,
                tint =
                    AlfredPrimary,
            )

            Spacer(
                Modifier.width(8.dp)
            )

            Text(
                text =
                    state.deviceName,
                style =
                    MaterialTheme
                        .typography
                        .titleMedium,
                fontWeight =
                    FontWeight.SemiBold,
                maxLines = 1,
                overflow =
                    TextOverflow.Ellipsis,
            )
        }

        Spacer(
            Modifier.height(4.dp)
        )

        InfoRow(
            "Device ID",
            state.deviceId,
            monospaceValue = true,
        )

        InfoRow(
            "Model",
            "${state.manufacturer} ${state.model}",
        )

        InfoRow(
            "Android",
            state.androidVersion,
        )

        InfoRow(
            "App version",
            state.appVersion,
            monospaceValue = true,
        )
    }
}

@Composable
private fun BatterySection(
    state: DashboardUiState
) {

    SectionCard(
        title = "Battery"
    ) {

        Row(
            verticalAlignment =
                Alignment.CenterVertically
        ) {

            Icon(
                imageVector =
                    Icons.Filled.BatteryChargingFull,
                contentDescription = null,
                tint =
                    AlfredPrimary,
                modifier =
                    Modifier.size(30.dp),
            )

            Spacer(
                Modifier.width(10.dp)
            )

            Column {

                Text(
                    text =
                        state.batteryLevel
                            ?.let {
                                "$it%"
                            }
                            ?: "Unknown",

                    style =
                        MaterialTheme
                            .typography
                            .titleLarge,

                    fontWeight =
                        FontWeight.Bold,
                )

                Text(
                    text =
                        when (
                            state.isCharging
                        ) {

                            true ->
                                "Charging"

                            false ->
                                "On battery"

                            null ->
                                "Battery status unknown"
                        },

                    style =
                        MaterialTheme
                            .typography
                            .bodySmall,

                    color =
                        AlfredOnSurfaceMuted,
                )
            }
        }
    }
}

@Composable
private fun ServiceSection(
    state: DashboardUiState,
    viewModel: DashboardViewModel
) {

    SectionCard(
        title = "Agent Service"
    ) {

        InfoRow(
            "Foreground service",
            if (
                state.foregroundServiceRunning
            ) {
                "Running"
            } else {
                "Stopped"
            }
        )

        state.lastCommand?.let {

            InfoRow(
                "Last command",
                it
            )
        }

        state.lastResult?.let {

            InfoRow(
                "Last result",
                it
            )
        }

        Spacer(
            Modifier.height(8.dp)
        )

        Row(
            modifier =
                Modifier.fillMaxWidth(),

            horizontalArrangement =
                Arrangement.spacedBy(8.dp)
        ) {

            val (
                startSource,
                startScale
            ) =
                rememberPressScale()

            OutlinedButton(
                onClick = {
                    viewModel.startService()
                },

                enabled =
                    !state.foregroundServiceRunning,

                interactionSource =
                    startSource,

                colors =
                    ButtonDefaults
                        .outlinedButtonColors(
                            contentColor =
                                AlfredPrimary
                        ),

                modifier =
                    Modifier
                        .weight(1f)
                        .scale(startScale)
            ) {

                Icon(
                    Icons.Filled.PlayArrow,
                    contentDescription = null
                )

                Spacer(
                    Modifier.width(4.dp)
                )

                Text("Start")
            }

            val (
                stopSource,
                stopScale
            ) =
                rememberPressScale()

            OutlinedButton(
                onClick = {
                    viewModel.stopService()
                },

                enabled =
                    state.foregroundServiceRunning,

                interactionSource =
                    stopSource,

                colors =
                    ButtonDefaults
                        .outlinedButtonColors(
                            contentColor =
                                MaterialTheme
                                    .colorScheme
                                    .error
                        ),

                modifier =
                    Modifier
                        .weight(1f)
                        .scale(stopScale)
            ) {

                Icon(
                    Icons.Filled.Stop,
                    contentDescription = null
                )

                Spacer(
                    Modifier.width(4.dp)
                )

                Text("Stop")
            }
        }
    }
}

@Composable
private fun VoiceSection(
    state: DashboardUiState,
    viewModel: DashboardViewModel
) {

    val listening =
        state.voiceListening

    SectionCard(
        title = "ALFRED Voice"
    ) {

        Row(
            modifier =
                Modifier.fillMaxWidth(),

            verticalAlignment =
                Alignment.CenterVertically
        ) {

            Icon(
                imageVector =
                    Icons.Filled.Mic,

                contentDescription = null,

                tint =
                    if (listening) {
                        MaterialTheme
                            .colorScheme
                            .error
                    } else {
                        AlfredPrimary
                    },

                modifier =
                    Modifier.size(32.dp)
            )

            Spacer(
                Modifier.width(10.dp)
            )

            Column(
                modifier =
                    Modifier.weight(1f)
            ) {

                Text(
                    text =
                        if (listening) {
                            "Listening"
                        } else {
                            "Voice Ready"
                        },

                    style =
                        MaterialTheme
                            .typography
                            .titleMedium,

                    fontWeight =
                        FontWeight.SemiBold
                )

                Text(
                    text =
                        state.voiceStatus.ifBlank {
                            "Ready"
                        },

                    style =
                        MaterialTheme
                            .typography
                            .bodySmall,

                    color =
                        AlfredOnSurfaceMuted
                )
            }
        }

        state.lastVoiceText
            .takeIf {
                it.isNotBlank()
            }
            ?.let { text ->

                Spacer(
                    Modifier.height(10.dp)
                )

                InfoRow(
                    "Last voice command",
                    text
                )
            }

        Spacer(
            Modifier.height(10.dp)
        )

        val (
            source,
            scale
        ) =
            rememberPressScale()

        OutlinedButton(
            onClick = {

                viewModel
                    .toggleVoiceListening()

            },

            enabled =
                state.foregroundServiceRunning,

            interactionSource =
                source,

            colors =
                ButtonDefaults
                    .outlinedButtonColors(
                        contentColor =
                            if (listening) {
                                MaterialTheme
                                    .colorScheme
                                    .error
                            } else {
                                AlfredPrimary
                            }
                    ),

            modifier =
                Modifier
                    .fillMaxWidth()
                    .scale(scale)
        ) {

            Icon(
                imageVector =
                    if (listening) {
                        Icons.Filled.Stop
                    } else {
                        Icons.Filled.Mic
                    },

                contentDescription = null
            )

            Spacer(
                Modifier.width(6.dp)
            )

            Text(
                if (listening) {
                    "Stop Listening"
                } else {
                    "Start Listening"
                }
            )
        }

        if (
            !state.foregroundServiceRunning
        ) {

            Spacer(
                Modifier.height(6.dp)
            )

            Text(
                text =
                    "Start the Alfred Agent service before using voice control.",

                style =
                    MaterialTheme
                        .typography
                        .labelSmall,

                color =
                    AlfredOnSurfaceMuted
            )
        }
    }
}

@Composable
private fun CapabilitiesSection(
    state: DashboardUiState
) {

    SectionCard(
        title = "Capabilities"
    ) {

        if (
            state.capabilities.isEmpty()
        ) {

            Text(
                "No capabilities registered.",
                color =
                    AlfredOnSurfaceMuted
            )

        } else {

            state.capabilities.forEach {
                capability ->

                CapabilityRow(
                    capability
                )
            }
        }

        Spacer(
            Modifier.height(6.dp)
        )

        Text(
            text =
                "Available capabilities can receive commands from Alfred Hub.",

            style =
                MaterialTheme
                    .typography
                    .labelSmall,

            color =
                AlfredOnSurfaceMuted
        )
    }
}

@Composable
private fun PermissionsSection(
    state: DashboardUiState
) {

    SectionCard(
        title = "Permissions"
    ) {

        if (
            state.permissions.isEmpty()
        ) {

            Text(
                "No permission information available.",
                color =
                    AlfredOnSurfaceMuted
            )

        } else {

            state.permissions.forEach {
                permission ->

                PermissionRow(
                    permission
                )
            }
        }
    }
}

@Composable
private fun ActionsSection(
    onNavigate: (String) -> Unit,
    viewModel: DashboardViewModel
) {

    SectionCard(
        title = "Quick Actions"
    ) {

        Column(
            verticalArrangement =
                Arrangement.spacedBy(8.dp)
        ) {

            Row(
                modifier =
                    Modifier.fillMaxWidth(),

                horizontalArrangement =
                    Arrangement.spacedBy(8.dp)
            ) {

                ActButton(
                    text = "Pair",
                    icon =
                        Icons.Filled.Link,
                    modifier =
                        Modifier.weight(1f)
                ) {

                    onNavigate(
                        "pairing"
                    )
                }

                ActButton(
                    text = "Test",
                    icon =
                        Icons.Filled.Sync,
                    modifier =
                        Modifier.weight(1f)
                ) {

                    viewModel
                        .testConnection()
                }
            }

            Row(
                modifier =
                    Modifier.fillMaxWidth(),

                horizontalArrangement =
                    Arrangement.spacedBy(8.dp)
            ) {

                ActButton(
                    text = "Permissions",
                    icon =
                        Icons.Filled.Lock,
                    modifier =
                        Modifier.weight(1f)
                ) {

                    onNavigate(
                        "permissions"
                    )
                }

                ActButton(
                    text = "Settings",
                    icon =
                        Icons.Filled.Settings,
                    modifier =
                        Modifier.weight(1f)
                ) {

                    onNavigate(
                        "settings"
                    )
                }
            }

            Row(
                modifier =
                    Modifier.fillMaxWidth(),

                horizontalArrangement =
                    Arrangement.spacedBy(8.dp)
            ) {

                ActButton(
                    text = "Logs",
                    icon =
                        Icons.Filled.Description,
                    modifier =
                        Modifier.weight(1f)
                ) {

                    onNavigate(
                        "logs"
                    )
                }
            }
        }
    }
}

@Composable
private fun ActButton(
    text: String,
    icon: ImageVector,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {

    val (
        source,
        scale
    ) =
        rememberPressScale()

    OutlinedButton(
        onClick = onClick,

        modifier =
            modifier.scale(
                scale
            ),

        interactionSource =
            source,

        colors =
            ButtonDefaults
                .outlinedButtonColors(
                    contentColor =
                        AlfredPrimary
                )
    ) {

        Icon(
            imageVector = icon,
            contentDescription = null
        )

        Spacer(
            Modifier.width(6.dp)
        )

        Text(
            text = text,
            style =
                MaterialTheme
                    .typography
                    .labelLarge
        )
    }
}

@Composable
private fun AlfredFooter() {

    Column {

        HorizontalDivider()

        Spacer(
            Modifier.height(12.dp)
        )

        Row(
            verticalAlignment =
                Alignment.CenterVertically
        ) {

            Icon(
                imageVector =
                    Icons.Filled.Build,

                contentDescription = null,

                tint =
                    AlfredOnSurfaceMuted,

                modifier =
                    Modifier.size(18.dp)
            )

            Spacer(
                Modifier.width(8.dp)
            )

            Text(
                text =
                    "ALFRED • Android Device Agent",

                style =
                    MaterialTheme
                        .typography
                        .labelSmall,

                color =
                    AlfredOnSurfaceMuted
            )
        }
    }
}