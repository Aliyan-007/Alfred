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
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
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
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class AlfredAgentService : Service() {

    companion object {

        const val ACTION_STOP =
            "com.alfred.android.action.STOP"

        private const val ACTION_START_VOICE =
            "com.alfred.android.action.START_VOICE"

        private const val ACTION_STOP_VOICE =
            "com.alfred.android.action.STOP_VOICE"

        fun start(
            context: Context
        ) {

            context
                .getSharedPreferences(
                    "alfred_service_prefs",
                    Context.MODE_PRIVATE
                )
                .edit()
                .putBoolean(
                    "service_enabled",
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

            context.startService(
                intent
            )
        }
    }

    private val serviceScope =
        CoroutineScope(
            SupervisorJob() +
                Dispatchers.IO
        )

    private lateinit var agent: AlfredAgent

    private var voiceAssistant: VoiceAssistant? =
        null

    private var commandProcessor:
        LocalCommandProcessor? =
        null

    private var started =
        false

    private var voiceStarted =
        false

    override fun onCreate() {

        super.onCreate()

        val app =
            applicationContext
                as AlfredApplication

        agent =
            app.container.agent

        commandProcessor =
            LocalCommandProcessor(
                context = applicationContext,
                agent = agent,
                aiService = AiService()
            )

        ensureNotificationChannel()

        startForeground(
            Constants.NOTIF_ID_CONNECTION,
            buildNotification(
                "Starting ALFRED..."
            )
        )
    }

    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int
    ): Int {

        when (intent?.action) {

            ACTION_STOP -> {

                stopEverything()

                return START_NOT_STICKY
            }

            ACTION_START_VOICE -> {

                startBackgroundVoice()

            }

            ACTION_STOP_VOICE -> {

                stopBackgroundVoice()

            }

            else -> {

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
            applicationContext
                as AlfredApplication

        serviceScope.launch {

            app.container.settingsRepository
                .settings
                .collectLatest { settings ->

                    val hubUrl =
                        settings.hubUrl

                    if (hubUrl.isBlank()) {

                        updateNotification(
                            "Hub not configured"
                        )

                        return@collectLatest
                    }

                    updateNotification(
                        "Connecting to ALFRED Hub..."
                    )

                    try {

                        agent.start(
                            hubUrl
                        )

                        updateNotification(
                            if (voiceStarted) {
                                "ALFRED connected • Voice active"
                            } else {
                                "ALFRED connected"
                            }
                        )

                    } catch (
                        error: Exception
                    ) {

                        updateNotification(
                            "Connection error"
                        )
                    }
                }
        }

        serviceScope.launch {

            agent.connectionState
                .collectLatest { state ->

                    val suffix =
                        if (voiceStarted) {
                            " • Voice active"
                        } else {
                            ""
                        }

                    updateNotification(
                        state.displayName +
                            suffix
                    )
                }
        }
    }

    private fun startBackgroundVoice() {

        if (voiceStarted) {
            return
        }

        if (
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {

            updateNotification(
                "Microphone permission required"
            )

            return
        }

        voiceStarted =
            true

        if (voiceAssistant == null) {

            voiceAssistant =
                VoiceAssistant(
                    context = applicationContext,

                    onListeningChanged = { listening ->

                        if (listening) {

                            updateNotification(
                                "Listening for voice command..."
                            )

                        } else {

                            updateNotification(
                                if (agent.connectionState.value
                                    .displayName.isNotBlank()
                                ) {
                                    agent.connectionState
                                        .value
                                        .displayName +
                                        " • Voice ready"
                                } else {
                                    "Voice ready"
                                }
                            )
                        }
                    },

                    onResult = { text ->

                        handleVoiceCommand(
                            text
                        )
                    },

                    onError = { error ->

                        updateNotification(
                            "Voice: $error"
                        )
                    }
                )
        }

        updateNotification(
            "ALFRED • Voice starting..."
        )

        voiceAssistant?.startListening()
    }

    private fun stopBackgroundVoice() {

        voiceStarted =
            false

        voiceAssistant?.stopListening()

        updateNotification(
            agent.connectionState
                .value
                .displayName
        )
    }

    private fun handleVoiceCommand(
        text: String
    ) {

        serviceScope.launch {

            val processor =
                commandProcessor
                    ?: return@launch

            updateNotification(
                "Processing voice command..."
            )

            try {

                val response =
                    processor.execute(
                        spokenText = text
                    )

                voiceAssistant?.speak(
                    response
                )

                updateNotification(
                    "ALFRED • Voice ready"
                )

                voiceStarted = true

                /*
                 * Start another recognition cycle.
                 *
                 * Android SpeechRecognizer performs
                 * individual recognition sessions rather
                 * than being a permanent microphone stream.
                 */
                launch {

                    kotlinx.coroutines.delay(
                        700
                    )

                    if (voiceStarted) {

                        voiceAssistant
                            ?.startListening()
                    }
                }

            } catch (
                error: Exception
            ) {

                updateNotification(
                    "Voice command failed"
                )
            }
        }
    }

    private fun stopEverything() {

        started =
            false

        voiceStarted =
            false

        voiceAssistant?.destroy()

        voiceAssistant =
            null

        commandProcessor =
            null

        agent.stop()

        getSharedPreferences(
            "alfred_service_prefs",
            Context.MODE_PRIVATE
        )
            .edit()
            .putBoolean(
                "service_enabled",
                false
            )
            .apply()

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.N
        ) {

            stopForeground(
                STOP_FOREGROUND_REMOVE
            )

        } else {

            @Suppress("DEPRECATION")
            stopForeground(
                true
            )
        }

        stopSelf()
    }

    override fun onTaskRemoved(
        rootIntent: Intent?
    ) {

        /*
         * START_STICKY handles normal service
         * recreation. Do not manually start another
         * copy here because that can create duplicate
         * service instances.
         */

        super.onTaskRemoved(
            rootIntent
        )
    }

    override fun onDestroy() {

        started =
            false

        voiceStarted =
            false

        voiceAssistant?.destroy()

        voiceAssistant =
            null

        agent.stop()

        serviceScope.cancel()

        super.onDestroy()
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
                "Stop",
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
}