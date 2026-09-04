package com.alfred.android.voice.wake

/**
 * Abstraction for a local/offline wake-word engine.
 *
 * VoiceAssistant and AlfredAgentService depend only on this
 * interface and do not need to know which wake-word library
 * is being used underneath.
 */
interface WakeWordEngine {

    /**
     * True when the engine is actively monitoring audio.
     */
    val isRunning: Boolean

    /**
     * Start local wake-word detection.
     *
     * This must NOT use Android SpeechRecognizer.
     */
    fun start()

    /**
     * Stop wake-word detection temporarily.
     *
     * The engine may be started again later.
     */
    fun stop()

    /**
     * Permanently release all resources.
     *
     * After release(), the engine should not be reused.
     */
    fun release()
}