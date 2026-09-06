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
import android.util.Log
import androidx.core.app.NotificationCompat
import com.alfred.android.AlfredApplication
import com.alfred.android.MainActivity
import com.alfred.android.R
import com.alfred.android.agent.AlfredAgent
import com.alfred.android.ai.AiService
import com.alfred.android.util.Constants
import com.alfred.android.voice.LocalCommandProcessor
import com.alfred.android.voice.VoiceAssistant
import com.alfred.android.voice.wake.OpenWakeWordEngineAdapter
import com.alfred.android.voice.wake.WakeWordEngine
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

    private var wakeWordEngine: WakeWordEngine? = null

    private var started = false

    private var voiceModeActive = false

    @Volatile
    private var conversationActive = false

    private var conversationTimeoutRunnable:
        Runnable? = null

    // ---------------------------------------------------------------------
    // SERVICE CREATION
    // ---------------------------------------------------------------------

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
         * AI + local command processing belongs to the
         * background service.
         */
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

        updateNotification(
            _serviceStatus.value
        )
    }

    // ---------------------------------------------------------------------
    // SERVICE COMMANDS
    // ---------------------------------------------------------------------

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
                 * The service must be promoted to microphone
                 * foreground mode BEFORE microphone work starts.
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
                 * Return to normal data-sync foreground mode.
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

    // ---------------------------------------------------------------------
    // FOREGROUND SERVICE
    // ---------------------------------------------------------------------

    /**
     * Promotes ALFRED to the correct foreground-service type.
     *
     * Normal:
     *     DATA_SYNC
     *
     * Voice:
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
                ServiceInfo
                    .FOREGROUND_SERVICE_TYPE_DATA_SYNC

            if (microphone) {

                serviceType =
                    serviceType or
                        ServiceInfo
                            .FOREGROUND_SERVICE_TYPE_MICROPHONE
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

    // ---------------------------------------------------------------------
    // ALFRED AGENT
    // ---------------------------------------------------------------------

    /**
     * Starts connection to the ALFRED Hub.
     */
    private fun startAgent() {

        val app =
            applicationContext as AlfredApplication

        serviceScope.launch {

            app.container
                .settingsRepository
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

    // ---------------------------------------------------------------------
    // VOICE CREATION
    // ---------------------------------------------------------------------

    /**
     * Creates the local wake engine and VoiceAssistant.
     *
     * Both are owned by this service.
     */
    private fun createVoiceAssistant() {

        mainHandler.post {

            if (voiceAssistant != null) {
                return@post
            }

            val wakeEngine =
                OpenWakeWordEngineAdapter(
                    context = applicationContext,

                    onWakeWordDetected = {
                        mainHandler.post {
                            handleWakeWordDetected()
                        }
                    },

                    onError = { error ->
                        mainHandler.post {
                            handleVoiceError(
                                error
                            )
                        }
                    }
                )

            wakeWordEngine =
                wakeEngine

            voiceAssistant =
                VoiceAssistant(

                    context =
                        applicationContext,

                    wakeWordEngine =
                        wakeEngine,

                    onListeningChanged = { listening ->

                        _voiceListening.value =
                            listening

                        if (
                            listening &&
                            conversationActive
                        ) {

                            _voiceStatus.value =
                                "Listening for command"

                        } else if (
                            !listening &&
                            conversationActive &&
                            _voiceStatus.value ==
                                "Listening for command"
                        ) {

                            _voiceStatus.value =
                                "Processing..."
                        }

                        updateVoiceNotification()
                    },

                    onResult = { text ->

                        mainHandler.post {

                            if (
                                !conversationActive
                            ) {
                                return@post
                            }

                            cancelConversationTimeout()

                            _lastVoiceText.value =
                                text

                            _voiceListening.value =
                                false

                            _voiceStatus.value =
                                "Processing..."

                            updateVoiceNotification()

                            executeVoiceCommand(
                                text
                            )
                        }
                    },

                    onError = { error ->

                        mainHandler.post {
                            handleVoiceError(
                                error
                            )
                        }
                    },

                    onWakeStateChanged = { active ->

                        mainHandler.post {

                            if (!voiceModeActive) {
                                return@post
                            }

                            if (
                                active &&
                                !conversationActive
                            ) {

                                _voiceListening.value =
                                    false

                                _voiceStatus.value =
                                    "Waiting for Alfred"

                            } else if (
                                !active &&
                                !conversationActive
                            ) {

                                _voiceStatus.value =
                                    "Ready"
                            }

                            updateVoiceNotification()
                        }
                    }
                )
        }
    }

    // ---------------------------------------------------------------------
    // START VOICE
    // ---------------------------------------------------------------------

    /**
     * Starts the complete background voice system.
     *
     * At this point ALFRED is NOT listening for a command.
     *
     * It is waiting locally for:
     *
     *     Alfred
     */
    private fun startVoiceListening() {

        if (!hasMicrophonePermission()) {

            _voiceStatus.value =
                "Microphone permission is not granted"

            updateVoiceNotification()

            return
        }

        createVoiceAssistant()

        conversationActive =
            false

        cancelConversationTimeout()

        _voiceStatus.value =
            "Starting wake-word engine..."

        updateVoiceNotification()

        mainHandler.post {

            if (!voiceModeActive) {
                return@post
            }

            voiceAssistant
                ?.startWakeWordListening()
        }
    }

    // ---------------------------------------------------------------------
    // WAKE WORD
    // ---------------------------------------------------------------------

    /**
     * Called when the real local Alfred wake-word model
     * detects "Alfred".
     */
    private fun handleWakeWordDetected() {

        if (!voiceModeActive) {
            return
        }

        if (conversationActive) {
            Log.i(
                TAG,
                "Ignoring duplicate wake-word detection"
            )

            return
        }

        conversationActive =
            true

        cancelConversationTimeout()

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Alfred detected"

        updateVoiceNotification()

        /*
         * WakeWordEngine already stops itself after detection.
         * Calling stop again is harmless and provides an extra
         * safety barrier.
         */
        wakeWordEngine?.stop()

        /*
         * ALFRED acknowledges the wake word first.
         */
        mainHandler.post {

            voiceAssistant?.speak(
                "Yes, Sir."
            ) {

                if (
                    !voiceModeActive ||
                    !conversationActive
                ) {
                    return@speak
                }

                _voiceStatus.value =
                    "Listening for command"

                updateVoiceNotification()

                voiceAssistant
                    ?.startCommandListening()

                armConversationTimeout()
            }
        }
    }

    // ---------------------------------------------------------------------
    // COMMAND PROCESSING
    // ---------------------------------------------------------------------

    /**
     * Executes one recognized command.
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

                mainHandler.post {

                    if (
                        !voiceModeActive ||
                        !conversationActive
                    ) {
                        return@post
                    }

                    _voiceStatus.value =
                        "Speaking..."

                    updateVoiceNotification()

                    voiceAssistant?.speak(
                        response
                    ) {

                        if (
                            !voiceModeActive ||
                            !conversationActive
                        ) {
                            return@speak
                        }

                        /*
                         * Command completed.
                         *
                         * ALFRED now returns to command listening
                         * instead of immediately returning to the
                         * wake-word detector.
                         *
                         * This creates a natural conversation:
                         *
                         * Alfred
                         *   -> Yes, Sir
                         *   -> command
                         *   -> answer
                         *   -> next command
                         *   -> ...
                         */
                        _voiceStatus.value =
                            "Listening for command"

                        updateVoiceNotification()

                        voiceAssistant
                            ?.startCommandListening()

                        armConversationTimeout()
                    }
                }

            } catch (
                error: Exception
            ) {

                mainHandler.post {

                    if (
                        !voiceModeActive ||
                        !conversationActive
                    ) {
                        return@post
                    }

                    Log.e(
                        TAG,
                        "Voice command failed",
                        error
                    )

                    _voiceStatus.value =
                        "Command failed"

                    updateVoiceNotification()

                    voiceAssistant?.speak(
                        "Sorry, Sir. I could not complete that command."
                    ) {

                        if (
                            !voiceModeActive ||
                            !conversationActive
                        ) {
                            return@speak
                        }

                        _voiceStatus.value =
                            "Listening for command"

                        updateVoiceNotification()

                        voiceAssistant
                            ?.startCommandListening()

                        armConversationTimeout()
                    }
                }
            }
        }
    }

    // ---------------------------------------------------------------------
    // ERROR HANDLING
    // ---------------------------------------------------------------------

    /**
     * Handles both wake-engine and speech-recognition errors.
     */
    private fun handleVoiceError(
        error: String
    ) {

        if (!voiceModeActive) {
            return
        }

        Log.e(
            TAG,
            "Voice error: $error"
        )

        _voiceListening.value =
            false

        _voiceStatus.value =
            error

        updateVoiceNotification()

        /*
         * If we are inside a conversation, give the user a chance
         * to speak again instead of getting stuck.
         */
        if (conversationActive) {

            voiceAssistant?.speak(
                "Sorry, Sir. Please try again."
            ) {

                if (
                    !voiceModeActive ||
                    !conversationActive
                ) {
                    return@speak
                }

                _voiceStatus.value =
                    "Listening for command"

                updateVoiceNotification()

                voiceAssistant
                    ?.startCommandListening()

                armConversationTimeout()
            }

        } else {

            /*
             * Wake-engine error while waiting for Alfred.
             *
             * We leave the service alive but clearly report the
             * problem instead of pretending wake detection is active.
             */
            conversationActive =
                false

            cancelConversationTimeout()
        }
    }

    // ---------------------------------------------------------------------
    // CONVERSATION TIMEOUT
    // ---------------------------------------------------------------------

    /**
     * Gives the user 18 seconds to continue the conversation.
     *
     * If no command is received, ALFRED returns to wake-word mode.
     */
    private fun armConversationTimeout() {

        cancelConversationTimeout()

        val runnable =
            Runnable {

                if (
                    !voiceModeActive ||
                    !conversationActive
                ) {
                    return@Runnable
                }

                Log.i(
                    TAG,
                    "Conversation timeout reached"
                )

                endConversationAndResumeWake()
            }

        conversationTimeoutRunnable =
            runnable

        mainHandler.postDelayed(
            runnable,
            CONVERSATION_TIMEOUT_MS
        )
    }

    private fun cancelConversationTimeout() {

        conversationTimeoutRunnable
            ?.let { runnable ->
                mainHandler.removeCallbacks(
                    runnable
                )
            }

        conversationTimeoutRunnable =
            null
    }

    /**
     * Ends the active conversation and returns to local
     * wake-word monitoring.
     */
    private fun endConversationAndResumeWake() {

        if (!voiceModeActive) {
            return
        }

        cancelConversationTimeout()

        conversationActive =
            false

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Waiting for Alfred"

        updateVoiceNotification()

        mainHandler.post {

            if (!voiceModeActive) {
                return@post
            }

            voiceAssistant
                ?.stopListening()

            /*
             * Small delay prevents the microphone transition from
             * immediately colliding with SpeechRecognizer cleanup.
             */
            mainHandler.postDelayed(
                {

                    if (
                        !voiceModeActive ||
                        conversationActive
                    ) {
                        return@postDelayed
                    }

                    _voiceStatus.value =
                        "Waiting for Alfred"

                    updateVoiceNotification()

                    voiceAssistant
                        ?.startWakeWordListening()
                },
                WAKE_RESTART_DELAY_MS
            )
        }
    }

    // ---------------------------------------------------------------------
    // STOP VOICE
    // ---------------------------------------------------------------------

    /**
     * Stops voice mode but leaves ALFRED itself running.
     */
    private fun stopVoiceListening() {

        cancelConversationTimeout()

        conversationActive =
            false

        mainHandler.post {

            voiceAssistant
                ?.stopListening()
        }

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Ready"

        updateVoiceNotification()
    }

    // ---------------------------------------------------------------------
    // STOP SERVICE
    // ---------------------------------------------------------------------

    /**
     * Completely stops ALFRED.
     */
    private fun stopAgent() {

        started =
            false

        voiceModeActive =
            false

        conversationActive =
            false

        cancelConversationTimeout()

        mainHandler.post {

            voiceAssistant
                ?.stopListening()
        }

        agent.stop()

        _serviceRunning.value =
            false

        _serviceStatus.value =
            "Stopped"

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Stopped"
    }

    // ---------------------------------------------------------------------
    // SERVICE DESTROY
    // ---------------------------------------------------------------------

    override fun onDestroy() {

        started =
            false

        voiceModeActive =
            false

        conversationActive =
            false

        cancelConversationTimeout()

        /*
         * Destroy VoiceAssistant on the main thread.
         *
         * VoiceAssistant stops the wake engine but DOES NOT release it.
         */
        mainHandler.post {

            voiceAssistant
                ?.destroy()

            voiceAssistant =
                null
        }

        /*
         * The SERVICE owns the wake engine lifetime.
         *
         * Therefore release it here exactly once.
         */
        wakeWordEngine?.release()

        wakeWordEngine =
            null

        agent.stop()

        serviceScope.cancel()

        _serviceRunning.value =
            false

        _voiceListening.value =
            false

        _voiceStatus.value =
            "Stopped"

        mainHandler.removeCallbacksAndMessages(
            null
        )

        super.onDestroy()
    }

    // ---------------------------------------------------------------------
    // TASK REMOVAL
    // ---------------------------------------------------------------------

    /**
     * Do NOT manually restart microphone mode when the Activity
     * disappears from Recents.
     *
     * This avoids background microphone-start violations on
     * newer Android versions.
     */
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

    // ---------------------------------------------------------------------
    // PERMISSIONS
    // ---------------------------------------------------------------------

    private fun hasMicrophonePermission(): Boolean {

        return checkSelfPermission(
            Manifest.permission.RECORD_AUDIO
        ) ==
            PackageManager.PERMISSION_GRANTED
    }

    // ---------------------------------------------------------------------
    // NOTIFICATION
    // ---------------------------------------------------------------------

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
         * Do not replace a voice-specific notification with
         * generic Hub connection status.
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

                _voiceStatus.value ==
                    "Waiting for Alfred" ->
                    "Waiting for wake word: Alfred"

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

    // ---------------------------------------------------------------------
    // STATIC STATE
    // ---------------------------------------------------------------------

    companion object {

        private const val TAG =
            "ALFRED-Service"

        private const val PREFS_NAME =
            "alfred_service_prefs"

        private const val PREF_SERVICE_ENABLED =
            "service_enabled"

        /**
         * Maximum time to remain inside one conversation
         * without another command.
         */
        private const val CONVERSATION_TIMEOUT_MS =
            18_000L

        /**
         * Delay before restarting local wake detection after
         * SpeechRecognizer has been destroyed.
         */
        private const val WAKE_RESTART_DELAY_MS =
            350L

        const val ACTION_STOP =
            "com.alfred.android.action.STOP"

        const val ACTION_START_VOICE =
            "com.alfred.android.action.START_VOICE"

        const val ACTION_STOP_VOICE =
            "com.alfred.android.action.STOP_VOICE"

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
         * The service enters microphone foreground mode and
         * starts local wake-word detection.
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
         * Stops voice recognition but leaves ALFRED itself running.
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