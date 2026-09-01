package com.alfred.android.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
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
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class AlfredAgentService : Service() {

    companion object {

        const val ACTION_STOP =
            "com.alfred.android.action.STOP"

        const val ACTION_START_VOICE =
            "com.alfred.android.action.START_VOICE"

        const val ACTION_STOP_VOICE =
            "com.alfred.android.action.STOP_VOICE"

        const val ACTION_START =
            "com.alfred.android.action.START"

        private const val PREFS =
            "alfred_service_prefs"

        private const val PREF_VOICE_ENABLED =
            "voice_enabled"

        fun start(
            context: Context
        ) {

            val prefs =
                context.getSharedPreferences(
                    PREFS,
                    Context.MODE_PRIVATE
                )

            prefs.edit()
                .putBoolean(
                    "service_enabled",
                    true
                )
                .apply()

            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java
                ).apply {

                    action =
                        ACTION_START
                }

            startServiceInternal(
                context,
                intent
            )
        }

        fun startVoice(
            context: Context
        ) {

            val prefs =
                context.getSharedPreferences(
                    PREFS,
                    Context.MODE_PRIVATE
                )

            prefs.edit()
                .putBoolean(
                    PREF_VOICE_ENABLED,
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

            startServiceInternal(
                context,
                intent
            )
        }

        fun stopVoice(
            context: Context
        ) {

            context
                .getSharedPreferences(
                    PREFS,
                    Context.MODE_PRIVATE
                )
                .edit()
                .putBoolean(
                    PREF_VOICE_ENABLED,
                    false
                )
                .apply()

            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java
                ).apply {

                    action =
                        ACTION_STOP_VOICE
                }

            startServiceInternal(
                context,
                intent
            )
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

            startServiceInternal(
                context,
                intent
            )
        }

        private fun startServiceInternal(
            context: Context,
            intent: Intent
        ) {

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

    private val serviceScope =
        CoroutineScope(
            SupervisorJob() +
                Dispatchers.IO
        )

    private lateinit var agent: AlfredAgent

    private lateinit var aiService: AiService

    private lateinit var commandProcessor: LocalCommandProcessor

    private var voiceAssistant: VoiceAssistant? =
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

        aiService =
            AiService()

        commandProcessor =
            LocalCommandProcessor(
                context = applicationContext,
                agent = agent,
                aiService = aiService
            )

        ensureNotificationChannel()

        createVoiceAssistant()

        startForegroundCompat(
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

        when (
            intent?.action
        ) {

            ACTION_STOP -> {

                stopAgent()

                stopForeground(
                    STOP_FOREGROUND_REMOVE
                )

                stopSelf()

                return START_NOT_STICKY
            }

            ACTION_START_VOICE -> {

                startAgentIfNeeded()

                startVoiceAssistant()

                return START_STICKY
            }

            ACTION_STOP_VOICE -> {

                stopVoiceAssistant()

                return START_STICKY
            }

            else -> {

                startAgentIfNeeded()

                return START_STICKY
            }
        }
    }

    private fun startAgentIfNeeded() {

        if (started) {
            return
        }

        started = true

        startAgent()
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

                    if (
                        hubUrl.isBlank()
                    ) {

                        updateNotification(
                            if (voiceStarted) {
                                "Voice active • Hub not configured"
                            } else {
                                "Hub not configured"
                            }
                        )

                        return@collectLatest
                    }

                    updateNotification(
                        if (voiceStarted) {
                            "Voice active • Connecting..."
                        } else {
                            "Connecting to ALFRED Hub..."
                        }
                    )

                    try {

                        agent.start(
                            hubUrl
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

                    val prefix =
                        if (voiceStarted) {
                            "Voice active • "
                        } else {
                            ""
                        }

                    updateNotification(
                        prefix +
                            state.displayName
                    )
                }
        }
    }

    private fun createVoiceAssistant() {

        voiceAssistant =
            VoiceAssistant(

                context =
                    applicationContext,

                onListeningChanged = { listening ->

                    if (
                        listening
                    ) {

                        updateNotification(
                            "Listening for voice commands..."
                        )

                    } else if (
                        voiceStarted
                    ) {

                        updateNotification(
                            "Voice active"
                        )
                    }
                },

                onResult = { text ->

                    handleVoiceCommand(
                        text
                    )
                },

                onError = { error ->

                    if (
                        voiceStarted
                    ) {

                        updateNotification(
                            "Voice: $error"
                        )
                    }
                }
            )
    }

    private fun startVoiceAssistant() {

        if (voiceStarted) {
            return
        }

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.S
        ) {

            /*
             * The microphone foreground-service must be
             * promoted while Android permits microphone
             * foreground-service use.
             *
             * Dashboard should call startVoice() while
             * the Activity is visible and RECORD_AUDIO
             * permission is already granted.
             */

            promoteToMicrophoneForeground()
        }

        voiceStarted = true

        updateNotification(
            "Voice active"
        )

        voiceAssistant?.startListening(
            continuous = true
        )
    }

    private fun stopVoiceAssistant() {

        voiceStarted = false

        voiceAssistant?.stopListening()

        updateNotification(
            "Voice stopped"
        )

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.Q
        ) {

            startForegroundCompat(
                buildNotification(
                    "ALFRED running"
                ),
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            )
        }
    }

    private fun handleVoiceCommand(
        text: String
    ) {

        serviceScope.launch {

            updateNotification(
                "Processing: $text"
            )

            val response =
                try {

                    commandProcessor.execute(
                        spokenText = text
                    )

                } catch (
                    exception: Exception
                ) {

                    "Sir, command process nahi ho saki."
                }

            voiceAssistant?.speak(
                response
            )

            updateNotification(
                if (voiceStarted) {
                    "Voice active"
                } else {
                    "ALFRED running"
                }
            )
        }
    }

    private fun promoteToMicrophoneForeground() {

        if (
            Build.VERSION.SDK_INT <
            Build.VERSION_CODES.Q
        ) {
            return
        }

        val types =
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC or
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE

        startForegroundCompat(
            buildNotification(
                "Starting microphone..."
            ),
            types
        )
    }

    private fun startForegroundCompat(
        notification: Notification,
        foregroundServiceType: Int =
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
    ) {

        if (
            Build.VERSION.SDK_INT >=
            Build.VERSION_CODES.Q
        ) {

            startForeground(
                Constants.NOTIF_ID_CONNECTION,
                notification,
                foregroundServiceType
            )

        } else {

            startForeground(
                Constants.NOTIF_ID_CONNECTION,
                notification
            )
        }
    }

    private fun stopAgent() {

        started = false

        stopVoiceAssistant()

        agent.stop()

        getSharedPreferences(
            PREFS,
            Context.MODE_PRIVATE
        )
            .edit()
            .putBoolean(
                "service_enabled",
                false
            )
            .putBoolean(
                PREF_VOICE_ENABLED,
                false
            )
            .apply()
    }

    override fun onDestroy() {

        started = false

        voiceStarted = false

        voiceAssistant?.destroy()

        voiceAssistant = null

        agent.stop()

        serviceScope.cancel()

        super.onDestroy()
    }

    override fun onTaskRemoved(
        rootIntent: Intent?
    ) {

        /*
         * The service is START_STICKY.
         *
         * Do not automatically recreate microphone mode
         * from this callback. Android controls whether a
         * microphone foreground service may be started from
         * the background.
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

        val notificationManager =
            getSystemService(
                NOTIFICATION_SERVICE
            ) as NotificationManager

        notificationManager.notify(
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

            val notificationManager =
                getSystemService(
                    NOTIFICATION_SERVICE
                ) as NotificationManager

            val channel =
                NotificationChannel(
                    Constants.NOTIF_CHANNEL_CONNECTION,
                    "ALFRED",
                    NotificationManager.IMPORTANCE_LOW
                ).apply {

                    description =
                        "Keeps ALFRED running in the background"
                }

            notificationManager
                .createNotificationChannel(
                    channel
                )
        }
    }
}