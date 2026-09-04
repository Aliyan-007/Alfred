package com.alfred.android.voice.wake

import android.content.Context
import android.util.Log
import com.rementia.openwakeword.lib.WakeWordEngine as LibraryWakeWordEngine
import com.rementia.openwakeword.lib.model.DetectionMode
import com.rementia.openwakeword.lib.model.WakeWordDetection
import com.rementia.openwakeword.lib.model.WakeWordModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.launch

/**
 * Adapter around the Re-MENTIA OpenWakeWord Android library.
 *
 * Important:
 * - Wake-word detection is local/offline.
 * - Android SpeechRecognizer is NOT used here.
 * - The actual Alfred wake-word classifier must exist as:
 *
 *     app/src/main/assets/alfred.onnx
 *
 * Required OpenWakeWord support models are supplied separately
 * by the library/project setup.
 */
class OpenWakeWordEngineAdapter(
    private val context: Context,
    private val onWakeWordDetected: () -> Unit,
    private val onError: (String) -> Unit
) : WakeWordEngine {

    companion object {
        private const val TAG = "OpenWakeWordAdapter"

        /**
         * Your custom Alfred wake-word classifier.
         */
        private const val MODEL_FILE = "alfred.onnx"

        /**
         * Human-readable model name.
         */
        private const val WAKE_WORD = "Alfred"

        /**
         * Initial detection threshold.
         *
         * We will tune this later after the real model is installed
         * and tested.
         */
        private const val THRESHOLD = 0.12f

        /**
         * Prevent repeated detections from a single utterance.
         */
        private const val COOLDOWN_MS = 2_000L
    }

    private var libraryEngine: LibraryWakeWordEngine? = null

    private var detectionJob: Job? = null

    /**
     * Long-lived scope for this adapter.
     *
     * SupervisorJob prevents one child failure from killing
     * unrelated work.
     */
    private var scope: CoroutineScope? = null

    @Volatile
    private var running = false

    @Volatile
    private var released = false

    override val isRunning: Boolean
        get() = running

    /**
     * Starts or restarts wake-word monitoring.
     */
    override fun start() {
        if (released) {
            Log.w(TAG, "Ignoring start(): engine has been released")
            return
        }

        if (running) {
            Log.d(TAG, "Wake-word engine is already running")
            return
        }

        try {
            if (!assetExists(MODEL_FILE)) {
                val message =
                    "$MODEL_FILE is missing from app/src/main/assets"

                Log.e(TAG, message)
                onError(message)
                return
            }

            /*
             * Reuse the underlying engine when possible.
             *
             * The service repeatedly switches between:
             *
             *   wake word -> command -> wake word
             *
             * so we do not want to recreate the model unnecessarily
             * every time.
             */
            if (libraryEngine == null) {
                libraryEngine = createLibraryEngine()
            }

            val engine = libraryEngine
                ?: run {
                    onError("Wake-word engine could not be created")
                    return
                }

            ensureScope()

            /*
             * Cancel any stale collector before creating a new one.
             */
            detectionJob?.cancel()

            running = true

            detectionJob = scope?.launch {
                engine.detections
                    .catch { throwable ->
                        if (!running || released) {
                            return@catch
                        }

                        Log.e(
                            TAG,
                            "Wake-word detection failed",
                            throwable
                        )

                        running = false

                        mainSafeError(
                            throwable.message
                                ?: "Wake-word detection failed"
                        )
                    }
                    .collect { detection ->
                        handleDetection(detection)
                    }
            }

            engine.start()

            Log.i(
                TAG,
                "OpenWakeWord engine started"
            )
        } catch (exception: Exception) {
            running = false

            detectionJob?.cancel()
            detectionJob = null

            Log.e(
                TAG,
                "Unable to start OpenWakeWord",
                exception
            )

            mainSafeError(
                exception.message
                    ?: "Unable to start wake-word engine"
            )
        }
    }

    /**
     * Temporarily stops wake-word detection.
     *
     * The engine remains allocated so it can be started again
     * without rebuilding everything.
     */
    override fun stop() {
        if (!running) {
            return
        }

        Log.i(
            TAG,
            "Stopping OpenWakeWord engine"
        )

        running = false

        detectionJob?.cancel()
        detectionJob = null

        try {
            libraryEngine?.stop()
        } catch (exception: Exception) {
            Log.e(
                TAG,
                "Error stopping OpenWakeWord engine",
                exception
            )
        }

        Log.i(
            TAG,
            "OpenWakeWord engine stopped"
        )
    }

    /**
     * Permanently releases the engine.
     *
     * This is called when AlfredAgentService is destroyed.
     */
    override fun release() {
        if (released) {
            return
        }

        Log.i(
            TAG,
            "Releasing OpenWakeWord engine"
        )

        released = true
        running = false

        detectionJob?.cancel()
        detectionJob = null

        try {
            libraryEngine?.stop()
        } catch (exception: Exception) {
            Log.e(
                TAG,
                "Error stopping OpenWakeWord during release",
                exception
            )
        }

        try {
            libraryEngine?.release()
        } catch (exception: Exception) {
            Log.e(
                TAG,
                "Error releasing OpenWakeWord",
                exception
            )
        }

        libraryEngine = null

        scope?.cancel()
        scope = null

        Log.i(
            TAG,
            "OpenWakeWord engine released"
        )
    }

    /**
     * Creates the Re-MENTIA engine.
     */
    private fun createLibraryEngine(): LibraryWakeWordEngine {
        val model = WakeWordModel(
            name = WAKE_WORD,
            modelPath = MODEL_FILE,
            threshold = THRESHOLD
        )

        return LibraryWakeWordEngine(
            context = context.applicationContext,
            models = listOf(model),
            detectionMode = DetectionMode.SINGLE_BEST,
            detectionCooldownMs = COOLDOWN_MS
        )
    }

    /**
     * Makes sure the coroutine scope exists.
     *
     * The scope is created lazily so the adapter does not allocate
     * coroutine resources until wake detection is actually started.
     */
    private fun ensureScope() {
        if (scope == null) {
            scope =
                CoroutineScope(
                    SupervisorJob() +
                        Dispatchers.Default
                )
        }
    }

    /**
     * Processes a detection emitted by the OpenWakeWord library.
     */
    private fun handleDetection(
        detection: WakeWordDetection
    ) {
        if (!running || released) {
            return
        }

        Log.i(
            TAG,
            "Wake word detected: $detection"
        )

        /*
         * Immediately stop the local detector.
         *
         * This prevents the detector from hearing the user's command
         * or Alfred's own TTS response as another wake word.
         */
        running = false

        try {
            libraryEngine?.stop()
        } catch (exception: Exception) {
            Log.e(
                TAG,
                "Error stopping engine after detection",
                exception
            )
        }

        detectionJob?.cancel()
        detectionJob = null

        mainSafeWakeDetected()
    }

    /**
     * Checks whether the custom Alfred ONNX model exists.
     */
    private fun assetExists(
        fileName: String
    ): Boolean {
        return try {
            context.assets
                .open(fileName)
                .use {
                    true
                }
        } catch (_: Exception) {
            false
        }
    }

    /**
     * Wake callbacks are ultimately consumed by the Android service,
     * so dispatch them safely.
     */
    private fun mainSafeWakeDetected() {
        try {
            onWakeWordDetected()
        } catch (exception: Exception) {
            Log.e(
                TAG,
                "Wake callback failed",
                exception
            )
        }
    }

    private fun mainSafeError(
        message: String
    ) {
        try {
            onError(message)
        } catch (exception: Exception) {
            Log.e(
                TAG,
                "Wake error callback failed",
                exception
            )
        }
    }
}