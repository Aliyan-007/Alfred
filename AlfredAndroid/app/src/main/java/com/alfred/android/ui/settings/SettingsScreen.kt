package com.alfred.android.ui.settings

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.alfred.android.storage.SettingsRepository
import com.alfred.android.ui.theme.AlfredOnSurfaceMuted
import com.alfred.android.ui.theme.AlfredPrimary
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(settingsRepository: SettingsRepository, onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var host by remember { mutableStateOf("") }
    var port by remember { mutableStateOf("8765") }
    var scheme by remember { mutableStateOf("ws") }
    var name by remember { mutableStateOf("") }
    var saved by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        val s = settingsRepository.settings.first()
        host = s.hubHost; port = s.hubPort.toString(); scheme = s.hubScheme; name = s.deviceName
    }

    val saveInteractionSource = remember { MutableInteractionSource() }
    val isSavePressed by saveInteractionSource.collectIsPressedAsState()
    val saveScale by animateFloatAsState(
        targetValue = if (isSavePressed) 0.96f else 1f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessHigh),
        label = "saveButtonScale",
    )

    Scaffold(containerColor = MaterialTheme.colorScheme.background, topBar = {
        TopAppBar(title = { Text("Settings", color = MaterialTheme.colorScheme.onBackground) },
            navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back", tint = AlfredPrimary) } },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background))
    }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(host, { host = it; saved = false }, label = { Text("Hub host / IP") }, placeholder = { Text("192.168.1.100") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(port, { port = it.filter { c -> c.isDigit() }.take(5); saved = false }, label = { Text("Hub port") }, singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.fillMaxWidth())
            OutlinedTextField(scheme, { scheme = it.lowercase().take(3); saved = false }, label = { Text("Scheme (ws / wss)") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(name, { name = it; saved = false }, label = { Text("Device display name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            Button(
                onClick = {
                    scope.launch {
                        settingsRepository.setHubHost(host)
                        settingsRepository.setHubPort(port.toIntOrNull() ?: 8765)
                        runCatching { settingsRepository.setHubScheme(scheme) }
                        settingsRepository.setDeviceName(name)
                        saved = true
                    }
                },
                interactionSource = saveInteractionSource,
                colors = ButtonDefaults.buttonColors(containerColor = AlfredPrimary),
                modifier = Modifier.fillMaxWidth().scale(saveScale),
            ) { Text("Save") }

            // Confirmation eases in/out rather than popping, so it reads as a
            // response to the tap instead of a layout jump.
            AnimatedContent(
                targetState = saved,
                transitionSpec = { fadeIn() togetherWith fadeOut() },
                label = "savedConfirmation"
            ) { isSaved ->
                if (isSaved) {
                    Text("Saved. Restart the agent to apply.", color = AlfredPrimary)
                }
            }
            Text("Use ws:// for local Wi-Fi. No PC IP is hardcoded.",
                style = MaterialTheme.typography.labelSmall, color = AlfredOnSurfaceMuted)
        }
    }
}

@Composable
private fun rememberCoroutineScope() = androidx.compose.runtime.rememberCoroutineScope()
