package com.alfred.android.ui.permissions

import android.content.Intent
import android.net.Uri
import android.provider.Settings
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.alfred.android.ui.components.SectionCard
import com.alfred.android.ui.theme.AlfredOnSurfaceMuted
import com.alfred.android.ui.theme.AlfredPrimary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PermissionsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    Scaffold(containerColor = MaterialTheme.colorScheme.background, topBar = {
        TopAppBar(title = { Text("Permissions", color = MaterialTheme.colorScheme.onBackground) },
            navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back", tint = AlfredPrimary) } },
            colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background))
    }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)) {
            SectionCard(title = "Notification access") {
                Text("Required for reading notifications.", color = AlfredOnSurfaceMuted)
                Button(onClick = { context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) },
                    colors = ButtonDefaults.buttonColors(containerColor = AlfredPrimary)) { Text("Open Notification access") }
            }
            SectionCard(title = "Accessibility (optional)") {
                Text("Required only for tap/swipe/back/home automation. Disabled by default; visibly shown on the dashboard.", color = AlfredOnSurfaceMuted)
                Button(onClick = { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) },
                    colors = ButtonDefaults.buttonColors(containerColor = AlfredPrimary)) { Text("Open Accessibility settings") }
            }
            SectionCard(title = "Battery optimization") {
                Text("Disable for reliable background connection.", color = AlfredOnSurfaceMuted)
                Button(onClick = {
                    runCatching { context.startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:${context.packageName}")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
                }, colors = ButtonDefaults.buttonColors(containerColor = AlfredPrimary)) { Text("Request unrestricted battery") }
            }
            SectionCard(title = "App info") {
                Button(onClick = { context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:${context.packageName}")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) },
                    colors = ButtonDefaults.buttonColors(containerColor = AlfredPrimary)) { Text("Open App info") }
            }
        }
    }
}
