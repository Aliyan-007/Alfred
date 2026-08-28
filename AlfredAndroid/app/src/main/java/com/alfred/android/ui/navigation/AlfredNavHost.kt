package com.alfred.android.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
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

    val app =
        LocalContext.current.applicationContext
            as AlfredApplication

    val viewModel: DashboardViewModel =
        viewModel(
            factory = DashboardViewModelFactory(app)
        )

    NavHost(
        navController = navController,
        startDestination = Routes.DASHBOARD,
    ) {

        composable(Routes.DASHBOARD) {

            DashboardScreen(
                onNavigate = { route ->
                    navController.navigate(route)
                },
                viewModel = viewModel,
            )
        }

        composable(Routes.PAIRING) {

            PairingScreen(
                onBack = {
                    navController.popBackStack()
                },
                viewModel = viewModel,
            )
        }

        composable(Routes.PERMISSIONS) {

            PermissionsScreen(
                onBack = {
                    navController.popBackStack()
                }
            )
        }

        composable(Routes.SETTINGS) {

            SettingsScreen(
                settingsRepository =
                    app.container.settingsRepository,
                onBack = {
                    navController.popBackStack()
                }
            )
        }

        composable(Routes.LOGS) {

            LogsScreen(
                onBack = {
                    navController.popBackStack()
                },
                viewModel = viewModel,
            )
        }
    }
}

private class DashboardViewModelFactory(
    private val app: AlfredApplication,
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(
        modelClass: Class<T>
    ): T {

        if (
            modelClass.isAssignableFrom(
                DashboardViewModel::class.java
            )
        ) {

            return DashboardViewModel(app) as T
        }

        throw IllegalArgumentException(
            "Unknown ViewModel class: ${modelClass.name}"
        )
    }
}
