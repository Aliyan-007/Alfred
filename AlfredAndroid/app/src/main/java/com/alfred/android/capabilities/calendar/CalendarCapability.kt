package com.alfred.android.capabilities.calendar

import android.Manifest
import android.content.ContentUris
import android.content.Context
import android.content.pm.PackageManager
import android.provider.CalendarContract
import androidx.core.content.ContextCompat
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.ErrorCodes
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import java.util.TimeZone

class CalendarCapability : BaseCapability() {
    override val id = "calendar"
    override val displayName = "Calendar"

    override fun refresh(context: Context) {
        val read = has(context, Manifest.permission.READ_CALENDAR)
        val write = has(context, Manifest.permission.WRITE_CALENDAR)
        setState(if (read && write) CapabilityState.AVAILABLE else CapabilityState.PERMISSION_REQUIRED)
    }

    override suspend fun handle(command: Command, context: Context): CommandResult =
        when (command.action.substringAfter('.', "list").lowercase()) {
            "list", "list_upcoming" -> list(context, command)
            "search" -> search(context, command)
            "create" -> create(context, command)
            "reschedule", "update", "cancel", "delete" -> mutate(context, command)
            else -> CommandResult.failure(command.id, CommandError(ErrorCodes.UNSUPPORTED_ACTION, "Unknown calendar action", id))
        }

    private fun list(context: Context, command: Command): CommandResult {
        if (!has(context, Manifest.permission.READ_CALENDAR)) return perm(command.id, Manifest.permission.READ_CALENDAR)
        val days = command.parameters["days"]?.jsonPrimitive?.intOrNull ?: 7
        val now = System.currentTimeMillis()
        val proj = arrayOf(CalendarContract.Events._ID, CalendarContract.Events.TITLE, CalendarContract.Events.DTSTART, CalendarContract.Events.DTEND, CalendarContract.Events.EVENT_LOCATION)
        val sel = "${CalendarContract.Events.DTSTART} >= ? AND ${CalendarContract.Events.DTSTART} <= ?"
        val args = arrayOf(now.toString(), (now + days * 86_400_000L).toString())
        val arr = buildJsonArray {
            context.contentResolver.query(CalendarContract.Events.CONTENT_URI, proj, sel, args, "${CalendarContract.Events.DTSTART} ASC")?.use { c ->
                val idC = c.getColumnIndexOrThrow(CalendarContract.Events._ID)
                val tC = c.getColumnIndexOrThrow(CalendarContract.Events.TITLE)
                val sC = c.getColumnIndexOrThrow(CalendarContract.Events.DTSTART)
                val eC = c.getColumnIndexOrThrow(CalendarContract.Events.DTEND)
                val lC = c.getColumnIndexOrThrow(CalendarContract.Events.EVENT_LOCATION)
                var n = 0
                while (c.moveToNext() && n < 50) {
                    add(buildJsonObject {
                        put("id", JsonPrimitive(c.getLong(idC))); put("title", JsonPrimitive(c.getString(tC) ?: "(no title)"))
                        put("start", JsonPrimitive(c.getLong(sC))); put("end", JsonPrimitive(c.getLong(eC)))
                        put("location", JsonPrimitive(c.getString(lC) ?: ""))
                    }); n++
                }
            }
        }
        return CommandResult.success(command.id, buildJsonObject { put("events", arr as JsonArray) })
    }

    private fun search(context: Context, command: Command): CommandResult {
        if (!has(context, Manifest.permission.READ_CALENDAR)) return perm(command.id, Manifest.permission.READ_CALENDAR)
        val q = command.parameters["query"]?.jsonPrimitive?.content?.trim()
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'query' required", id))
        val proj = arrayOf(CalendarContract.Events._ID, CalendarContract.Events.TITLE, CalendarContract.Events.DTSTART)
        val arr = buildJsonArray {
            context.contentResolver.query(CalendarContract.Events.CONTENT_URI, proj, "${CalendarContract.Events.TITLE} LIKE ?", arrayOf("%$q%"), null)?.use { c ->
                val idC = c.getColumnIndexOrThrow(CalendarContract.Events._ID)
                val tC = c.getColumnIndexOrThrow(CalendarContract.Events.TITLE)
                val sC = c.getColumnIndexOrThrow(CalendarContract.Events.DTSTART)
                var n = 0
                while (c.moveToNext() && n < 50) {
                    add(buildJsonObject { put("id", JsonPrimitive(c.getLong(idC))); put("title", JsonPrimitive(c.getString(tC) ?: "")); put("start", JsonPrimitive(c.getLong(sC))) }); n++
                }
            }
        }
        return CommandResult.success(command.id, buildJsonObject { put("events", arr as JsonArray) })
    }

