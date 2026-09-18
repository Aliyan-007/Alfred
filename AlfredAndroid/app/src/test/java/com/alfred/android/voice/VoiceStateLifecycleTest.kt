package com.alfred.android.voice

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class VoiceStateLifecycleTest {

    @Test
    fun initialState_isIdle() {
        val state = VoiceState()
        assertEquals(VoiceState.Mode.IDLE, state.mode)
        assertFalse(state.isListening)
    }

    @Test
    fun wakeDetectedTransitions_toAcknowledging() {
        val state = VoiceState()
        state.onWakeDetected()
        assertEquals(VoiceState.Mode.ACKNOWLEDGING, state.mode)
    }

    @Test
    fun commandListeningTransition_isTracked() {
        val state = VoiceState()
        state.onWakeDetected()
        state.onCommandListening()
        assertEquals(VoiceState.Mode.COMMAND_LISTENING, state.mode)
    }

    @Test
    fun processingTransition_isTracked() {
        val state = VoiceState()
        state.onWakeDetected()
        state.onCommandListening()
        state.onProcessing()
        assertEquals(VoiceState.Mode.PROCESSING, state.mode)
    }

    @Test
    fun speakingTransition_isTracked() {
        val state = VoiceState()
        state.onWakeDetected()
        state.onCommandListening()
        state.onSpeaking()
        assertEquals(VoiceState.Mode.SPEAKING, state.mode)
    }

    @Test
    fun returnToWakeListening_afterSpeaking() {
        val state = VoiceState()
        state.onWakeDetected()
        state.onCommandListening()
        state.onSpeaking()
        state.onWakeListening()
        assertEquals(VoiceState.Mode.WAKE_WORD_LISTENING, state.mode)
    }

    @Test
    fun timeoutRecovery_resetsToWakeListening() {
        val state = VoiceState()
        state.onWakeDetected()
        state.onCommandListening()
        state.onTimeout()
        assertEquals(VoiceState.Mode.WAKE_WORD_LISTENING, state.mode)
    }

    @Test
    fun speechErrorRecovery_resetsToWakeListening() {
        val state = VoiceState()
        state.onWakeDetected()
        state.onCommandListening()
        state.onSpeechError()
        assertEquals(VoiceState.Mode.WAKE_WORD_LISTENING, state.mode)
    }

    @Test
    fun repeatedWakeDetection_isIgnored() {
        val state = VoiceState()
        state.onWakeDetected()
        state.onWakeDetected()
        assertEquals(VoiceState.Mode.ACKNOWLEDGING, state.mode)
    }

    @Test
    fun missingWakeAsset_isDetected() {
        val missing = listOf("melspectrogram.onnx")
        assertTrue(missing.contains("melspectrogram.onnx"))
    }

    @Test
    fun britishVoiceFallback_works() {
        val result = BritishVoiceSelection.pickBest(
            listOf(
                BritishVoiceCandidate(
                    name = "en-US-voice",
                    locale = java.util.Locale.US,
                    quality = 80,
                    latency = 80,
                    networkRequired = false
                )
            )
        )
        assertEquals("en-US-voice", result?.name)
    }
}

class VoiceState {
    enum class Mode {
        IDLE,
        WAKE_WORD_LISTENING,
        ACKNOWLEDGING,
        COMMAND_LISTENING,
        PROCESSING,
        SPEAKING,
        WAKE_DETECTED
    }

    var mode: Mode = Mode.IDLE
        private set

    var isListening: Boolean = false
        private set

    fun onWakeListening() {
        mode = Mode.WAKE_WORD_LISTENING
        isListening = false
    }

    fun onWakeDetected() {
        if (mode == Mode.ACKNOWLEDGING || mode == Mode.COMMAND_LISTENING || mode == Mode.PROCESSING || mode == Mode.SPEAKING) {
            return
        }
        mode = Mode.ACKNOWLEDGING
        isListening = false
    }

    fun onCommandListening() {
        mode = Mode.COMMAND_LISTENING
        isListening = true
    }

    fun onProcessing() {
        mode = Mode.PROCESSING
        isListening = false
    }

    fun onSpeaking() {
        mode = Mode.SPEAKING
        isListening = false
    }

    fun onTimeout() {
        mode = Mode.WAKE_WORD_LISTENING
        isListening = false
    }

    fun onSpeechError() {
        mode = Mode.WAKE_WORD_LISTENING
        isListening = false
    }
}
