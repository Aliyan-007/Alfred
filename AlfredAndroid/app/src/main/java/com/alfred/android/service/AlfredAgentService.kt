package com.alfred.android.service

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
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

    private val mainHandler =
        Handler(
            Looper.getMainLooper()
        )

    private lateinit var agent: AlfredAgent

    private lateinit var commandProcessor: LocalCommandProcessor

    private var voiceAssistant: VoiceAssistant? = null

    private var started = false

    private var voiceModeActive = false

    override fun onCreate() {

        super.onCreate()

        android.util.Log.i(
            TAG,
            "ALFRED service created"
        )

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

        ensureNotificationChannel()

        _serviceRunning.value = true

        _serviceStatus.value =
            "Starting ALFRED..."
    }

    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int
    ): Int {

        android.util.Log.i(
            TAG,
            "onStartCommand action=${intent?.action}"
        )

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

                android.util.Log.i(
                    TAG,
                    "Starting voice mode"
                )

                promoteToForeground(
                    microphone = true
                )

                if (!started) {

                    started = true

                    startAgent()
                }

                startVoiceListening()
            }

            ACTION_STOP_VOICE -> {

                android.util.Log.i(
                    TAG,
                    "Stopping voice mode"
                )

                stopVoiceListening()

                if (started) {

                    promoteToForeground(
                        microphone = false
                    )
                }
            }

            else -> {

                promoteToForeground(
                    microphone = false
                )

                if (!started) {

                    started = true

                    startAgent()
                }
            }
        }

        return START_STICKY
    }

    private fun promoteToForeground(
        microphone: Boolean
    ) {

        val notificationText =
            if (microphone) {
                "Voice assistant active"
            } else {
                _serviceStatus.value
            }

        val notification =
            buildNotification(
                notificationText
            )

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.Q
        ) {

            var serviceType =
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC

            if (microphone) {

                serviceType =
                    serviceType or
                        ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
            }

            startForeground(
                Constants.NOTIF_ID_CONNECTION,
                notification,
                serviceType
            )

        } else {

            startForeground(
                Constants.NOTIF_ID_CONNECTION,
                notification
            )
        }

        voiceModeActive =
            microphone

        android.util.Log.i(
            TAG,
            "Foreground mode updated. microphone=$microphone"
        )
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

                        android.util.Log.e(
                            TAG,
                            "Agent connection failed",
                            error
                        )

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

        mainHandler.post {

            if (
                voiceAssistant != null
            ) {
                return@post
            }

            android.util.Log.i(
                TAG,
                "Creating VoiceAssistant"
            )

            voiceAssistant =
                VoiceAssistant(

                    context =
                        applicationContext,

                    onListeningChanged = { listening ->

                        android.util.Log.i(
                            TAG,
                            "Voice listening=$listening"
                        )

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

                        android.util.Log.i(
                            TAG,
                            "VOICE RESULT: $text"
                        )

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

                        android.util.Log.e(
                            TAG,
                            "VOICE ERROR: $error"
                        )

                        _voiceListening.value =
                            false

                        _voiceStatus.value =
                            error

                        updateVoiceNotification()
                    }
                )
        }
    }

    private fun startVoiceListening() {

        if (!hasMicrophonePermission()) {

            android.util.Log.e(
                TAG,
                "Microphone permission missing"
            )

            _voiceStatus.value =
                "Microphone permission is not granted"

            updateVoiceNotification()

            return
        }

        createVoiceAssistant()

        _voiceStatus.value =
            "Starting microphone..."

        updateVoiceNotification()

        mainHandler.post {

            android.util.Log.i(
                TAG,
                "Calling VoiceAssistant.startListening()"
            )

            voiceAssistant?.startListening(
                continuous = false
            )
        }
    }

    private fun stopVoiceListening() {

        mainHandler.post {

            voiceAssistant?.stopListening()
        }

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Ready"

        updateVoiceNotification()
    }

    private fun executeVoiceCommand(
        text: String
    ) {

        android.util.Log.i(
            TAG,
            "EXECUTING COMMAND: $text"
        )

        serviceScope.launch {

            try {

                android.util.Log.i(
                    TAG,
                    "Sending command to LocalCommandProcessor"
                )

                val response =
                    commandProcessor.execute(
                        spokenText = text
                    )

                android.util.Log.i(
                    TAG,
                    "COMMAND RESPONSE: $response"
                )

                _voiceStatus.value =
                    response

                updateVoiceNotification()

                mainHandler.post {

                    voiceAssistant?.speak(
                        response
                    )
                }

            } catch (
                error: Exception
            ) {

                android.util.Log.e(
                    TAG,
                    "COMMAND EXECUTION FAILED",
                    error
                )

                _voiceStatus.value =
                    "Command failed: ${
                        error.message
                            ?: "Unknown error"
                    }"

                updateVoiceNotification()

                mainHandler.post {

                    voiceAssistant?.speak(
                        "Sorry Sir, command execute nahi ho saki."
                    )
                }
            }
        }
    }

    private fun hasMicrophonePermission(): Boolean {

        return checkSelfPermission(
            Manifest.permission.RECORD_AUDIO
        ) ==
            PackageManager.PERMISSION_GRANTED
    }

    private fun stopAgent() {

        started = false

        voiceModeActive = false

        stopVoiceListening()

        agent.stop()

        _serviceRunning.value =
            false

        _serviceStatus.value =
            "Stopped"
    }

    override fun onDestroy() {

        android.util.Log.i(
            TAG,
            "ALFRED service destroyed"
        )

        started = false

        voiceModeActive = false

        mainHandler.post {

            voiceAssistant?.destroy()

            voiceAssistant = null
        }

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
                    Intent.FLAG_ACTIVITY_SINGLE_TOP or
                        Intent.FLAG_ACTIVITY_CLEAR_TOP
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

        val title =
            if (voiceModeActive) {
                "ALFRED • Voice Active"
            } else {
                "ALFRED"
            }

        return NotificationCompat.Builder(
            this,
            Constants.NOTIF_CHANNEL_CONNECTION
        )
            .setContentTitle(
                title
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
            .setCategory(
                NotificationCompat.CATEGORY_SERVICE
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

        if (!voiceModeActive) {

            updateNotification(
                status
            )
        }
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

        private const val TAG =
            "ALFRED-Service"

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