    private fun create(context: Context, command: Command): CommandResult {
        if (!has(context, Manifest.permission.WRITE_CALENDAR)) return perm(command.id, Manifest.permission.WRITE_CALENDAR)
        val title = command.parameters["title"]?.jsonPrimitive?.content
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'title' required", id))
        val start = command.parameters["start"]?.jsonPrimitive?.longOrNull
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'start' (epoch ms) required", id))
        val end = command.parameters["end"]?.jsonPrimitive?.longOrNull ?: (start + 3_600_000L)
        val calId = primaryCalendarId(context) ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.CAPABILITY_UNAVAILABLE, "No writable calendar", id))
        val values = android.content.ContentValues().apply {
            put(CalendarContract.Events.CALENDAR_ID, calId); put(CalendarContract.Events.TITLE, title)
            put(CalendarContract.Events.DESCRIPTION, command.parameters["description"]?.jsonPrimitive?.content)
            put(CalendarContract.Events.EVENT_LOCATION, command.parameters["location"]?.jsonPrimitive?.content)
            put(CalendarContract.Events.DTSTART, start); put(CalendarContract.Events.DTEND, end)
            put(CalendarContract.Events.EVENT_TIMEZONE, TimeZone.getDefault().id)
        }
        val uri = context.contentResolver.insert(CalendarContract.Events.CONTENT_URI, values)
        val newId = uri?.lastPathSegment?.toLongOrNull()
        return CommandResult.success(command.id, buildJsonObject { put("id", JsonPrimitive(newId ?: -1)); put("title", JsonPrimitive(title)); put("created", JsonPrimitive(newId != null)) })
    }

    private fun mutate(context: Context, command: Command): CommandResult {
        if (!has(context, Manifest.permission.WRITE_CALENDAR)) return perm(command.id, Manifest.permission.WRITE_CALENDAR)
        val confirm = command.confirm || command.parameters["confirm"]?.jsonPrimitive?.content?.toBoolean() == true
        if (!confirm) return CommandResult.failure(command.id, CommandError(ErrorCodes.CONFIRMATION_REQUIRED, "Calendar mutations require confirmation", id, mapOf("action" to command.action)))
        val eventId = command.parameters["event_id"]?.jsonPrimitive?.longOrNull
            ?: return CommandResult.failure(command.id, CommandError(ErrorCodes.INVALID_PARAMETERS, "'event_id' required", id))
        val uri = ContentUris.withAppendedId(CalendarContract.Events.CONTENT_URI, eventId)
        val action = command.action.substringBefore('.').lowercase()
        return if (action.contains("cancel") || action.contains("delete")) {
            val rows = context.contentResolver.delete(uri, null, null)
            CommandResult.success(command.id, buildJsonObject { put("deleted", JsonPrimitive(rows > 0)); put("id", JsonPrimitive(eventId)) })
        } else {
            val values = android.content.ContentValues()
            command.parameters["start"]?.jsonPrimitive?.longOrNull?.let { values.put(CalendarContract.Events.DTSTART, it) }
            command.parameters["end"]?.jsonPrimitive?.longOrNull?.let { values.put(CalendarContract.Events.DTEND, it) }
            command.parameters["title"]?.jsonPrimitive?.content?.let { values.put(CalendarContract.Events.TITLE, it) }
            val rows = context.contentResolver.update(uri, values, null, null)
            CommandResult.success(command.id, buildJsonObject { put("updated", JsonPrimitive(rows > 0)); put("id", JsonPrimitive(eventId)) })
        }
    }

    private fun primaryCalendarId(context: Context): Long? {
        if (!has(context, Manifest.permission.READ_CALENDAR)) return null
        context.contentResolver.query(CalendarContract.Calendars.CONTENT_URI, arrayOf(CalendarContract.Calendars._ID, CalendarContract.Calendars.IS_PRIMARY), null, null, null)?.use { c ->
            val idC = c.getColumnIndexOrThrow(CalendarContract.Calendars._ID)
            val pC = c.getColumnIndexOrThrow(CalendarContract.Calendars.IS_PRIMARY)
            var first: Long? = null
            while (c.moveToNext()) { val id = c.getLong(idC); if (first == null) first = id; if (c.getInt(pC) == 1) return id }
            return first
        }
        return null
    }

    private fun has(context: Context, p: String) = ContextCompat.checkSelfPermission(context, p) == PackageManager.PERMISSION_GRANTED
    private fun perm(id: String, p: String) = CommandResult.failure(id, CommandError(ErrorCodes.PERMISSION_REQUIRED, "$p not granted", "calendar", mapOf("permission" to p)))
}
