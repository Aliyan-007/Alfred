package com.alfred.android.voice

import java.util.Locale

data class BritishVoiceCandidate(
    val name: String,
    val locale: Locale,
    val quality: Int,
    val latency: Int,
    val networkRequired: Boolean
)

data class BritishVoiceDiagnostics(
    val requestedLocale: Locale = Locale.UK,
    val exactBritishVoiceExists: Boolean = false,
    val selectedVoiceName: String? = null,
    val selectedVoiceLocale: Locale = Locale.UK,
    val isFallback: Boolean = false,
    val selectedVoice: BritishVoiceCandidate? = null
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

    fun evaluate(
        candidates: List<BritishVoiceCandidate>,
        requestedLocale: Locale = Locale.UK
    ): BritishVoiceDiagnostics {
        val exactBritishVoiceExists = candidates.any {
            it.locale.language == requestedLocale.language &&
                it.locale.country == requestedLocale.country
        }
        val selected = pickBest(candidates)
        val selectedLocale = selected?.locale ?: requestedLocale
        val isFallback = selected == null || selected.locale.language != requestedLocale.language || selected.locale.country != requestedLocale.country

        return BritishVoiceDiagnostics(
            requestedLocale = requestedLocale,
            exactBritishVoiceExists = exactBritishVoiceExists,
            selectedVoiceName = selected?.name,
            selectedVoiceLocale = selectedLocale,
            isFallback = isFallback,
            selectedVoice = selected
        )
    }
}
