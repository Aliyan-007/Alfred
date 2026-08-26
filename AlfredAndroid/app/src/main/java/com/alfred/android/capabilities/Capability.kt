package com.alfred.android.capabilities

import android.content.Context
import com.alfred.android.protocol.CapabilityWireInfo
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.ErrorCodes
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.JsonObject

interface Capability {
    val id: String
    val displayName: String
    val state: StateFlow<CapabilityState>
    fun refresh(context: Context)
    suspend fun handle(command: Command, context: Context): CommandResult
}

abstract class BaseCapability : Capability {
    private val _state = MutableStateFlow(CapabilityState.UNAVAILABLE)
    final override val state: StateFlow<CapabilityState> = _state.asStateFlow()
    protected fun setState(s: CapabilityState) { _state.value = s }
    fun toWireInfo() = CapabilityWireInfo(id, state.value.wireValue)
}

fun permissionRequiredError(capId: String, perm: String, msg: String = "Permission required: $perm") =
    CommandError(ErrorCodes.PERMISSION_REQUIRED, msg, capId, mapOf("permission" to perm))

fun invalidParametersError(msg: String = "Missing or invalid parameters") =
    CommandError(ErrorCodes.INVALID_PARAMETERS, msg)

fun unsupportedActionError(action: String) =
    CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Action '$action' is not supported")
