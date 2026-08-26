package com.alfred.android.capabilities

import com.alfred.android.capabilities.shortcuts.WorkflowStep
import com.alfred.android.capabilities.shortcuts.WorkflowStore
import kotlinx.serialization.json.JsonObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ShortcutWorkflowTest {
    @Test fun storeCrud() {
        val s = WorkflowStore(); assertNull(s.get("study"))
        s.save("Study", listOf(WorkflowStep("open_app", JsonObject(emptyMap()))))
        assertEquals(1, s.get("study")?.size)
        s.delete("STUDY"); assertNull(s.get("study"))
    }
}
