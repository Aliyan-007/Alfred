package com.alfred.android.voice

import java.util.Locale

data class BritishVoiceCandidate(
    val name: String,
    val locale: Locale,
    val quality: Int,
    val latency: Int,
    val networkRequired: Boolean
)

object BritishVoiceSelection {
    private val britishLocale = Locale.UK

    fun pickBest(candidates: List<BritishVoiceCandidate>): BritishVoiceCandidate? {
        val britishCandidates = candidates.filter {
            it.locale.language == britishLocale.language &&
                it.locale.country == britishLocale.country
        }

        return britishCandidates
            .sortedWith(
                compareByDescending<BritishVoiceCandidate> { it.quality }
                    .thenBy { it.latency }
                    .thenBy { it.networkRequired }
            )
            .firstOrNull() ?: candidates
            .sortedWith(
                compareByDescending<BritishVoiceCandidate> { it.quality }
                    .thenBy { it.latency }
                    .thenBy { it.networkRequired }
            )
            .firstOrNull()
    }
}
