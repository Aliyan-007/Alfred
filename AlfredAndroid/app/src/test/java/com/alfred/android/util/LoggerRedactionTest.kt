package com.alfred.android.util

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LoggerRedactionTest {
    private fun redact(s: String) = Regex("(?i)(token|password|secret|pairing[_ -]?code|authorization)\"?\\s*[:=]\\s*\"?[^\\s,\"}]+")
        .replace(s) { "${it.groupValues[1]}=******" }

    @Test fun tokenRedacted() { val o = redact("token=abc123"); assertFalse(o.contains("abc123")); assertTrue(o.contains("******")) }
    @Test fun pairingCodeRedacted() { val o = redact("pairing code = 482913"); assertFalse(o.contains("482913")) }
    @Test fun plainPasses() { val m = "command get_battery"; assertTrue(redact(m) == m) }
}
