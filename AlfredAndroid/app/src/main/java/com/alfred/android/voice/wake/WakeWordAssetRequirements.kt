package com.alfred.android.voice.wake

object WakeWordAssetRequirements {
    val requiredAssetNames: List<String> = listOf(
        "alfred.onnx",
        "melspectrogram.onnx",
        "embedding_model.onnx"
    )

    data class AssetState(
        val missingAssets: List<String>,
        val hasMissingAssets: Boolean
    )

    fun findMissing(availableAssetNames: Collection<String>): List<String> {
        val available = availableAssetNames.map { it.trim() }.filter { it.isNotEmpty() }.toSet()
        return requiredAssetNames.filterNot { available.contains(it) }
    }

    fun normalizeState(availableAssetNames: Collection<String>): AssetState {
        val missing = findMissing(availableAssetNames)
        return AssetState(
            missingAssets = missing,
            hasMissingAssets = missing.isNotEmpty()
        )
    }
}
