package com.alfred.android.websocket

import com.alfred.android.util.Logger
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

interface WsTransport {
    fun connect(url: String): Flow<WsEvent>
    fun send(text: String): Boolean
    fun close(code: Int = 1000, reason: String? = null)
    fun cancel()
}

sealed class WsEvent {
    data class Open(val response: Response) : WsEvent()
    data class Message(val text: String) : WsEvent()
    data class Closing(val code: Int, val reason: String) : WsEvent()
    data class Closed(val code: Int, val reason: String) : WsEvent()
    data class Failure(val throwable: Throwable, val response: Response?) : WsEvent()
}

class OkHttpWsTransport(
    private val client: OkHttpClient = defaultClient(),
) : WsTransport {

    @Volatile private var socket: WebSocket? = null

    override fun connect(url: String): Flow<WsEvent> = callbackFlow {
        val request = Request.Builder().url(url).build()
        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) { socket = webSocket; trySend(WsEvent.Open(response)) }
            override fun onMessage(webSocket: WebSocket, text: String) { trySend(WsEvent.Message(text)) }
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) { trySend(WsEvent.Closing(code, reason)); webSocket.close(code, reason) }
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) { trySend(WsEvent.Closed(code, reason)); channel.close() }
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) { trySend(WsEvent.Failure(t, response)); channel.close(t) }
        }
        val ws = client.newWebSocket(request, listener)
        socket = ws
        awaitClose { ws.close(1000, "client closing"); socket = null }
    }

    override fun send(text: String): Boolean = socket?.send(text) ?: false
    override fun close(code: Int, reason: String?) { socket?.close(code, reason); socket = null }
    override fun cancel() { socket?.cancel(); socket = null }

    companion object {
        fun defaultClient(): OkHttpClient = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(0, TimeUnit.MILLISECONDS)
            .pingInterval(20, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()
    }
}
