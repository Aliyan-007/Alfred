package com.alfred.android.agent

import android.content.Context
import com.alfred.android.capabilities.CapabilityProvider
import com.alfred.android.capabilities.CapabilityRegistry
import com.alfred.android.pairing.CredentialStore
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.PairRequest
import com.alfred.android.protocol.PairResponse
import com.alfred.android.protocol.RegistrationMessage
import com.alfred.android.protocol.RegistrationResponse
import com.alfred.android.registry.DeviceIdentity
import com.alfred.android.service.ConnectionState
import com.alfred.android.util.Constants
import com.alfred.android.util.DeviceInfo
import com.alfred.android.util.Logger
import com.alfred.android.websocket.ConnectionManager
import com.alfred.android.websocket.OkHttpWsTransport
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject

class AlfredAgent(
    private val context: Context,
    private val scope: CoroutineScope,
    val registry: CapabilityRegistry = CapabilityRegistry(),
    connectionManager: ConnectionManager? = null,
) {

    private val tag = "ALFRED-Agent"

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    private val cm = connectionManager ?: ConnectionManager(
        OkHttpWsTransport(),
        scope,
        appPingIntervalMs = Constants.DEFAULT_HEARTBEAT_INTERVAL_MS,
    )

    private val credentials = CredentialStore(context)
    private val identity = DeviceIdentity(context)

    private val _connectionState =
        MutableStateFlow(ConnectionState.DISCONNECTED)

    val connectionState: StateFlow<ConnectionState> =
        _connectionState.asStateFlow()

    private val _authenticated =
        MutableStateFlow(false)

    val authenticated: StateFlow<Boolean> =
        _authenticated.asStateFlow()

    private val _paired =
        MutableStateFlow(credentials.isPaired())

    val paired: StateFlow<Boolean> =
        _paired.asStateFlow()

    private val _lastCommand =
        MutableStateFlow<String?>(null)

    val lastCommand: StateFlow<String?> =
        _lastCommand.asStateFlow()

    private val _lastResult =
        MutableStateFlow<String?>(null)

    val lastResult: StateFlow<String?> =
        _lastResult.asStateFlow()

    private val _logs =
        MutableSharedFlow<LogEntry>(
            extraBufferCapacity = 128
        )

    val logs: SharedFlow<LogEntry> =
        _logs.asSharedFlow()

    private var collectorJob: Job? = null


    init {
        CapabilityProvider.populate(registry)
    }


    fun start(hubUrl: String) {

        collectorJob?.cancel()

        _authenticated.value = false

        cm.connect(hubUrl)

        collectorJob = scope.launch {

            launch {
                cm.state.collect {
                    onState(it)
                }
            }

            launch {
                cm.messages.collect {
                    onIncoming(it)
                }
            }

            launch {

                com.alfred.android.events.DeviceEvents.bus.collect { event ->

                    send(
                        json.encodeToString(
                            com.alfred.android.protocol.DeviceEvent.serializer(),
                            event
                        )
                    )
                }
            }
        }

        registry.refreshAll(context)
    }


    fun stop() {

        collectorJob?.cancel()

        collectorJob = null

        cm.disconnect()

        _authenticated.value = false
    }


    fun send(text: String): Boolean {
        return cm.send(text)
    }


    fun refreshCapabilities() {
        registry.refreshAll(context)
    }


    fun sendPairRequest(code: String): Boolean {

        if (
            _connectionState.value != ConnectionState.CONNECTED
        ) {

            log(
                "Pair requested but not connected",
                true
            )

            return false
        }

        send(
            json.encodeToString(
                PairRequest.serializer(),
                PairRequest(
                    code = code,
                    name = identity.deviceName
                )
            )
        )

        log("Pair request sent")

        return true
    }


    fun unpair() {

        credentials.clearToken()

        _paired.value = false

        _authenticated.value = false

        log("Pairing revoked")
    }


    private fun onState(
        state: ConnectionState
    ) {

        _connectionState.value = state

        if (
            state == ConnectionState.CONNECTED
        ) {

            sendRegistration()

        } else if (
            state == ConnectionState.DISCONNECTED ||
            state == ConnectionState.AUTHENTICATION_FAILED
        ) {

            _authenticated.value = false
        }
    }


    private fun sendRegistration() {

        val message = buildRegistrationMessage()

        send(
            json.encodeToString(
                RegistrationMessage.serializer(),
                message
            )
        )

        log(
            "Register as ${identity.deviceId}"
        )
    }


    private suspend fun onIncoming(
        raw: String
    ) {

        val type = peekType(raw)

        if (type == null) {

            log(
                "Malformed message",
                true
            )

            return
        }

        when (type) {

            "registered" -> {

                runCatching {

                    json.decodeFromString(
                        RegistrationResponse.serializer(),
                        raw
                    )

                }.onSuccess { response ->

                    if (response.success) {

                        _authenticated.value = true

                        log("Registered")

                    } else {

                        cm.reportAuthenticationFailure()

                        log(
                            "Rejected: ${response.reason}",
                            true
                        )
                    }

                }.onFailure {

                    _authenticated.value = true

                    log("Registered (ack)")
                }
            }


            "register_rejected",
            "authentication_failed" -> {

                credentials.clearToken()

                _authenticated.value = false

                cm.reportAuthenticationFailure()

                log(
                    "Authentication failed",
                    true
                )
            }


            "pair_response" -> {

                runCatching {

                    json.decodeFromString(
                        PairResponse.serializer(),
                        raw
                    )

                }.getOrNull()?.let { response ->

                    if (
                        response.success &&
                        response.authToken != null
                    ) {

                        credentials.saveToken(
                            response.authToken
                        )

                        _paired.value = true

                        log("Paired")

                        sendRegistration()

                    } else {

                        log(
                            "Pair failed: ${response.reason}",
                            true
                        )

                        cm.reportAuthenticationFailure()
                    }
                }
            }


            "pong" -> {
                // Hub heartbeat response.
            }


            "command" -> {

                handleCommand(raw)
            }


            else -> {

                log(
                    "Unknown message type: $type",
                    true
                )
            }
        }
    }


    private suspend fun handleCommand(
        raw: String
    ) {

        val command = runCatching {

            val root =
                Json.parseToJsonElement(raw)
                    .jsonObject

            val commandElement =
                root["command"]
                    ?: throw IllegalArgumentException(
                        "Missing command object"
                    )

            json.decodeFromJsonElement(
                Command.serializer(),
                commandElement
            )

        }.getOrElse { error ->

            log(
                "Bad command: ${error.message}",
                true
            )

            return
        }


        if (
            !command.device.isNullOrBlank() &&
            command.device != identity.deviceId
        ) {

            log(
                "Command is for another device: ${command.device}"
            )

            return
        }


        log(
            "Executing command: ${command.action}"
        )

        _lastCommand.value =
            command.action


        val result = try {

            registry.dispatch(
                command,
                context
            )

        } catch (error: Exception) {

            log(
                "Command execution error: ${error.message}",
                true
            )

            CommandResult(
                id = command.id,
                success = false,
                error =
                    com.alfred.android.protocol.CommandError(
                        code = "execution_error",
                        message =
                            error.message
                                ?: "Unknown error",
                    ),
            )
        }


        _lastResult.value =

            if (result.success) {
                "success"
            } else {
                "error:${result.error?.code}"
            }


        val response =
            json.encodeToString(
                CommandResult.serializer(),
                result
            )


        log(
            "Sending command result: ${command.id}"
        )


        val sent =
            send(response)


        if (!sent) {

            log(
                "Failed to send command result",
                true
            )
        }


        log(
            "Result ${command.id}: ${
                if (result.success) {
                    "ok"
                } else {
                    result.error?.code
                }
            }"
        )
    }


    fun buildRegistrationMessage():
        RegistrationMessage {

        val packageInfo =
            context.packageManager.getPackageInfo(
                context.packageName,
                0
            )

        return RegistrationMessage(
            deviceId = identity.deviceId,
            name = identity.deviceName,
            capabilities = registry.wireInfo(),
            appVersion =
                packageInfo.versionName ?: "0.1.0",
            androidVersion =
                DeviceInfo.androidVersion,
            manufacturer =
                DeviceInfo.manufacturer,
            model =
                DeviceInfo.model,
            authToken =
                credentials.getToken(),
        )
    }


    private fun peekType(
        raw: String
    ): String? {

        return runCatching {

            Json.parseToJsonElement(raw)
                .jsonObject["type"]
                ?.toString()
                ?.trim('"')

        }.getOrNull()
    }


    private fun log(
        message: String,
        error: Boolean = false
    ) {

        Logger.d(tag) {
            message
        }

        _logs.tryEmit(
            LogEntry(
                ts = System.currentTimeMillis(),

                level =
                    if (error) {
                        LogLevel.ERROR
                    } else {
                        LogLevel.INFO
                    },

                message = message
            )
        )
    }
}


enum class LogLevel {
    INFO,
    WARN,
    ERROR
}


data class LogEntry(
    val ts: Long,
    val level: LogLevel,
    val message: String,
)