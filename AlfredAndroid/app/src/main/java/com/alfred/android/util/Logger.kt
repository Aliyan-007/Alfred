package com.alfred.android.util

import android.util.Log

object Logger {
    private const val DEFAULT_TAG = "ALFRED"
    @Volatile var verbose: Boolean = true

    private val secretPattern = Regex(
        "(?i)(token|password|secret|pairing[_ -]?code|authorization)\"?\\s*[:=]\\s*\"?[^\\s,\"}]+"
    )

    private fun redact(m: String) = m.replace(secretPattern) { "${it.groupValues[1]}=******" }

    fun v(tag: String = DEFAULT_TAG, message: () -> String) { if (verbose) Log.v(tag, redact(message())) }
    fun d(tag: String = DEFAULT_TAG, message: () -> String) { if (verbose) Log.d(tag, redact(message())) }
    fun i(tag: String = DEFAULT_TAG, message: String) { Log.i(tag, redact(message)) }
    fun w(tag: String = DEFAULT_TAG, message: String, t: Throwable? = null) { Log.w(tag, redact(message), t) }
    fun e(tag: String = DEFAULT_TAG, message: String, t: Throwable? = null) { Log.e(tag, redact(message), t) }
}
