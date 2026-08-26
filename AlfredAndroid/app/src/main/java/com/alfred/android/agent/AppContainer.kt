package com.alfred.android.agent

import android.content.Context
import com.alfred.android.storage.SettingsRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob


class AppContainer(
    context: Context,
) {

    private val appContext =
        context.applicationContext


    val appScope =
        CoroutineScope(
            SupervisorJob()
            + Dispatchers.Default
        )


    val settingsRepository =
        SettingsRepository(
            appContext
        )


    val agent: AlfredAgent by lazy {

        AlfredAgent(
            appContext,
            appScope,
        )
    }
}
