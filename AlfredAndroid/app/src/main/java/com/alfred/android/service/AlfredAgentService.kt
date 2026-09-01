package com.alfred.android.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.alfred.android.AlfredApplication
import com.alfred.android.MainActivity
import com.alfred.android.R
import com.alfred.android.agent.AlfredAgent
import com.alfred.android.ai.AiService
import com.alfred.android.util.Constants
import com.alfred.android.voice.LocalCommandProcessor
import com.alfred.android.voice.VoiceAssistant
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class AlfredAgentService : Service() {

    private val serviceScope =
        CoroutineScope(
            SupervisorJob() +
                Dispatchers.Default
        )

    private lateinit var agent: AlfredAgent

    private var voiceAssistant: VoiceAssistant? = null

    private lateinit var commandProcessor: LocalCommandProcessor

    private var started = false

    override fun onCreate() {

        super.onCreate()

        val app =
            applicationContext as AlfredApplication

        agent =
            app.container.agent

        commandProcessor =
            LocalCommandProcessor(
                context = applicationContext,
                agent = agent,
                aiService = AiService()
            )

        createVoiceAssistant()

        ensureNotificationChannel()

        _serviceRunning.value = true
        _serviceStatus.value = "Starting ALFRED..."
    }

    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int
    ): Int {

        when (intent?.action) {

            ACTION_STOP -> {

                stopAgent()

                stopForeground(
                    STOP_FOREGROUND_REMOVE
                )

                stopSelf()

                return START_NOT_STICKY
            }

            ACTION_START_VOICE -> {

                startVoiceListening()

            }

            ACTION_STOP_VOICE -> {

                stopVoiceListening()

            }

            else -> {

                startForeground(
                    Constants.NOTIF_ID_CONNECTION,
                    buildNotification(
                        _serviceStatus.value
                    )
                )

                if (!started) {

                    started = true

                    startAgent()
                }
            }
        }

        return START_STICKY
    }

    private fun startAgent() {

        val app =
            applicationContext as AlfredApplication

        serviceScope.launch {

            app.container.settingsRepository
                .settings
                .collectLatest { settings ->

                    val hubUrl =
                        settings.hubUrl

                    if (hubUrl.isBlank()) {

                        updateServiceStatus(
                            "Hub not configured"
                        )

                        return@collectLatest
                    }

                    updateServiceStatus(
                        "Connecting to ALFRED Hub..."
                    )

                    try {

                        agent.start(
                            hubUrl
                        )

                    } catch (
                        error: Exception
                    ) {

                        updateServiceStatus(
                            "Connection error"
                        )
                    }
                }
        }

        serviceScope.launch {

            agent.connectionState
                .collectLatest { state ->

                    updateServiceStatus(
                        state.displayName
                    )
                }
        }
    }

    private fun createVoiceAssistant() {

        voiceAssistant =
            VoiceAssistant(
                context = applicationContext,

                onListeningChanged = { listening ->

                    _voiceListening.value =
                        listening

                    _voiceStatus.value =
                        if (listening) {
                            "Listening..."
                        } else {
                            "Ready"
                        }

                    updateVoiceNotification()
                },

                onResult = { text ->

                    _lastVoiceText.value =
                        text

                    _voiceStatus.value =
                        "Processing..."

                    updateVoiceNotification()

                    executeVoiceCommand(
                        text
                    )
                },

                onError = { error ->

                    _voiceListening.value =
                        false

                    _voiceStatus.value =
                        error

                    updateVoiceNotification()
                }
            )
    }

    private fun startVoiceListening() {

        if (!hasMicrophonePermission()) {

            _voiceStatus.value =
                "Microphone permission is not granted"

            updateVoiceNotification()

            return
        }

        _voiceStatus.value =
            "Starting microphone..."

        updateVoiceNotification()

        voiceAssistant?.startListening()
    }

    private fun stopVoiceListening() {

        voiceAssistant?.stopListening()

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Ready"

        updateVoiceNotification()
    }

    private fun executeVoiceCommand(
        text: String
    ) {

        serviceScope.launch {

            try {

                val response =
                    commandProcessor.execute(
                        spokenText = text
                    )

                _voiceStatus.value =
                    response

                updateVoiceNotification()

                voiceAssistant?.speak(
                    response
                )

            } catch (
                error: Exception
            ) {

                _voiceStatus.value =
                    "Command failed"

                updateVoiceNotification()
            }
        }
    }

    private fun hasMicrophonePermission(): Boolean {

        return checkSelfPermission(
            android.Manifest.permission.RECORD_AUDIO
        ) ==
            android.content.pm.PackageManager.PERMISSION_GRANTED
    }

    private fun stopAgent() {

        started = false

        stopVoiceListening()

        agent.stop()

        _serviceRunning.value =
            false

        _serviceStatus.value =
            "Stopped"
    }

    override fun onDestroy() {

        started = false

        voiceAssistant?.destroy()

        voiceAssistant =
            null

        agent.stop()

        serviceScope.cancel()

        _serviceRunning.value =
            false

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Stopped"

        super.onDestroy()
    }

    override fun onTaskRemoved(
        rootIntent: Intent?
    ) {

        if (
            getSharedPreferences(
                PREFS_NAME,
                Context.MODE_PRIVATE
            ).getBoolean(
                PREF_SERVICE_ENABLED,
                false
            )
        ) {

            val restartIntent =
                Intent(
                    applicationContext,
                    AlfredAgentService::class.java
                )

            if (
                Build.VERSION.SDK_INT >=
                Build.VERSION_CODES.O
            ) {

                applicationContext
                    .startForegroundService(
                        restartIntent
                    )

            } else {

                applicationContext
                    .startService(
                        restartIntent
                    )
            }
        }

        super.onTaskRemoved(
            rootIntent
        )
    }

    override fun onBind(
        intent: Intent?
    ): IBinder? {

        return null
    }

    private fun buildNotification(
        text: String
    ): Notification {

        val openIntent =
            Intent(
                this,
                MainActivity::class.java
            ).apply {

                flags =
                    Intent.FLAG_ACTIVITY_SINGLE_TOP
            }

        val openPendingIntent =
            PendingIntent.getActivity(
                this,
                0,
                openIntent,
                PendingIntent.FLAG_IMMUTABLE or
                    PendingIntent.FLAG_UPDATE_CURRENT
            )

        val stopIntent =
            Intent(
                this,
                AlfredAgentService::class.java
            ).apply {

                action =
                    ACTION_STOP
            }

        val stopPendingIntent =
            PendingIntent.getService(
                this,
                1,
                stopIntent,
                PendingIntent.FLAG_IMMUTABLE or
                    PendingIntent.FLAG_UPDATE_CURRENT
            )

        return NotificationCompat.Builder(
            this,
            Constants.NOTIF_CHANNEL_CONNECTION
        )
            .setContentTitle(
                "ALFRED"
            )
            .setContentText(
                text
            )
            .setSmallIcon(
                R.drawable.ic_stat_alfred
            )
            .setOngoing(
                true
            )
            .setContentIntent(
                openPendingIntent
            )
            .addAction(
                0,
                getString(
                    R.string.notif_action_stop
                ),
                stopPendingIntent
            )
            .setForegroundServiceBehavior(
                NotificationCompat
                    .FOREGROUND_SERVICE_IMMEDIATE
            )
            .build()
    }

    private fun updateNotification(
        text: String
    ) {

        runCatching {

            val manager =
                getSystemService(
                    NOTIFICATION_SERVICE
                ) as NotificationManager

            manager.notify(
                Constants.NOTIF_ID_CONNECTION,
                buildNotification(
                    text
                )
            )
        }
    }

    private fun updateServiceStatus(
        status: String
    ) {

        _serviceStatus.value =
            status

        updateNotification(
            status
        )
    }

    private fun updateVoiceNotification() {

        val voiceText =
            when {

                _voiceListening.value ->
                    "Listening for command..."

                _voiceStatus.value != "Ready" &&
                    _voiceStatus.value != "Stopped" ->
                    _voiceStatus.value

                else ->
                    _serviceStatus.value
            }

        updateNotification(
            voiceText
        )
    }

    private fun ensureNotificationChannel() {

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.O
        ) {

            val manager =
                getSystemService(
                    NOTIFICATION_SERVICE
                ) as NotificationManager

            val channel =
                NotificationChannel(
                    Constants.NOTIF_CHANNEL_CONNECTION,
                    "ALFRED Connection",
                    NotificationManager.IMPORTANCE_LOW
                ).apply {

                    description =
                        "Keeps ALFRED connected and running in the background"
                }

            manager.createNotificationChannel(
                channel
            )
        }
    }

    companion object {

        const val ACTION_STOP =
            "com.alfred.android.action.STOP"

        const val ACTION_START_VOICE =
            "com.alfred.android.action.START_VOICE"

        const val ACTION_STOP_VOICE =
            "com.alfred.android.action.STOP_VOICE"

        private const val PREFS_NAME =
            "alfred_service_prefs"

        private const val PREF_SERVICE_ENABLED =
            "service_enabled"

        private val _serviceRunning =
            MutableStateFlow(false)

        val serviceRunning:
            StateFlow<Boolean> =
            _serviceRunning.asStateFlow()

        private val _voiceListening =
            MutableStateFlow(false)

        val voiceListening:
            StateFlow<Boolean> =
            _voiceListening.asStateFlow()

        private val _lastVoiceText =
            MutableStateFlow("")

        val lastVoiceText:
            StateFlow<String> =
            _lastVoiceText.asStateFlow()

        private val _voiceStatus =
            MutableStateFlow("Ready")

        val voiceStatus:
            StateFlow<String> =
            _voiceStatus.asStateFlow()

        private val _serviceStatus =
            MutableStateFlow("Stopped")

        val serviceStatus:
            StateFlow<String> =
            _serviceStatus.asStateFlow()

        fun start(
            context: Context
        ) {

            context
                .getSharedPreferences(
                    PREFS_NAME,
                    Context.MODE_PRIVATE
                )
                .edit()
                .putBoolean(
                    PREF_SERVICE_ENABLED,
                    true
                )
                .apply()

            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java
                )

            if (
                Build.VERSION.SDK_INT >=
                Build.VERSION_CODES.O
            ) {

                context.startForegroundService(
                    intent
                )

            } else {

                context.startService(
                    intent
                )
            }
        }

        fun stop(
            context: Context
        ) {

            context
                .getSharedPreferences(
                    PREFS_NAME,
                    Context.MODE_PRIVATE
                )
                .edit()
                .putBoolean(
                    PREF_SERVICE_ENABLED,
                    false
                )
                .apply()

            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java
                ).apply {

                    action =
                        ACTION_STOP
                }

            if (
                Build.VERSION.SDK_INT >=
                Build.VERSION_CODES.O
            ) {

                context.startForegroundService(
                    intent
                )

            } else {

                context.startService(
                    intent
                )
            }
        }

        fun startVoice(
            context: Context
        ) {

            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java
                ).apply {

                    action =
                        ACTION_START_VOICE
                }

            if (
                Build.VERSION.SDK_INT >=
                Build.VERSION_CODES.O
            ) {

                context.startForegroundService(
                    intent
                )

            } else {

                context.startService(
                    intent
                )
            }
        }

        fun stopVoice(
            context: Context
        ) {

            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java
                ).apply {

                    action =
                        ACTION_STOP_VOICE
                }

            if (
                Build.VERSION.SDK_INT >=
                Build.VERSION_CODES.O
            ) {

                context.startForegroundService(
                    intent
                )

            } else {

                context.startService(
                    intent
                )
            }
        }
    }
}