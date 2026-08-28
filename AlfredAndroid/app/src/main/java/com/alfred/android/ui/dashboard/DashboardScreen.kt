package com.alfred.android.ui.dashboard

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
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
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.PhoneAndroid
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.PowerSettingsNew
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
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
import com.alfred.android.viewmodel.DashboardViewModel
import kotlinx.coroutines.delay

@Composable
fun DashboardScreen(
    onNavigate: (String) -> Unit,
    viewModel: DashboardViewModel = viewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {

            DashboardHeader(state)

            var sectionIndex = 0

            Staggered(sectionIndex++) {
                SystemStatusCard(state)
            }

            Staggered(sectionIndex++) {
                ConnectionSection(state)
            }

            Staggered(sectionIndex++) {
                DeviceSection(state)
            }

            Staggered(sectionIndex++) {
                BatterySection(state)
            }

            Staggered(sectionIndex++) {
                ServiceSection(state, viewModel)
            }

            Staggered(sectionIndex++) {
                CapabilitiesSection(state)
            }

            Staggered(sectionIndex++) {
                PermissionsSection(state)
            }
            Staggered(sectionIndex++) {
                VoiceSection(
                    state = state,
                    viewModel = viewModel
                )
            }
            Staggered(sectionIndex++) {
                ActionsSection(onNavigate, viewModel)
            }

            Staggered(sectionIndex) {
                AlfredFooter()
            }

            Spacer(Modifier.height(12.dp))
        }
    }
}

@Composable
private fun DashboardHeader(
    state: DashboardUiState,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
    ) {

        AlfredLogo()

        Spacer(Modifier.width(14.dp))

        Column(
            modifier = Modifier.weight(1f),
        ) {

            Text(
                text = "ALFRED",
                style = MaterialTheme.typography.displayLarge,
                color = MaterialTheme.colorScheme.onBackground,
                fontWeight = FontWeight.Bold,
            )

            Text(
                text = "Android Device Agent",
                style = MaterialTheme.typography.titleMedium,
                color = AlfredPrimary,
            )
        }

        ConnectionIndicator(state.connectionState)
    }
}

@Composable
private fun ConnectionIndicator(
    state: ConnectionState,
) {
    val color = when (state) {
        ConnectionState.CONNECTED -> Color(0xFF4CAF50)
        ConnectionState.CONNECTING -> AlfredPrimary
        ConnectionState.RECONNECTING -> Color(0xFFFFA000)
        ConnectionState.AUTHENTICATION_FAILED -> Color(0xFFF44336)
        ConnectionState.DISCONNECTED -> AlfredOnSurfaceMuted
    }

    Box(
        modifier = Modifier
            .size(14.dp)
            .background(color, CircleShape),
    )
}

@Composable
private fun SystemStatusCard(
    state: DashboardUiState,
) {
    val connected =
        state.connectionState == ConnectionState.CONNECTED

    val running =
        state.foregroundServiceRunning

    val title = when {
        connected && running ->
            "ALFRED ONLINE"

        running ->
            "AGENT STARTING"

        else ->
            "ALFRED OFFLINE"
    }

    val description = when {
        connected && state.authenticated ->
            "Connected and authenticated with your Alfred Hub."

        running ->
            "Agent service is running. Waiting for Hub connection."

        else ->
            "Start the agent to connect this Android device."
    }

    SectionCard(
        title = "System Status",
    ) {

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
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
                modifier = Modifier.size(38.dp),
            )

            Spacer(Modifier.width(12.dp))

            Column(
                modifier = Modifier.weight(1f),
            ) {

                Text(
                    text = title,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )

                Spacer(Modifier.height(3.dp))

                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = AlfredOnSurfaceMuted,
                )
            }
        }
    }
}

/**
 * Fades and slides sections into the screen.
 */
@Composable
private fun Staggered(
    index: Int,
    content: @Composable () -> Unit,
) {
    var visible by remember {
        mutableStateOf(false)
    }

    LaunchedEffect(Unit) {
        delay(index * 55L)
        visible = true
    }

    AnimatedVisibility(
        visible = visible,
        enter =
            fadeIn(
                animationSpec = tween(350),
            ) +
                slideInVertically(
                    initialOffsetY = { it / 5 },
                    animationSpec =
                        spring(
                            dampingRatio =
                                Spring.DampingRatioMediumBouncy,
                            stiffness =
                                Spring.StiffnessMediumLow,
                        ),
                ),
    ) {
        content()
    }
}

/**
 * Shared press animation for dashboard buttons.
 */
@Composable
private fun rememberPressScale():
    Pair<MutableInteractionSource, Float> {

    val interactionSource =
        remember {
            MutableInteractionSource()
        }

    val isPressed by
        interactionSource.collectIsPressedAsState()

    val scale by animateFloatAsState(
        targetValue =
            if (isPressed) {
                0.96f
            } else {
                1f
            },
        animationSpec =
            spring(
                dampingRatio =
                    Spring.DampingRatioMediumBouncy,
                stiffness =
                    Spring.StiffnessHigh,
            ),
        label = "pressScale",
    )

    return interactionSource to scale
}

