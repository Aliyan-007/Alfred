package com.alfred.android.capabilities.notifications

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.alfred.android.util.Logger

class AlfredNotificationListener : NotificationListenerService() {
    private val tag = "ALFRED-Notif"
    override fun onListenerConnected() { super.onListenerConnected(); NotificationState.listenerConnected = true; Logger.i(tag, "connected") }
    override fun onListenerDisconnected() { super.onListenerDisconnected(); NotificationState.listenerConnected = false }
    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn ?: return
        val title = sbn.notification?.extras?.getString(Notification.EXTRA_TITLE)
        val text = sbn.notification?.extras?.getString(Notification.EXTRA_TEXT)
        NotificationState.notePosted(sbn.packageName, title, text, sbn.postTime)
    }
    override fun onNotificationRemoved(sbn: StatusBarNotification?) { sbn?.let { NotificationState.noteRemoved(it.packageName, it.postTime) } }
}
