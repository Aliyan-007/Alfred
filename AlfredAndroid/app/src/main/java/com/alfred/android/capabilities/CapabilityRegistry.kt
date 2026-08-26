package com.alfred.android.capabilities

import android.content.Context
import com.alfred.android.protocol.CapabilityWireInfo
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.ErrorCodes
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow

class CapabilityRegistry {
    private val _capabilities = MutableStateFlow<List<Capability>>(emptyList())
    val capabilities: Flow<List<Capability>> = _capabilities

    private val byId: Map<String, Capability> get() = _capabilities.value.associateBy { it.id }

    fun register(c: Capability) {
        val cur = _capabilities.value.toMutableList()
        if (cur.none { it.id == c.id }) { cur.add(c); _capabilities.value = cur }
    }
    fun get(id: String): Capability? = byId[id]
    fun all(): List<Capability> = _capabilities.value
    fun refreshAll(context: Context) = _capabilities.value.forEach { it.refresh(context) }

    fun wireInfo(): List<CapabilityWireInfo> = _capabilities.value.map { cap ->
        (cap as? BaseCapability)?.toWireInfo() ?: CapabilityWireInfo(cap.id, cap.state.value.wireValue)
    }

    suspend fun dispatch(command: Command, context: Context): CommandResult {
        val capId = command.action.substringBefore('.').lowercase()
        val cap = byId[capId] ?: return CommandResult.failure(
            command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown capability '$capId'"))
        if (cap.state.value != CapabilityState.AVAILABLE) return CommandResult.failure(
            command.id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE,
                "Capability '$capId' is not available (${cap.state.value.wireValue})", capId))
        return try { cap.handle(command, context) }
        catch (t: Throwable) {
            CommandResult.failure(command.id, CommandError(ErrorCodes.INTERNAL_ERROR, t.message ?: "Internal error", capId))
        }
    }
}