@Composable
private fun ConnectionSection(
    state: DashboardUiState,
) {
    val (label, level) =
        when (state.connectionState) {

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
        title = "Connection",
    ) {

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement =
                Arrangement.SpaceBetween,
            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            Text(
                text = "Hub Status",
                color = AlfredOnSurfaceMuted,
                style =
                    MaterialTheme.typography.bodyMedium,
            )

            StatusPill(
                label,
                level,
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
            },
        )

        InfoRow(
            "Paired",
            if (state.paired) {
                "Yes"
            } else {
                "No"
            },
        )
    }
}

@Composable
private fun DeviceSection(
    state: DashboardUiState,
) {
    SectionCard(
        title = "Device",
    ) {

        Row(
            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            Icon(
                imageVector =
                    Icons.Filled.PhoneAndroid,
                contentDescription = null,
                tint = AlfredPrimary,
            )

            Spacer(Modifier.width(8.dp))

            Text(
                text = state.deviceName,
                style =
                    MaterialTheme.typography.titleMedium,
                fontWeight =
                    FontWeight.SemiBold,
                maxLines = 1,
                overflow =
                    TextOverflow.Ellipsis,
            )
        }

        Spacer(Modifier.height(4.dp))

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
    state: DashboardUiState,
) {
    SectionCard(
        title = "Battery",
    ) {

        Row(
            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            Icon(
                imageVector =
                    Icons.Filled.BatteryChargingFull,
                contentDescription = null,
                tint = AlfredPrimary,
                modifier =
                    Modifier.size(30.dp),
            )

            Spacer(Modifier.width(10.dp))

            Column {

                Text(
                    text =
                        state.batteryLevel
                            ?.let {
                                "$it%"
                            }
                            ?: "Unknown",
                    style =
                        MaterialTheme.typography.titleLarge,
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
                        MaterialTheme.typography.bodySmall,
                    color =
                        AlfredOnSurfaceMuted,
                )
            }
        }
    }
}

@Composable
private fun CapabilitiesSection(
    state: DashboardUiState,
) {
    SectionCard(
        title = "Capabilities",
    ) {

        if (
            state.capabilities.isEmpty()
        ) {

            Text(
                "No capabilities registered.",
                color =
                    AlfredOnSurfaceMuted,
            )

        } else {

            state.capabilities.forEach {
                CapabilityRow(it)
            }
        }

        Spacer(
            Modifier.height(6.dp),
        )

        Text(
            text =
                "Available capabilities can receive commands from Alfred Hub.",
            style =
                MaterialTheme.typography.labelSmall,
            color =
                AlfredOnSurfaceMuted,
        )
    }
}

@Composable
private fun PermissionsSection(
    state: DashboardUiState,
) {
    SectionCard(
        title = "Permissions",
    ) {

        if (
            state.permissions.isEmpty()
        ) {

            Text(
                "No permission information available.",
                color =
                    AlfredOnSurfaceMuted,
            )

        } else {

            state.permissions.forEach {
                PermissionRow(it)
            }
        }
    }
}

@Composable
private fun ServiceSection(
    state: DashboardUiState,
    viewModel: DashboardViewModel,
) {
    SectionCard(
        title = "Agent Service",
    ) {

        InfoRow(
            "Foreground service",
            if (
                state.foregroundServiceRunning
            ) {
                "Running"
            } else {
                "Stopped"
            },
        )

        state.lastCommand?.let {

            InfoRow(
                "Last command",
                it,
            )
        }

        state.lastResult?.let {

            InfoRow(
                "Last result",
                it,
            )
        }

        Spacer(
            Modifier.height(8.dp),
        )

        Row(
            modifier =
                Modifier.fillMaxWidth(),
            horizontalArrangement =
                Arrangement.spacedBy(8.dp),
        ) {

            val (
                startSource,
                startScale,
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
                                AlfredPrimary,
                        ),
                modifier =
                    Modifier
                        .weight(1f)
                        .scale(startScale),
            ) {

                Icon(
                    Icons.Filled.PlayArrow,
                    contentDescription = null,
                )

                Spacer(
                    Modifier.width(4.dp),
                )

                Text(
                    "Start",
                )
            }

            val (
                stopSource,
                stopScale,
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
                                    .error,
                        ),
                modifier =
                    Modifier
                        .weight(1f)
                        .scale(stopScale),
            ) {

                Icon(
                    Icons.Filled.Stop,
                    contentDescription = null,
                )

                Spacer(
                    Modifier.width(4.dp),
                )

                Text(
                    "Stop",
                )
            }
        }
    }
}

