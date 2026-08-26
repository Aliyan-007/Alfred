package com.alfred.android.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.alfred.android.AlfredApplication
import com.alfred.android.ui.dashboard.DashboardScreen
import com.alfred.android.ui.logs.LogsScreen
import com.alfred.android.ui.pairing.PairingScreen
import com.alfred.android.ui.permissions.PermissionsScreen
import com.alfred.android.ui.settings.SettingsScreen
import com.alfred.android.viewmodel.DashboardViewModel

object Routes {
    const val DASHBOARD = "dashboard"
    const val PAIRING = "pairing"
    const val PERMISSIONS = "permissions"
    const val SETTINGS = "settings"
    const val LOGS = "logs"
}

@Composable
fun AlfredNavHost() {
    val navController = rememberNavController()
    val app = LocalContext.current.applicationContext as AlfredApplication
    val vm: DashboardViewModel = viewModel(factory = object : androidx.lifecycle.ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T = DashboardViewModel(app) as T
    })

    NavHost(navController = navController, startDestination = Routes.DASHBOARD) {
        composable(Routes.DASHBOARD) { DashboardScreen({ r -> navController.navigate(r) }, vm) }
        composable(Routes.PAIRING) { PairingScreen({ navController.popBackStack() }, vm) }
        composable(Routes.PERMISSIONS) { PermissionsScreen { navController.popBackStack() } }
        composable(Routes.SETTINGS) { SettingsScreen(app.container.settingsRepository) { navController.popBackStack() } }
        composable(Routes.LOGS) { LogsScreen({ navController.popBackStack() }, vm) }
    }
}
