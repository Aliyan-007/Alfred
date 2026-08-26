
package com.alfred.android.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.alfred.android.R
import com.alfred.android.agent.AlfredAgent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob


class AlfredForegroundService : Service() {

    companion object {

        const val CHANNEL_ID =
            "alfred_connection"

        const val NOTIFICATION_ID =
            1001

        const val EXTRA_HUB_URL =
            "hub_url"


        fun start(
            context: Context,
            hubUrl: String,
        ) {

            val intent =
                Intent(
                    context,
                    AlfredForegroundService::class.java,
                ).apply {

                    putExtra(
                        EXTRA_HUB_URL,
                        hubUrl,
                    )
                }


            if (
                Build.VERSION.SDK_INT
                >= Build.VERSION_CODES.O
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
            context: Context,
        ) {

            context.stopService(
                Intent(
                    context,
                    AlfredForegroundService::class.java,
                )
            )
        }
    }


    private val serviceScope =
        CoroutineScope(
            SupervisorJob()
            + Dispatchers.IO
        )


    private lateinit var agent: AlfredAgent


    override fun onCreate() {

        super.onCreate()

        createNotificationChannel()

        startForeground(
            NOTIFICATION_ID,
            createNotification(
                "Connecting to ALFRED Hub...",
            )
        )


        agent =
            AlfredAgent(
                applicationContext,
                serviceScope,
            )
    }


    override fun onStartCommand(
        intent: Intent?,
        flags: Int,
        startId: Int,
    ): Int {

        val hubUrl =
            intent?.getStringExtra(
                EXTRA_HUB_URL
            )


        if (
            !hubUrl.isNullOrBlank()
        ) {

            agent.start(
                hubUrl
            )


            updateNotification(
                "Connected to ALFRED Hub",
            )
        }


        return START_STICKY
    }


    override fun onDestroy() {

        agent.stop()

        super.onDestroy()
    }


    override fun onBind(
        intent: Intent?,
    ): IBinder? {

        return null
    }


    private fun createNotificationChannel() {

        if (
            Build.VERSION.SDK_INT
            >= Build.VERSION_CODES.O
        ) {

            val channel =
                NotificationChannel(
                    CHANNEL_ID,
                    "ALFRED Connection",
                    NotificationManager.IMPORTANCE_LOW,
                ).apply {

                    description =
                        "Keeps ALFRED connected to the Hub"
                }


            val manager =
                getSystemService(
                    NotificationManager::class.java
                )


            manager.createNotificationChannel(
                channel
            )
        }
    }


    private fun createNotification(
        text: String,
    ) =

        NotificationCompat.Builder(
            this,
            CHANNEL_ID,
        )
            .setContentTitle(
                "ALFRED"
            )
            .setContentText(
                text
            )
            .setSmallIcon(
                R.drawable.ic_launcher_foreground
            )
            .setOngoing(
                true
            )
            .build()


    private fun updateNotification(
        text: String,
    ) {

        val manager =
            getSystemService(
                NotificationManager::class.java
            )


        manager.notify(
            NOTIFICATION_ID,
            createNotification(
                text
            )
        )
    }
}