@Composable
private fun VoiceSection(
    state: DashboardUiState,
    viewModel: DashboardViewModel,
) {

    SectionCard(
        title = "Voice Assistant",
    ) {

        Column(
            modifier =
                Modifier.fillMaxWidth(),
            horizontalAlignment =
                Alignment.CenterHorizontally,
        ) {

            Text(
                text =
                    state.voiceStatus,
                style =
                    MaterialTheme.typography.titleMedium,
                fontWeight =
                    FontWeight.SemiBold,
            )

            Spacer(
                Modifier.height(8.dp),
            )

            if (
                state.lastVoiceText.isNotBlank()
            ) {

                Text(
                    text =
                        "\"${state.lastVoiceText}\"",
                    style =
                        MaterialTheme.typography.bodyMedium,
                    color =
                        AlfredOnSurfaceMuted,
                )

                Spacer(
                    Modifier.height(12.dp),
                )
            }

            val (
                source,
                scale,
            ) =
                rememberPressScale()

            OutlinedButton(
                onClick = {

                    viewModel.toggleVoiceListening()
                },

                interactionSource =
                    source,

                colors =
                    ButtonDefaults
                        .outlinedButtonColors(
                            contentColor =
                                if (
                                    state.voiceListening
                                ) {
                                    MaterialTheme
                                        .colorScheme
                                        .error
                                } else {
                                    AlfredPrimary
                                }
                        ),

                modifier =
                    Modifier
                        .size(
                            width = 180.dp,
                            height = 56.dp
                        )
                        .scale(scale),
            ) {

                Icon(
                    imageVector =
                        if (
                            state.voiceListening
                        ) {
                            Icons.Filled.MicOff
                        } else {
                            Icons.Filled.Mic
                        },

                    contentDescription =
                        if (
                            state.voiceListening
                        ) {
                            "Stop listening"
                        } else {
                            "Start listening"
                        },

                    modifier =
                        Modifier.size(26.dp),
                )

                Spacer(
                    Modifier.width(8.dp),
                )

                Text(
                    text =
                        if (
                            state.voiceListening
                        ) {
                            "Stop"
                        } else {
                            "Speak"
                        }
                )
            }

            Spacer(
                Modifier.height(8.dp),
            )

            Text(
                text =
                    if (
                        state.voiceListening
                    ) {
                        "Alfred is listening..."
                    } else {
                        "Tap Speak to give Alfred a command"
                    },

                style =
                    MaterialTheme.typography.bodySmall,

                color =
                    AlfredOnSurfaceMuted,
            )
        }
    }
}

@Composable
private fun ActionsSection(
    onNavigate: (String) -> Unit,
    viewModel: DashboardViewModel,
) {
    SectionCard(
        title = "Quick Actions",
    ) {

        Column(
            verticalArrangement =
                Arrangement.spacedBy(8.dp),
        ) {

            Row(
                modifier =
                    Modifier.fillMaxWidth(),
                horizontalArrangement =
                    Arrangement.spacedBy(8.dp),
            ) {

                ActButton(
                    text = "Pair",
                    icon =
                        Icons.Filled.Link,
                    modifier =
                        Modifier.weight(1f),
                ) {
                    onNavigate("pairing")
                }

                ActButton(
                    text = "Test",
                    icon =
                        Icons.Filled.Sync,
                    modifier =
                        Modifier.weight(1f),
                ) {
                    viewModel.testConnection()
                }
            }

            Row(
                modifier =
                    Modifier.fillMaxWidth(),
                horizontalArrangement =
                    Arrangement.spacedBy(8.dp),
            ) {

                ActButton(
                    text = "Permissions",
                    icon =
                        Icons.Filled.Lock,
                    modifier =
                        Modifier.weight(1f),
                ) {
                    onNavigate("permissions")
                }

                ActButton(
                    text = "Settings",
                    icon =
                        Icons.Filled.Settings,
                    modifier =
                        Modifier.weight(1f),
                ) {
                    onNavigate("settings")
                }
            }

            Row(
                modifier =
                    Modifier.fillMaxWidth(),
                horizontalArrangement =
                    Arrangement.spacedBy(8.dp),
            ) {

                ActButton(
                    text = "Logs",
                    icon =
                        Icons.Filled.Description,
                    modifier =
                        Modifier.weight(1f),
                ) {
                    onNavigate("logs")
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
        scale,
    ) =
        rememberPressScale()

    OutlinedButton(
        onClick = onClick,
        modifier =
            modifier.scale(scale),
        interactionSource =
            source,
        colors =
            ButtonDefaults
                .outlinedButtonColors(
                    contentColor =
                        AlfredPrimary,
                ),
    ) {

        Icon(
            imageVector = icon,
            contentDescription = null,
        )

        Spacer(
            Modifier.width(6.dp),
        )

        Text(
            text = text,
            style =
                MaterialTheme.typography.labelLarge,
        )
    }
}

@Composable
private fun AlfredFooter() {

    Column {

        HorizontalDivider()

        Spacer(
            Modifier.height(12.dp),
        )

        Row(
            verticalAlignment =
                Alignment.CenterVertically,
        ) {

            Icon(
                imageVector =
                    Icons.Filled.Build,
                contentDescription = null,
                tint =
                    AlfredOnSurfaceMuted,
                modifier =
                    Modifier.size(18.dp),
            )

            Spacer(
                Modifier.width(8.dp),
            )

            Text(
                text =
                    "ALFRED • Android Device Agent",
                style =
                    MaterialTheme.typography.labelSmall,
                color =
                    AlfredOnSurfaceMuted,
            )
        }
    }
}