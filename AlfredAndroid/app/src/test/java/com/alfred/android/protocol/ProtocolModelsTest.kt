package com.alfred.android.protocol

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ProtocolModelsTest {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    @Test fun `success result shape`() {
        val s = json.encodeToString(CommandResult.serializer(), CommandResult.success("c1", buildJsonObject { put("battery", 87) }))
        assertTrue(s.contains("\"type\":\"command_result\"")); assertTrue(s.contains("\"success\":true")); assertTrue(s.contains("\"id\":\"c1\""))
    }

    @Test fun `failure carries structured error`() {
        val err = CommandError(ErrorCodes.PERMISSION_REQUIRED, "need perm", "calendar", mapOf("p" to "READ"))
        val s = json.encodeToString(CommandResult.serializer(), CommandResult.failure("c2", err))
        assertTrue(s.contains("\"code\":\"permission_required\"")); assertTrue(s.contains("\"capability\":\"calendar\""))
    }

    @Test fun `command defaults`() {
        val c = json.decodeFromString(Command.serializer(), """{"id":"c3","action":"get_battery"}""")
        assertEquals("c3", c.id); assertNull(c.device); assertTrue(c.parameters.isEmpty())
    }

    @Test fun `command with confirm and device`() {
        val c = json.decodeFromString(Command.serializer(), """{"id":"c4","device":"p1","action":"x","confirm":true}""")
        assertEquals("p1", c.device); assertTrue(c.confirm)
    }

    @Test fun `pair round trip`() {
        val req = PairRequest(code = "482913", name = "Phone")
        val s = json.encodeToString(PairRequest.serializer(), req)
        assertTrue(s.contains("\"type\":\"pair\""))
        val resp = json.decodeFromString(PairResponse.serializer(), """{"success":true,"auth_token":"t","device_id":"d"}""")
        assertTrue(resp.success); assertEquals("t", resp.authToken)
    }

    @Test fun `event has timestamp`() {
        val e = DeviceEvent(event = "battery_changed", device = "d", ts = 1)
        val s = json.encodeToString(DeviceEvent.serializer(), e)
        assertTrue(s.contains("\"event\":\"battery_changed\"")); assertTrue(s.contains("\"ts\":1"))
    }

    @Test fun `error codes stable`() {
        assertEquals("permission_required", ErrorCodes.PERMISSION_REQUIRED)
        assertEquals("capability_unavailable", ErrorCodes.CAPABILITY_UNAVAILABLE)
        assertEquals("unsupported_action", ErrorCodes.UNSUPPORTED_ACTION)
        assertEquals("invalid_parameters", ErrorCodes.INVALID_PARAMETERS)
        assertEquals("confirmation_required", ErrorCodes.CONFIRMATION_REQUIRED)
        assertEquals("authentication_failed", ErrorCodes.AUTHENTICATION_FAILED)
        assertEquals("internal_error", ErrorCodes.INTERNAL_ERROR)
    }
}
