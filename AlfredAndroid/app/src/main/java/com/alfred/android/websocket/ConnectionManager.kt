package com.alfred.android.websocket

import com.alfred.android.service.ConnectionState
import com.alfred.android.util.Logger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.min
import kotlin.math.pow

class ConnectionManager(
    private val transport: WsTransport,
    private val scope: CoroutineScope,
    private val appPingIntervalMs: Long = 25_000L,
    private val baseBackoffMs: Long = 1_000L,
    private val maxBackoffMs: Long = 60_000L,
) {
    private val tag = "ALFRED-WS"
    private val _state = MutableStateFlow(ConnectionState.DISCONNECTED)
    val state: StateFlow<ConnectionState> = _state.asStateFlow()

    private val _messages = MutableSharedFlow<String>(extraBufferCapacity = 32)
    val messages: SharedFlow<String> = _messages.asSharedFlow()

    private val running = AtomicBoolean(false)
    private var connectJob: Job? = null
    private var pingJob: Job? = null
    private var attempt = 0
    private var authFailure = false

    @Volatile var currentUrl: String = ""; private set

    fun connect(url: String) {
        if (url.isBlank()) { _state.value = ConnectionState.DISCONNECTED; return }
        currentUrl = url; authFailure = false
        if (running.compareAndSet(false, true)) launchLoop()
        else { stopInternal(); running.set(true); launchLoop() }
    }

    fun disconnect() { stopInternal(); _state.value = ConnectionState.DISCONNECTED }

    fun reportAuthenticationFailure() {
        authFailure = true; _state.value = ConnectionState.AUTHENTICATION_FAILED; stopInternal()
    }

    fun send(text: String): Boolean = transport.send(text)

    private fun launchLoop() {
        connectJob = scope.launch {
            attempt = 0
            while (running.get() && isActive) {
                if (authFailure) break
                _state.value = if (attempt == 0) ConnectionState.CONNECTING else ConnectionState.RECONNECTING
                try {
                    transport.connect(currentUrl).collect { event ->
                        when (event) {
                            is WsEvent.Open -> { attempt = 0; _state.value = ConnectionState.CONNECTED; Logger.i(tag, "connected"); startPing() }
                            is WsEvent.Message -> _messages.tryEmit(event.text)
                            is WsEvent.Closing, is WsEvent.Closed -> stopPing()
                            is WsEvent.Failure -> Logger.w(tag, "failure: ${event.throwable.message}")
                        }
                    }
                } catch (t: Throwable) { Logger.w(tag, "loop error: ${t.message}") }
                stopPing()
                if (!running.get() || authFailure) break
                _state.value = ConnectionState.RECONNECTING
                val d = backoff(attempt++)
                Logger.i(tag, "reconnect in ${d}ms")
                delay(d)
            }
            _state.value = if (authFailure) ConnectionState.AUTHENTICATION_FAILED else ConnectionState.DISCONNECTED
            running.set(false)
        }
    }

    private fun startPing() {
        stopPing()
        pingJob = scope.launch {
            while (isActive && _state.value == ConnectionState.CONNECTED) {
                delay(appPingIntervalMs)
                if (!transport.send("{\"type\":\"ping\"}")) break
            }
        }
    }
    private fun stopPing() { pingJob?.cancel(); pingJob = null }
    private fun stopInternal() { running.set(false); connectJob?.cancel(); connectJob = null; stopPing(); transport.cancel() }
    private fun backoff(attempt: Int): Long = min(baseBackoffMs * 2.0.pow(attempt.coerceAtMost(10)).toLong(), maxBackoffMs)
}
