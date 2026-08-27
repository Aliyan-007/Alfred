package com.alfred.android.capabilities.calendar

import android.Manifest
import android.content.ContentUris
import android.content.ContentValues
import android.content.Context
import android.content.pm.PackageManager
import android.provider.CalendarContract
import androidx.core.content.ContextCompat
import com.alfred.android.capabilities.BaseCapability
import com.alfred.android.capabilities.CapabilityState
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandError
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.ErrorCodes
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


    override fun refresh(
        context: Context
    ) {

        val readGranted =
            hasPermission(
                context,
                Manifest.permission.READ_CALENDAR
            )

        val writeGranted =
            hasPermission(
                context,
                Manifest.permission.WRITE_CALENDAR
            )

        if (
            readGranted &&
            writeGranted
        ) {

            setState(
                CapabilityState.AVAILABLE
            )

        } else {

            setState(
                CapabilityState.PERMISSION_REQUIRED
            )
        }
    }


    override suspend fun handle(
        command: Command,
        context: Context
    ): CommandResult {

        val action =
            command.action
                .substringAfter(
                    ".",
                    "list"
                )
                .lowercase()

        return when (
            action
        ) {

            "list",
            "list_upcoming" -> {

                listEvents(
                    context,
                    command
                )
            }


            "search" -> {

                searchEvents(
                    context,
                    command
                )
            }


            "create" -> {

                createEvent(
                    context,
                    command
                )
            }


            "reschedule",
            "update" -> {

                updateEvent(
                    context,
                    command
                )
            }


            "cancel",
            "delete" -> {

                deleteEvent(
                    context,
                    command
                )
            }


            else -> {

                CommandResult.failure(
                    command.id,
                    CommandError(
                        ErrorCodes.UNSUPPORTED_ACTION,
                        "Unknown calendar action: $action",
                        id
                    )
                )
            }
        }
    }


    // =====================================================
    // LIST EVENTS
    // =====================================================

    private fun listEvents(
        context: Context,
        command: Command
    ): CommandResult {

        if (
            !hasPermission(
                context,
                Manifest.permission.READ_CALENDAR
            )
        ) {

            return permissionError(
                command.id,
                Manifest.permission.READ_CALENDAR
            )
        }


        return try {

            val days =
                command.parameters["days"]
                    ?.jsonPrimitive
                    ?.intOrNull
                    ?: 7


            val now =
                System.currentTimeMillis()


            val endTime =
                now +
                (
                    days.toLong() *
                    24L *
                    60L *
                    60L *
                    1000L
                )


            val projection =
                arrayOf(

                    CalendarContract.Events._ID,

                    CalendarContract.Events.TITLE,

                    CalendarContract.Events.DTSTART,

                    CalendarContract.Events.DTEND,

                    CalendarContract.Events.EVENT_LOCATION
                )


            val selection =
                "${CalendarContract.Events.DTSTART} >= ? AND " +
                "${CalendarContract.Events.DTSTART} <= ?"


            val selectionArgs =
                arrayOf(
                    now.toString(),
                    endTime.toString()
                )


            val events =
                buildJsonArray {

                    context.contentResolver.query(

                        CalendarContract.Events.CONTENT_URI,

                        projection,

                        selection,

                        selectionArgs,

                        "${CalendarContract.Events.DTSTART} ASC"

                    )?.use { cursor ->

                        val idColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events._ID
                            )


                        val titleColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events.TITLE
                            )


                        val startColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events.DTSTART
                            )


                        val endColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events.DTEND
                            )


                        val locationColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events.EVENT_LOCATION
                            )


                        var count = 0


                        while (
                            cursor.moveToNext() &&
                            count < 50
                        ) {

                            add(

                                buildJsonObject {

                                    put(
                                        "id",
                                        JsonPrimitive(
                                            cursor.getLong(
                                                idColumn
                                            )
                                        )
                                    )


                                    put(
                                        "title",
                                        JsonPrimitive(
                                            cursor.getString(
                                                titleColumn
                                            )
                                                ?: "(no title)"
                                        )
                                    )


                                    put(
                                        "start",
                                        JsonPrimitive(
                                            cursor.getLong(
                                                startColumn
                                            )
                                        )
                                    )


                                    put(
                                        "end",
                                        JsonPrimitive(
                                            cursor.getLong(
                                                endColumn
                                            )
                                        )
                                    )


                                    put(
                                        "location",
                                        JsonPrimitive(
                                            cursor.getString(
                                                locationColumn
                                            )
                                                ?: ""
                                        )
                                    )
                                }
                            )

                            count++
                        }
                    }
                }


            CommandResult.success(

                command.id,

                buildJsonObject {

                    put(
                        "events",
                        events
                    )
                }
            )

        } catch (
            error: Exception
        ) {

            CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.CAPABILITY_UNAVAILABLE,

                    "Failed to read calendar: ${error.message}",

                    id
                )
            )
        }
    }


    // =====================================================
    // SEARCH EVENTS
    // =====================================================

    private fun searchEvents(
        context: Context,
        command: Command
    ): CommandResult {

        if (
            !hasPermission(
                context,
                Manifest.permission.READ_CALENDAR
            )
        ) {

            return permissionError(
                command.id,
                Manifest.permission.READ_CALENDAR
            )
        }


        val query =
            command.parameters["query"]
                ?.jsonPrimitive
                ?.content
                ?.trim()


        if (
            query.isNullOrBlank()
        ) {

            return CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.INVALID_PARAMETERS,

                    "'query' required",

                    id
                )
            )
        }


        return try {

            val projection =
                arrayOf(

                    CalendarContract.Events._ID,

                    CalendarContract.Events.TITLE,

                    CalendarContract.Events.DTSTART,

                    CalendarContract.Events.DTEND
                )


            val events =
                buildJsonArray {

                    context.contentResolver.query(

                        CalendarContract.Events.CONTENT_URI,

                        projection,

                        "${CalendarContract.Events.TITLE} LIKE ?",

                        arrayOf(
                            "%$query%"
                        ),

                        "${CalendarContract.Events.DTSTART} ASC"

                    )?.use { cursor ->

                        val idColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events._ID
                            )


                        val titleColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events.TITLE
                            )


                        val startColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events.DTSTART
                            )


                        val endColumn =
                            cursor.getColumnIndexOrThrow(
                                CalendarContract.Events.DTEND
                            )


                        var count = 0


                        while (
                            cursor.moveToNext() &&
                            count < 50
                        ) {

                            add(

                                buildJsonObject {

                                    put(
                                        "id",
                                        JsonPrimitive(
                                            cursor.getLong(
                                                idColumn
                                            )
                                        )
                                    )


                                    put(
                                        "title",
                                        JsonPrimitive(
                                            cursor.getString(
                                                titleColumn
                                            )
                                                ?: ""
                                        )
                                    )


                                    put(
                                        "start",
                                        JsonPrimitive(
                                            cursor.getLong(
                                                startColumn
                                            )
                                        )
                                    )


                                    put(
                                        "end",
                                        JsonPrimitive(
                                            cursor.getLong(
                                                endColumn
                                            )
                                        )
                                    )
                                }
                            )

                            count++
                        }
                    }
                }


            CommandResult.success(

                command.id,

                buildJsonObject {

                    put(
                        "events",
                        events
                    )
                }
            )

        } catch (
            error: Exception
        ) {

            CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.CAPABILITY_UNAVAILABLE,

                    "Failed to search calendar: ${error.message}",

                    id
                )
            )
        }
    }


    // =====================================================
    // CREATE EVENT
    // =====================================================

    private fun createEvent(
        context: Context,
        command: Command
    ): CommandResult {

        if (
            !hasPermission(
                context,
                Manifest.permission.WRITE_CALENDAR
            )
        ) {

            return permissionError(
                command.id,
                Manifest.permission.WRITE_CALENDAR
            )
        }


        val title =
            command.parameters["title"]
                ?.jsonPrimitive
                ?.content
                ?.trim()


        if (
            title.isNullOrBlank()
        ) {

            return CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.INVALID_PARAMETERS,

                    "'title' required",

                    id
                )
            )
        }


        val start =
            command.parameters["start"]
                ?.jsonPrimitive
                ?.longOrNull


        if (
            start == null
        ) {

            return CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.INVALID_PARAMETERS,

                    "'start' (epoch milliseconds) required",

                    id
                )
            )
        }


        val end =
            command.parameters["end"]
                ?.jsonPrimitive
                ?.longOrNull
                ?: (
                    start +
                    60L *
                    60L *
                    1000L
                )


        return try {

            val calendarId =
                getWritableCalendarId(
                    context
                )


            if (
                calendarId == null
            ) {

                return CommandResult.failure(

                    command.id,

                    CommandError(

                        ErrorCodes.CAPABILITY_UNAVAILABLE,

                        "No writable calendar found on device",

                        id
                    )
                )
            }


            val values =
                ContentValues().apply {

                    put(
                        CalendarContract.Events.CALENDAR_ID,
                        calendarId
                    )


                    put(
                        CalendarContract.Events.TITLE,
                        title
                    )


                    command.parameters["description"]
                        ?.jsonPrimitive
                        ?.content
                        ?.let {

                            put(
                                CalendarContract.Events.DESCRIPTION,
                                it
                            )
                        }


                    command.parameters["location"]
                        ?.jsonPrimitive
                        ?.content
                        ?.let {

                            put(
                                CalendarContract.Events.EVENT_LOCATION,
                                it
                            )
                        }


                    put(
                        CalendarContract.Events.DTSTART,
                        start
                    )


                    put(
                        CalendarContract.Events.DTEND,
                        end
                    )


                    put(
                        CalendarContract.Events.EVENT_TIMEZONE,
                        TimeZone
                            .getDefault()
                            .id
                    )
                }


            val uri =
                context.contentResolver.insert(

                    CalendarContract.Events.CONTENT_URI,

                    values
                )


            if (
                uri == null
            ) {

                return CommandResult.failure(

                    command.id,

                    CommandError(

                        ErrorCodes.CAPABILITY_UNAVAILABLE,

                        "Calendar provider returned null while creating event",

                        id
                    )
                )
            }


            val eventId =
                uri.lastPathSegment
                    ?.toLongOrNull()


            if (
                eventId == null
            ) {

                return CommandResult.failure(

                    command.id,

                    CommandError(

                        ErrorCodes.CAPABILITY_UNAVAILABLE,

                        "Event was created but its ID could not be determined",

                        id
                    )
                )
            }


            CommandResult.success(

                command.id,

                buildJsonObject {

                    put(
                        "id",
                        JsonPrimitive(
                            eventId
                        )
                    )


                    put(
                        "title",
                        JsonPrimitive(
                            title
                        )
                    )


                    put(
                        "start",
                        JsonPrimitive(
                            start
                        )
                    )


                    put(
                        "end",
                        JsonPrimitive(
                            end
                        )
                    )


                    put(
                        "calendar_id",
                        JsonPrimitive(
                            calendarId
                        )
                    )


                    put(
                        "created",
                        JsonPrimitive(
                            true
                        )
                    )
                }
            )

        } catch (
            error: Exception
        ) {

            CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.CAPABILITY_UNAVAILABLE,

                    "Failed to create calendar event: ${error.message}",

                    id
                )
            )
        }
    }


    // =====================================================
    // UPDATE EVENT
    // =====================================================

    private fun updateEvent(
        context: Context,
        command: Command
    ): CommandResult {

        if (
            !hasPermission(
                context,
                Manifest.permission.WRITE_CALENDAR
            )
        ) {

            return permissionError(
                command.id,
                Manifest.permission.WRITE_CALENDAR
            )
        }


        val eventId =
            command.parameters["event_id"]
                ?.jsonPrimitive
                ?.longOrNull


        if (
            eventId == null
        ) {

            return CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.INVALID_PARAMETERS,

                    "'event_id' required",

                    id
                )
            )
        }


        return try {

            val values =
                ContentValues()


            command.parameters["title"]
                ?.jsonPrimitive
                ?.content
                ?.let {

                    values.put(
                        CalendarContract.Events.TITLE,
                        it
                    )
                }


            command.parameters["start"]
                ?.jsonPrimitive
                ?.longOrNull
                ?.let {

                    values.put(
                        CalendarContract.Events.DTSTART,
                        it
                    )
                }


            command.parameters["end"]
                ?.jsonPrimitive
                ?.longOrNull
                ?.let {

                    values.put(
                        CalendarContract.Events.DTEND,
                        it
                    )
                }


            if (
                values.size() == 0
            ) {

                return CommandResult.failure(

                    command.id,

                    CommandError(

                        ErrorCodes.INVALID_PARAMETERS,

                        "No fields provided to update",

                        id
                    )
                )
            }


            val uri =
                ContentUris.withAppendedId(

                    CalendarContract.Events.CONTENT_URI,

                    eventId
                )


            val rows =
                context.contentResolver.update(

                    uri,

                    values,

                    null,

                    null
                )


            CommandResult.success(

                command.id,

                buildJsonObject {

                    put(
                        "updated",
                        JsonPrimitive(
                            rows > 0
                        )
                    )


                    put(
                        "id",
                        JsonPrimitive(
                            eventId
                        )
                    )


                    put(
                        "rows",
                        JsonPrimitive(
                            rows
                        )
                    )
                }
            )

        } catch (
            error: Exception
        ) {

            CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.CAPABILITY_UNAVAILABLE,

                    "Failed to update calendar event: ${error.message}",

                    id
                )
            )
        }
    }


    // =====================================================
    // DELETE EVENT
    // =====================================================

    private fun deleteEvent(
        context: Context,
        command: Command
    ): CommandResult {

        if (
            !hasPermission(
                context,
                Manifest.permission.WRITE_CALENDAR
            )
        ) {

            return permissionError(
                command.id,
                Manifest.permission.WRITE_CALENDAR
            )
        }


        val eventId =
            command.parameters["event_id"]
                ?.jsonPrimitive
                ?.longOrNull


        if (
            eventId == null
        ) {

            return CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.INVALID_PARAMETERS,

                    "'event_id' required",

                    id
                )
            )
        }


        return try {

            val uri =
                ContentUris.withAppendedId(

                    CalendarContract.Events.CONTENT_URI,

                    eventId
                )


            val rows =
                context.contentResolver.delete(

                    uri,

                    null,

                    null
                )


            CommandResult.success(

                command.id,

                buildJsonObject {

                    put(
                        "deleted",
                        JsonPrimitive(
                            rows > 0
                        )
                    )


                    put(
                        "id",
                        JsonPrimitive(
                            eventId
                        )
                    )


                    put(
                        "rows",
                        JsonPrimitive(
                            rows
                        )
                    )
                }
            )

        } catch (
            error: Exception
        ) {

            CommandResult.failure(

                command.id,

                CommandError(

                    ErrorCodes.CAPABILITY_UNAVAILABLE,

                    "Failed to delete calendar event: ${error.message}",

                    id
                )
            )
        }
    }


    // =====================================================
    // FIND WRITABLE CALENDAR
    // =====================================================

    private fun getWritableCalendarId(
        context: Context
    ): Long? {

        if (
            !hasPermission(
                context,
                Manifest.permission.READ_CALENDAR
            )
        ) {

            return null
        }


        val projection =
            arrayOf(

                CalendarContract.Calendars._ID,

                CalendarContract.Calendars.CALENDAR_ACCESS_LEVEL,

                CalendarContract.Calendars.VISIBLE
            )


        return try {

            context.contentResolver.query(

                CalendarContract.Calendars.CONTENT_URI,

                projection,

                null,

                null,

                null

            )?.use { cursor ->

                val idColumn =
                    cursor.getColumnIndexOrThrow(
                        CalendarContract.Calendars._ID
                    )


                val accessColumn =
                    cursor.getColumnIndexOrThrow(
                        CalendarContract.Calendars.CALENDAR_ACCESS_LEVEL
                    )


                val visibleColumn =
                    cursor.getColumnIndexOrThrow(
                        CalendarContract.Calendars.VISIBLE
                    )


                var fallbackId: Long? =
                    null


                while (
                    cursor.moveToNext()
                ) {

                    val calendarId =
                        cursor.getLong(
                            idColumn
                        )


                    val accessLevel =
                        cursor.getInt(
                            accessColumn
                        )


                    val visible =
                        cursor.getInt(
                            visibleColumn
                        )


                    if (
                        fallbackId == null
                    ) {

                        fallbackId =
                            calendarId
                    }


                    if (
                        visible == 1 &&
                        accessLevel >=
                        CalendarContract.Calendars.CAL_ACCESS_CONTRIBUTOR
                    ) {

                        return calendarId
                    }
                }


                fallbackId
            }

        } catch (
            error: Exception
        ) {

            null
        }
    }


    // =====================================================
    // PERMISSION CHECK
    // =====================================================

    private fun hasPermission(
        context: Context,
        permission: String
    ): Boolean {

        return ContextCompat.checkSelfPermission(

            context,

            permission

        ) == PackageManager.PERMISSION_GRANTED
    }


    private fun permissionError(
        commandId: String,
        permission: String
    ): CommandResult {

        return CommandResult.failure(

            commandId,

            CommandError(

                ErrorCodes.PERMISSION_REQUIRED,

                "$permission not granted",

                id,

                mapOf(
                    "permission" to permission
                )
            )
        )
    }
}
