package com.alfred.android

import android.app.Application
import com.alfred.android.agent.AppContainer
import com.alfred.android.util.Logger

class AlfredApplication : Application() {
    lateinit var container: AppContainer; private set
    override fun onCreate() {
        super.onCreate()
        Logger.verbose = BuildConfig.DEBUG
        container = AppContainer(this)
    }
}
