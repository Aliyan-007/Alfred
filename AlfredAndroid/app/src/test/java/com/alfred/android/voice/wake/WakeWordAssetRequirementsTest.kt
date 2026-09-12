package com.alfred.android.voice.wake

import com.alfred.android.voice.BritishVoiceCandidate
import com.alfred.android.voice.BritishVoiceSelection
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Locale

class WakeWordAssetRequirementsTest {

    @Test
    fun requiredAssetNames_areExact() {
        assertEquals(
            listOf(
                "alfred.onnx",
                "melspectrogram.onnx",
                "embedding_model.onnx"
            ),
            WakeWordAssetRequirements.requiredAssetNames
        )
    }

    @Test
    fun missingAssets_areReported() {
        val missing = WakeWordAssetRequirements.findMissing(
            setOf(
                "alfred.onnx",
                "embedding_model.onnx"
            )
        )

        assertEquals(
            listOf("melspectrogram.onnx"),
            missing
        )
    }

    @Test
    fun wakeEngineStateTransitions_areStable() {
        val assetState = WakeWordAssetRequirements.normalizeState(
            setOf(
                "alfred.onnx",
                "melspectrogram.onnx",
                "embedding_model.onnx"
            )
        )

        assertFalse(assetState.hasMissingAssets)
        assertTrue(assetState.missingAssets.isEmpty())
    }
}

class BritishVoiceSelectionTest {

    @Test
    fun prefersExactBritishEnglishVoice() {
        val result = BritishVoiceSelection.pickBest(
            listOf(
                BritishVoiceCandidate(
                    name = "en-US-daniel",
                    locale = Locale.US,
                    quality = 100,
                    latency = 100,
                    networkRequired = false
                ),
                BritishVoiceCandidate(
                    name = "en-GB-daniel",
                    locale = Locale.UK,
                    quality = 200,
                    latency = 90,
                    networkRequired = false
                )
            )
        )

        assertEquals("en-GB-daniel", result?.name)
    }

    @Test
    fun fallsBackToLocaleWhenNoDedicatedVoiceExists() {
        val result = BritishVoiceSelection.pickBest(
            listOf(
                BritishVoiceCandidate(
                    name = "en-US-voice",
                    locale = Locale.US,
                    quality = 100,
                    latency = 80,
                    networkRequired = false
                )
            )
        )

        assertEquals("en-US-voice", result?.name)
    }
}
