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

        val app =
            applicationContext as AlfredApplication

        /*
         * Use the single AlfredAgent instance owned by
         * the application container.
         */
        agent =
            app.container.agent

        /*
         * AI + local command processing belongs to
         * the background service, NOT DashboardViewModel.
         */
        commandProcessor =
            LocalCommandProcessor(
                context = applicationContext,
                agent = agent,
                aiService = AiService()
            )

        ensureNotificationChannel()

        /*
         * The service has been created, but we still
         * make sure the notification is shown quickly
         * when the service is started.
         */
        _serviceRunning.value = true

        _serviceStatus.value =
            "Starting ALFRED..."
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

                /*
                 * Make sure the service is foreground
                 * BEFORE doing microphone work.
                 */
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

                stopVoiceListening()

                /*
                 * Once voice mode stops, return the
                 * foreground service to normal data-sync mode.
                 */
                if (started) {

                    promoteToForeground(
                        microphone = false
                    )
                }
            }

            else -> {

                /*
                 * Normal ALFRED background mode.
                 */
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

    /**
     * Promotes ALFRED to the correct foreground-service type.
     *
     * Normal mode:
     *     DATA_SYNC
     *
     * Voice mode:
     *     DATA_SYNC + MICROPHONE
     */
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
    }

    /**
     * Starts connection to the ALFRED Hub.
     */
    private fun startAgent() {

        val app =
            applicationContext as AlfredApplication

        /*
         * Observe settings and connect to the Hub.
         */
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

        /*
         * Keep notification status synchronized
         * with the actual agent connection.
         */
        serviceScope.launch {

            agent.connectionState
                .collectLatest { state ->

                    updateServiceStatus(
                        state.displayName
                    )
                }
        }
    }

    /**
     * Creates the VoiceAssistant on the main thread.
     *
     * SpeechRecognizer and TextToSpeech are UI/main-thread
     * oriented Android APIs.
     */
    private fun createVoiceAssistant() {

        mainHandler.post {

            if (
                voiceAssistant != null
            ) {
                return@post
            }

            voiceAssistant =
                VoiceAssistant(

                    context =
                        applicationContext,

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
    }

    /**
     * Starts microphone recognition.
     */
    private fun startVoiceListening() {

        if (!hasMicrophonePermission()) {

            _voiceStatus.value =
                "Microphone permission is not granted"

            updateVoiceNotification()

            return
        }

        /*
         * VoiceAssistant is created on the main thread.
         */
        createVoiceAssistant()

        _voiceStatus.value =
            "Starting microphone..."

        updateVoiceNotification()

        mainHandler.post {

            voiceAssistant?.startListening()
        }
    }

    /**
     * Stops the current recognition session.
     */
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

    /**
     * Processes the spoken command through:
     *
     * Voice
     *   ↓
     * LocalCommandProcessor
     *   ↓
     * AiService
     *   ↓
     * AiCommandMapper
     *   ↓
     * Android action
     */
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

                /*
                 * TTS must run on the main thread.
                 */
                mainHandler.post {

                    voiceAssistant?.speak(
                        response
                    )
                }

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
            Manifest.permission.RECORD_AUDIO
        ) ==
            PackageManager.PERMISSION_GRANTED
    }

    /**
     * Completely stops ALFRED.
     */
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

        started = false

        voiceModeActive = false

        /*
         * Destroy SpeechRecognizer/TTS on the main thread.
         */
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

    /**
     * If Android removes ALFRED's task from Recents,
     * do NOT immediately restart microphone mode.
     *
     * The foreground service itself is what keeps ALFRED
     * alive. We only allow Android/service lifecycle to
     * handle recovery.
     */
    override fun onTaskRemoved(
        rootIntent: Intent?
    ) {

        /*
         * Intentionally no manual restart here.
         *
         * This avoids creating background-start violations
         * on newer Android versions.
         */

        super.onTaskRemoved(
            rootIntent
        )
    }

    override fun onBind(
        intent: Intent?
    ): IBinder? {

        return null
    }

    /**
     * Creates the persistent ALFRED notification.
     */
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

        /*
         * Don't replace a voice-specific notification
         * with a generic connection status.
         */
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

    /**
     * Creates ALFRED's persistent notification channel.
     */
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

        /**
         * Starts normal background ALFRED.
         */
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

        /**
         * Completely stops ALFRED.
         */
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

        /**
         * Starts background voice mode.
         *
         * This also starts the service if it isn't
         * already running.
         */
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

        /**
         * Stops voice recognition but leaves
         * ALFRED itself running.
         */
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