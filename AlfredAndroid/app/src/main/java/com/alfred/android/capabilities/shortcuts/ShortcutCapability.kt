package com.alfred.android.capabilities.shortcuts

import android.content.Context
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.capabilities.apps.AppCapability
import com.alfred.android.capabilities.apps.UrlCapability
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonPrimitive

data class WorkflowStep(val type: String, val params: JsonObject) {
    fun toJson(): JsonObject = buildJsonObject { put("type", JsonPrimitive(type)); params.forEach { (k, v) -> put(k, v) } }
}

class ShortcutCapability(
    private val appCapability: AppCapability = AppCapability(),
    private val urlCapability: UrlCapability = UrlCapability(),
) : BaseCapability() {
    override val id = "shortcuts"
    override val displayName = "Shortcuts / Workflows"
    private val store = WorkflowStore()

    override fun refresh(context: Context) = setState(CapabilityState.AVAILABLE)

    override suspend fun handle(command: Command, context: Context): CommandResult =
        when (command.action.substringAfter('.', "run").lowercase()) {
            "list" -> listWorkflows(command.id)
            "define", "save" -> define(command)
            "delete" -> delete(command)
            "run" -> run(context, command)
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown shortcut action", id))
        }

    private fun listWorkflows(id: String) = CommandResult.success(id, buildJsonObject {
        put("workflows", JsonArray(store.all().map { (name, steps) ->
            buildJsonObject { put("name", JsonPrimitive(name)); put("steps", JsonArray(steps.map { it.toJson() })) }
        }))
    })

    private fun define(command: Command): CommandResult {
        val name = command.parameters["name"]?.jsonPrimitive?.contentOrNull?.trim()
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'name' required", id))
        val stepsArr = command.parameters["steps"]?.jsonArray
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'steps' array required", id))
        val steps = stepsArr.mapNotNull { el ->
            val obj = el as? JsonObject ?: return@mapNotNull null
            val type = obj["type"]?.jsonPrimitive?.contentOrNull ?: return@mapNotNull null
            WorkflowStep(type, obj)
        }
        if (steps.isEmpty()) return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "No valid steps", id))
        steps.firstOrNull { it.type !in ALLOWED }?.let {
            return CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Step type '${it.type}' not allowed. Allowed: $ALLOWED", id))
        }
        store.save(name, steps)
        return CommandResult.success(command.id, buildJsonObject { put("saved", JsonPrimitive(true)); put("name", JsonPrimitive(name)) })
    }

    private fun delete(command: Command): CommandResult {
        val name = command.parameters["name"]?.jsonPrimitive?.contentOrNull
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'name' required", id))
        store.delete(name)
        return CommandResult.success(command.id, buildJsonObject { put("deleted", JsonPrimitive(true)) })
    }

    private suspend fun run(context: Context, command: Command): CommandResult {
        val name = command.parameters["name"]?.jsonPrimitive?.contentOrNull
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'name' required", id))
        val workflow = store.get(name)
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "Workflow '$name' not found", id))
        val results = mutableListOf<JsonObject>()
        for ((i, step) in workflow.withIndex()) {
            val synthetic = Command(id = "${command.id}_$i", action = step.type, parameters = step.params)
            val res = when (step.type) {
                "open_app" -> appCapability.handle(synthetic, context)
                "open_url" -> urlCapability.handle(synthetic, context)
                else -> CommandResult.failure(synthetic.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, step.type, id))
            }
            results.add(buildJsonObject {
                put("step", JsonPrimitive(step.type)); put("success", JsonPrimitive(res.success))
                res.error?.let { put("error", JsonPrimitive(it.code)) }
            })
        }
        return CommandResult.success(command.id, buildJsonObject {
            put("workflow", JsonPrimitive(name)); put("results", JsonArray(results))
            put("completed", JsonPrimitive(results.all { it["success"]?.jsonPrimitive?.content?.toBoolean() == true }))
        })
    }

    companion object { private val ALLOWED = setOf("open_app", "open_url") }
}
