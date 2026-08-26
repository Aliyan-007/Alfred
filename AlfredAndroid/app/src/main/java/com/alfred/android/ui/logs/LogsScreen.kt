package com.alfred.android.ui.logs

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.alfred.android.agent.LogLevel
import com.alfred.android.ui.theme.AlfredError
import com.alfred.android.ui.theme.AlfredOnSurfaceMuted
import com.alfred.android.ui.theme.AlfredPrimary
import com.alfred.android.ui.theme.AlfredWarning
import com.alfred.android.viewmodel.DashboardViewModel
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LogsScreen(onBack: () -> Unit, viewModel: DashboardViewModel) {
    val logs by viewModel.logs.collectAsStateWithLifecycle()
    val fmt = remember { SimpleDateFormat("HH:mm:ss", Locale.US) }
    Scaffold(containerColor = MaterialTheme.colorScheme.background, topBar = {
        TopAppBar(title = { Text("Logs", color = MaterialTheme.colorScheme.onBackground) },
            navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back", tint = AlfredPrimary) } },
            actions = { OutlinedButton(onClick = { viewModel.clearLogs() }) { Text("Clear") } },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background))
    }) { padding ->
        if (logs.isEmpty()) {
            Text("No log entries yet. Start the agent or pair with the Hub.", color = AlfredOnSurfaceMuted,
                modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp))
        } else {
            LazyColumn(Modifier.fillMaxSize().padding(padding).padding(horizontal = 12.dp)) {
                items(logs.asReversed()) { e ->
                    val color = when (e.level) { LogLevel.ERROR -> AlfredError; LogLevel.WARN -> AlfredWarning; LogLevel.INFO -> MaterialTheme.colorScheme.onSurface }
                    Text("${fmt.format(Date(e.ts))}  ${e.message}", style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = color)
                }
            }
        }
    }
}

@Composable
private fun <T> remember(calculation: () -> T): T = androidx.compose.runtime.remember(calculation = calculation)
