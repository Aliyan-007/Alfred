package com.alfred.android.ui.pairing

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
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
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.alfred.android.service.ConnectionState
import com.alfred.android.ui.theme.AlfredPrimary
import com.alfred.android.ui.theme.AlfredWarning
import com.alfred.android.viewmodel.DashboardViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PairingScreen(onBack: () -> Unit, viewModel: DashboardViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var code by remember { mutableStateOf("") }

    val pairInteractionSource = remember { MutableInteractionSource() }
    val isPairPressed by pairInteractionSource.collectIsPressedAsState()
    val pairScale by animateFloatAsState(
        targetValue = if (isPairPressed) 0.96f else 1f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy, stiffness = Spring.StiffnessHigh),
        label = "pairButtonScale",
    )

    Scaffold(containerColor = MaterialTheme.colorScheme.background, topBar = {
        TopAppBar(title = { Text("Pairing", color = MaterialTheme.colorScheme.onBackground) },
            navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back", tint = AlfredPrimary) } },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background))
    }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Enter the pairing code shown on your PC (e.g. 482913). The returned token is stored encrypted.",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)

            val statusText = "Status: ${state.connectionState.displayName} • Paired: ${if (state.paired) "yes" else "no"}"
            AnimatedContent(
                targetState = statusText,
                transitionSpec = { fadeIn(tween(250)) togetherWith fadeOut(tween(150)) },
                label = "pairingStatus",
            ) { text ->
                Text(text, style = MaterialTheme.typography.labelLarge, color = if (state.paired) AlfredPrimary else AlfredWarning)
            }

            OutlinedTextField(code, { code = it.filter { c -> c.isDigit() }.take(8) }, label = { Text("Pair code") },
                singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.fillMaxWidth())
            Button(
                onClick = { viewModel.pairWithCode(code) },
                enabled = code.length >= 4 && state.connectionState == ConnectionState.CONNECTED,
                interactionSource = pairInteractionSource,
                colors = ButtonDefaults.buttonColors(containerColor = AlfredPrimary),
                modifier = Modifier.fillMaxWidth().scale(pairScale),
            ) { Text("Pair with Hub") }
            OutlinedButton(onClick = { viewModel.revokePairing() }, enabled = state.paired, modifier = Modifier.fillMaxWidth()) { Text("Revoke pairing") }
        }
    }
}
