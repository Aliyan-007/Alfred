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
import com.alfred.android.util.Constants

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch


class AlfredAgentService : Service() {

    private val serviceScope =
        CoroutineScope(
            SupervisorJob() +
                Dispatchers.IO
        )

    private lateinit var agent: AlfredAgent

    private var started = false


    override fun onCreate() {

        super.onCreate()

        val app =
            applicationContext
                as AlfredApplication

        agent =
            app.container.agent

        ensureNotificationChannel()
    }


    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int,
    ): Int {

        if (
            intent?.action == ACTION_STOP
        ) {

            stopAgent()

            stopForeground(
                STOP_FOREGROUND_REMOVE
            )

            stopSelf()

            return START_NOT_STICKY
        }


        startForeground(
            Constants.NOTIF_ID_CONNECTION,
            buildNotification(
                "Starting ALFRED..."
            )
        )


        if (
            !started
        ) {

            started = true

            startAgent()
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


                    if (
                        hubUrl.isBlank()
                    ) {

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

                    updateNotification(
                        state.displayName
                    )
                }
        }
    }


    private fun stopAgent() {

        started = false

        agent.stop()


        getSharedPreferences(
            "alfred_service_prefs",
            Context.MODE_PRIVATE,
        )
            .edit()
            .putBoolean(
                "service_enabled",
                false,
            )
            .apply()
    }


    override fun onDestroy() {

        started = false

        agent.stop()

        serviceScope.cancel()

        super.onDestroy()
    }


    override fun onTaskRemoved(
        rootIntent: Intent?,
    ) {

        val restartIntent =
            Intent(
                applicationContext,
                AlfredAgentService::class.java,
            )


        if (
            Build.VERSION.SDK_INT
            >= Build.VERSION_CODES.O
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


        super.onTaskRemoved(
            rootIntent
        )
    }


    override fun onBind(
        intent: Intent?,
    ): IBinder? {

        return null
    }


    private fun buildNotification(
        text: String,
    ): Notification {

        val openIntent =
            Intent(
                this,
                MainActivity::class.java,
            ).apply {

                flags =
                    Intent.FLAG_ACTIVITY_SINGLE_TOP
            }


        val openPendingIntent =
            PendingIntent.getActivity(
                this,
                0,
                openIntent,
                PendingIntent.FLAG_IMMUTABLE
                    or
                    PendingIntent.FLAG_UPDATE_CURRENT,
            )


        val stopIntent =
            Intent(
                this,
                AlfredAgentService::class.java,
            ).apply {

                action =
                    ACTION_STOP
            }


        val stopPendingIntent =
            PendingIntent.getService(
                this,
                1,
                stopIntent,
                PendingIntent.FLAG_IMMUTABLE
                    or
                    PendingIntent.FLAG_UPDATE_CURRENT,
            )


        return NotificationCompat.Builder(
            this,
            Constants.NOTIF_CHANNEL_CONNECTION,
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
                stopPendingIntent,
            )
            .setForegroundServiceBehavior(
                NotificationCompat
                    .FOREGROUND_SERVICE_IMMEDIATE
            )
            .build()
    }


    private fun updateNotification(
        text: String,
    ) {

        val notificationManager =
            getSystemService(
                NOTIFICATION_SERVICE
            )
                as NotificationManager


        notificationManager.notify(
            Constants.NOTIF_ID_CONNECTION,
            buildNotification(
                text
            )
        )
    }


    private fun ensureNotificationChannel() {

        if (
            Build.VERSION.SDK_INT
            >= Build.VERSION_CODES.O
        ) {

            val notificationManager =
                getSystemService(
                    NOTIFICATION_SERVICE
                )
                    as NotificationManager


            val channel =
                NotificationChannel(
                    Constants.NOTIF_CHANNEL_CONNECTION,
                    "ALFRED Connection",
                    NotificationManager.IMPORTANCE_LOW,
                ).apply {

                    description =
                        "Keeps ALFRED connected to the Hub"
                }


            notificationManager
                .createNotificationChannel(
                    channel
                )
        }
    }


    companion object {

        const val ACTION_STOP =
            "com.alfred.android.action.STOP"


        fun start(
            context: Context,
        ) {

            context
                .getSharedPreferences(
                    "alfred_service_prefs",
                    Context.MODE_PRIVATE,
                )
                .edit()
                .putBoolean(
                    "service_enabled",
                    true,
                )
                .apply()


            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java,
                )


            if (
                Build.VERSION.SDK_INT
                >= Build.VERSION_CODES.O
            ) {

                context
                    .startForegroundService(
                        intent
                    )

            } else {

                context.startService(
                    intent
                )
            }
        }


        fun stop(
            context: Context,
        ) {

            val intent =
                Intent(
                    context,
                    AlfredAgentService::class.java,
                ).apply {

                    action =
                        ACTION_STOP
                }


            context.startService(
                intent
            )
        }
    }
}