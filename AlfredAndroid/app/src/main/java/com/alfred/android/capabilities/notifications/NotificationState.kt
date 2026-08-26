package com.alfred.android.capabilities.notifications

import java.util.concurrent.ConcurrentLinkedDeque

object NotificationState {
    @Volatile var listenerConnected: Boolean = false
    data class Event(val pkg: String, val title: String?, val text: String?, val postTime: Long)
    private const val MAX = 25
    private val recent = ConcurrentLinkedDeque<Event>()

    fun notePosted(pkg: String, title: String?, text: String?, postTime: Long) {
        recent.addFirst(Event(pkg, title, text, postTime))
        while (recent.size > MAX) recent.removeLast()
    }
    fun noteRemoved(pkg: String, postTime: Long) { recent.removeAll { it.pkg == pkg && it.postTime == postTime } }
    fun snapshot(): List<Event> = recent.toList()
}
