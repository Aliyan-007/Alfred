package com.alfred.android.capabilities

import android.content.Context
import com.alfred.android.protocol.Command
import com.alfred.android.protocol.CommandResult
import com.alfred.android.protocol.ErrorCodes
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.mockito.kotlin.mock

class CapabilityRegistryTest {
    private class Fake(override val id: String, initial: CapabilityState) : Capability {
        override val displayName = id
        private val _s = MutableStateFlow(initial); override val state = _s
        override fun refresh(context: Context) {}
        var last: Command? = null
        override suspend fun handle(command: Command, context: Context): CommandResult { last = command; return CommandResult.success(command.id, kotlinx.serialization.json.JsonObject(emptyMap())) }
    }
    private val context: Context = mock()

    @Test fun `routes to capability`() = runTest {
        val reg = CapabilityRegistry(); val b = Fake("battery", CapabilityState.AVAILABLE); reg.register(b)
        val r = reg.dispatch(Command("c1", action = "battery"), context)
        assertTrue(r.success); assertEquals("c1", b.last?.id)
    }

    @Test fun `unknown action`() = runTest {
        val r = CapabilityRegistry().dispatch(Command("c2", action = "nope"), context)
        assertEquals(ErrorCodes.UNSUPPORTED_ACTION, r.error?.code)
    }

    @Test fun `non available returns unavailable`() = runTest {
        val reg = CapabilityRegistry(); reg.register(Fake("calendar", CapabilityState.PERMISSION_REQUIRED))
        val r = reg.dispatch(Command("c3", action = "calendar.list"), context)
        assertEquals(ErrorCodes.CAPABILITY_UNAVAILABLE, r.error?.code)
    }

    @Test fun `namespaced routing`() = runTest {
        val reg = CapabilityRegistry(); val a = Fake("apps", CapabilityState.AVAILABLE); reg.register(a)
        reg.dispatch(Command("c4", action = "apps.open_app"), context)
        assertEquals("apps.open_app", a.last?.action)
    }

    @Test fun `duplicates ignored`() {
        val reg = CapabilityRegistry(); reg.register(Fake("battery", CapabilityState.AVAILABLE)); reg.register(Fake("battery", CapabilityState.AVAILABLE))
        assertEquals(1, reg.all().size)
    }

    @Test fun `error helpers`() {
        val e = permissionRequiredError("calendar", "READ_CALENDAR")
        assertEquals(ErrorCodes.PERMISSION_REQUIRED, e.code); assertEquals("READ_CALENDAR", e.data?.get("permission"))
        assertEquals(ErrorCodes.INVALID_PARAMETERS, invalidParametersError().code)
        assertEquals(ErrorCodes.UNSUPPORTED_ACTION, unsupportedActionError("x").code)
    }
}
