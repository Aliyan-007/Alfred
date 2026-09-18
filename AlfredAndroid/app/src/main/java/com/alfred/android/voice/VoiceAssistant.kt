package com.alfred.android.voice

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import androidx.core.content.ContextCompat
import com.alfred.android.voice.wake.WakeWordEngine
import java.util.Locale
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

/**
 * Voice layer for ALFRED.
 *
 * Responsibilities:
 *
 * 1. Local wake-word engine
 * 2. Android SpeechRecognizer for commands
 * 3. Text-to-Speech responses
 *
 * Important:
 *
 * SpeechRecognizer is NEVER used for wake-word detection.
 *
 * Wake detection is handled entirely by WakeWordEngine.
 */
class VoiceAssistant(
    private val context: Context,
    private val wakeWordEngine: WakeWordEngine,
    private val onListeningChanged: (Boolean) -> Unit,
    private val onResult: (String) -> Unit,
    private val onError: (String) -> Unit,
    private val onWakeStateChanged: (Boolean) -> Unit = {},
    private val onTtsStateChanged: ((Boolean, Locale, String, Boolean) -> Unit)? = null
) : TextToSpeech.OnInitListener {

    private enum class ListeningMode {
        IDLE,
        WAKE_WORD,
        COMMAND
    }

    private var speechRecognizer: SpeechRecognizer? = null

    private var textToSpeech: TextToSpeech? = null

    @Volatile
    private var ttsInitialized = false

    @Volatile
    private var destroyed = false

    @Volatile
    private var isListening = false

    @Volatile
    private var listeningMode = ListeningMode.IDLE

    var ttsReady: Boolean
        get() = ttsInitialized
        private set(value) {
            ttsInitialized = value
        }

    var requestedLocale: Locale = Locale.UK
        private set

    var selectedVoiceName: String = "unknown"
        private set

    var currentVoiceLocale: Locale = Locale.US
        private set

    var britishEnglishAvailable: Boolean = false
        private set

    var usingBritishFallback: Boolean = false
        private set

    val ttsDiagnostics: BritishVoiceDiagnostics
        get() = BritishVoiceSelection.evaluate(
            candidates = emptyList(),
            requestedLocale = requestedLocale
        )

    private val utteranceCallbacks =
        ConcurrentHashMap<String, () -> Unit>()

    private val pendingSpeech =
        ArrayDeque<Pair<String, (() -> Unit)?>>()

    private val mainHandler =
        Handler(
            Looper.getMainLooper()
        )

    init {
        /*
         * TTS must be initialized using the application context
         * so it does not retain an Activity.
         */
        textToSpeech =
            TextToSpeech(
                context.applicationContext,
                this
            )
    }

    // ---------------------------------------------------------------------
    // TEXT TO SPEECH
    // ---------------------------------------------------------------------

    override fun onInit(
        status: Int
    ) {
        if (destroyed) {
            return
        }

        if (status != TextToSpeech.SUCCESS) {
            ttsReady = false

            LogHelper.error(
                "TTS initialization failed"
            )

            return
        }

        ttsReady = true
        requestedLocale = Locale.UK

        configureBritishMaleVoice()

        LogHelper.info(
            "TTS initialized; requested locale=${requestedLocale}; en-GB=${britishEnglishAvailable}; selectedVoice=${selectedVoiceName}; fallback=${usingBritishFallback}"
        )

        onTtsStateChanged?.invoke(
            ttsReady,
            currentVoiceLocale,
            selectedVoiceName,
            britishEnglishAvailable
        )

        flushPendingSpeech()

        textToSpeech?.setSpeechRate(
            0.96f
        )

        textToSpeech?.setPitch(
            0.98f
        )

        textToSpeech?.setOnUtteranceProgressListener(
            object : UtteranceProgressListener() {

                override fun onStart(
                    utteranceId: String?
                ) {
                    /*
                     * Nothing required here.
                     */
                }

                override fun onDone(
                    utteranceId: String?
                ) {
                    finishUtterance(
                        utteranceId
                    )
                }

                @Deprecated(
                    "Deprecated in Android API"
                )
                override fun onError(
                    utteranceId: String?
                ) {
                    finishUtterance(
                        utteranceId
                    )
                }

                override fun onError(
                    utteranceId: String?,
                    errorCode: Int
                ) {
                    finishUtterance(
                        utteranceId
                    )
                }
            }
        )

        LogHelper.info(
            "TTS initialized"
        )
    }

    /**
     * Speaks text and optionally invokes onDone when TTS finishes.
     *
     * TTS completion is important because the service uses it to decide
     * when to start command listening again.
     */
    fun speak(
        text: String,
        onDone: (() -> Unit)? = null
    ) {
        if (
            text.isBlank() ||
            destroyed
        ) {
            onDone?.invoke()
            return
        }

        val cleanText =
            cleanForSpeech(
                text
            )

        if (cleanText.isBlank()) {
            onDone?.invoke()
            return
        }

        if (!ttsReady || textToSpeech == null) {
            pendingSpeech.addLast(
                cleanText to onDone
            )
            return
        }

        val utteranceId =
            "alfred-${UUID.randomUUID()}"

        if (onDone != null) {
            utteranceCallbacks[
                utteranceId
            ] = onDone
        }

        val result =
            try {
                textToSpeech?.speak(
                    cleanText,
                    TextToSpeech.QUEUE_FLUSH,
                    null,
                    utteranceId
                )
            } catch (exception: Exception) {
                LogHelper.error(
                    "TTS speak failed: ${exception.message}"
                )

                TextToSpeech.ERROR
            }

        if (result == TextToSpeech.ERROR) {
            utteranceCallbacks.remove(
                utteranceId
            )

            onDone?.invoke()
        }
    }

    private fun flushPendingSpeech() {
        if (!ttsReady || textToSpeech == null) {
            return
        }

        while (pendingSpeech.isNotEmpty()) {
            val (pendingText, pendingDone) = pendingSpeech.removeFirst()
            speak(
                pendingText,
                pendingDone
            )
        }
    }

    private fun finishUtterance(
        utteranceId: String?
    ) {
        if (utteranceId == null) {
            return
        }

        val callback =
            utteranceCallbacks.remove(
                utteranceId
            )

        if (callback != null) {
            mainHandler.post {
                if (!destroyed) {
                    callback()
                }
            }
        }
    }

    /**
     * Selects the best available British English male voice.
     *
     * Android's Voice object does not expose a reliable gender field,
     * therefore the name hints are heuristic.
     */
    private fun configureBritishMaleVoice() {
        val tts =
            textToSpeech
                ?: return

        val voices =
            runCatching {
                tts.voices
            }.getOrNull()
                .orEmpty()

        val britishVoices =
            voices.map {
                BritishVoiceCandidate(
                    name = it.name,
                    locale = it.locale,
                    quality = it.quality,
                    latency = it.latency,
                    networkRequired = it.isNetworkConnectionRequired
                )
            }

        val diagnostics =
            BritishVoiceSelection.evaluate(
                britishVoices,
                requestedLocale = Locale.UK
            )

        val selected = diagnostics.selectedVoice

        if (selected != null) {
            val voice =
                voices.firstOrNull {
                    it.name == selected.name
                }

            if (voice != null) {
                tts.setVoice(
                    voice
                )
                selectedVoiceName = voice.name
                currentVoiceLocale = voice.locale
                britishEnglishAvailable =
                    voice.locale.language == Locale.UK.language &&
                        voice.locale.country == Locale.UK.country
                usingBritishFallback = diagnostics.isFallback
                requestedLocale = Locale.UK
                LogHelper.info(
                    "Selected British TTS voice: ${voice.name}; locale=${voice.locale}; fallback=${usingBritishFallback}"
                )
                return
            }
        }

        val hasBritishLocale = diagnostics.exactBritishVoiceExists

        currentVoiceLocale = Locale.UK
        britishEnglishAvailable = hasBritishLocale
        usingBritishFallback = true
        requestedLocale = Locale.UK
        selectedVoiceName = "default"

        tts.setLanguage(
            Locale.UK
        )

        if (hasBritishLocale) {
            LogHelper.info(
                "Using available en-GB language fallback"
            )
        } else {
            LogHelper.info(
                "No dedicated British voice found; using en-GB fallback"
            )
        }
    }

    /**
     * Removes URLs and unusual symbols before TTS.
     *
     * Roman Urdu and normal English remain intact.
     */
    private fun cleanForSpeech(
        text: String
    ): String {
        return text
            .replace(
                Regex(
                    "https?://\\S+"
                ),
                "web link"
            )
            .replace(
                Regex(
                    "[^A-Za-z0-9 .,!?'-]"
                ),
                " "
            )
            .replace(
                Regex(
                    "\\s+"
                ),
                " "
            )
            .trim()
    }

    // ---------------------------------------------------------------------
    // WAKE WORD
    // ---------------------------------------------------------------------

    /**
     * Starts genuine local wake-word detection.
     *
     * SpeechRecognizer is NOT used here.
     */
    fun startWakeWordListening() {
        if (destroyed) {
            return
        }

        if (!hasMicrophonePermission()) {
            onError(
                "Microphone permission is not granted"
            )
            return
        }

        if (listeningMode == ListeningMode.WAKE_WORD && wakeWordEngine.isRunning) {
            return
        }

        mainHandler.post {
            if (destroyed) {
                return@post
            }

            stopRecognizerOnly()

            listeningMode =
                ListeningMode.WAKE_WORD

            isListening = false

            onListeningChanged(
                false
            )

            onWakeStateChanged(
                true
            )

            wakeWordEngine.start()
        }
    }

    /**
     * Starts Android SpeechRecognizer after the wake word.
     */
    fun startCommandListening() {
        if (destroyed) {
            return
        }

        if (!hasMicrophonePermission()) {
            onError(
                "Microphone permission is not granted"
            )
            return
        }

        if (
            !SpeechRecognizer
                .isRecognitionAvailable(
                    context
                )
        ) {
            onError(
                "Speech recognition is not available on this phone"
            )
            return
        }

        if (listeningMode == ListeningMode.COMMAND && speechRecognizer != null) {
            return
        }

        mainHandler.post {
            if (destroyed) {
                return@post
            }

            wakeWordEngine.stop()

            stopRecognizerOnly()

            onWakeStateChanged(
                false
            )

            listeningMode =
                ListeningMode.COMMAND

            startRecognition()
        }
    }

    /**
     * Kept for compatibility with existing callers.
     *
     * It now means command listening only.
     */
    fun startListening(
        continuous: Boolean = false
    ) {
        startCommandListening()
    }

    private fun startRecognition() {
        if (
            destroyed ||
            listeningMode !=
            ListeningMode.COMMAND
        ) {
            return
        }

        stopRecognizerOnly()

        speechRecognizer =
            SpeechRecognizer
                .createSpeechRecognizer(
                    context
                )

        speechRecognizer?.setRecognitionListener(
            object : RecognitionListener {

                override fun onReadyForSpeech(
                    params: Bundle?
                ) {
                    if (destroyed) {
                        return
                    }

                    isListening = true

                    onListeningChanged(
                        true
                    )
                }

                override fun onBeginningOfSpeech() {
                    /*
                     * Speech has started.
                     */
                }

                override fun onRmsChanged(
                    rmsdB: Float
                ) {
                    /*
                     * Reserved for future UI volume meter.
                     */
                }

                override fun onBufferReceived(
                    buffer: ByteArray?
                ) {
                    /*
                     * Not required.
                     */
                }

                override fun onEndOfSpeech() {
                    isListening = false

                    onListeningChanged(
                        false
                    )
                }

                override fun onError(
                    error: Int
                ) {
                    isListening = false

                    onListeningChanged(
                        false
                    )

                    if (
                        destroyed ||
                        listeningMode !=
                        ListeningMode.COMMAND
                    ) {
                        return
                    }

                    onError(
                        recognitionErrorMessage(
                            error
                        )
                    )
                }

                override fun onResults(
                    results: Bundle?
                ) {
                    isListening = false

                    onListeningChanged(
                        false
                    )

                    val text =
                        results
                            ?.getStringArrayList(
                                SpeechRecognizer
                                    .RESULTS_RECOGNITION
                            )
                            ?.firstOrNull()
                            ?.trim()
                            .orEmpty()

                    if (
                        listeningMode !=
                        ListeningMode.COMMAND
                    ) {
                        return
                    }

                    if (text.isBlank()) {
                        onError(
                            "I did not hear anything"
                        )
                        return
                    }

                    onResult(
                        text
                    )
                }

                override fun onPartialResults(
                    partialResults: Bundle?
                ) {
                    /*
                     * Partial results disabled.
                     */
                }

                override fun onEvent(
                    eventType: Int,
                    params: Bundle?
                ) {
                    /*
                     * Not required.
                     */
                }
            }
        )

        val intent =
            Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            ).apply {

                putExtra(
                    RecognizerIntent
                        .EXTRA_LANGUAGE_MODEL,
                    RecognizerIntent
                        .LANGUAGE_MODEL_FREE_FORM
                )

                putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE,
                    Locale.getDefault()
                )

                putExtra(
                    RecognizerIntent
                        .EXTRA_LANGUAGE_PREFERENCE,
                    Locale.getDefault()
                )

                putExtra(
                    RecognizerIntent
                        .EXTRA_PARTIAL_RESULTS,
                    false
                )

                putExtra(
                    RecognizerIntent
                        .EXTRA_MAX_RESULTS,
                    3
                )
            }

        try {
            speechRecognizer
                ?.startListening(
                    intent
                )
        } catch (exception: Exception) {
            isListening = false

            onListeningChanged(
                false
            )

            onError(
                exception.message
                    ?: "Could not start voice recognition"
            )
        }
    }

    // ---------------------------------------------------------------------
    // STOP / CLEANUP
    // ---------------------------------------------------------------------

    /**
     * Stops whichever voice mode is currently active.
     *
     * Wake engine is stopped but NOT released.
     *
     * The service owns the wake engine lifetime.
     */
    fun stopListening() {
        mainHandler.post {
            listeningMode =
                ListeningMode.IDLE

            wakeWordEngine.stop()

            onWakeStateChanged(
                false
            )

            stopRecognizerOnly()

            isListening = false

            onListeningChanged(
                false
            )
        }
    }

    private fun stopRecognizerOnly() {
        try {
            speechRecognizer?.stopListening()
        } catch (_: Exception) {
        }

        try {
            speechRecognizer?.cancel()
        } catch (_: Exception) {
        }

        try {
            speechRecognizer?.destroy()
        } catch (_: Exception) {
        }

        speechRecognizer = null
    }

    /**
     * Permanently destroys the voice layer.
     *
     * IMPORTANT:
     * WakeWordEngine.release() is NOT called here.
     *
     * AlfredAgentService owns the wake engine and releases it.
     */
    fun destroy() {
        mainHandler.post {
            if (destroyed) {
                return@post
            }

            destroyed = true

            listeningMode =
                ListeningMode.IDLE

            wakeWordEngine.stop()

            onWakeStateChanged(
                false
            )

            stopRecognizerOnly()

            textToSpeech?.stop()

            textToSpeech?.shutdown()

            textToSpeech = null

            ttsReady = false

            utteranceCallbacks.clear()

            isListening = false

            onListeningChanged(
                false
            )
        }
    }

    private fun hasMicrophonePermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECORD_AUDIO
        ) ==
            PackageManager.PERMISSION_GRANTED
    }

    private fun recognitionErrorMessage(
        error: Int
    ): String {
        return when (error) {

            SpeechRecognizer.ERROR_AUDIO ->
                "There was an audio problem"

            SpeechRecognizer.ERROR_CLIENT ->
                "Voice recognition stopped"

            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS ->
                "Microphone permission is required"

            SpeechRecognizer.ERROR_NETWORK ->
                "A network error occurred"

            SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
                "Voice recognition timed out"

            SpeechRecognizer.ERROR_NO_MATCH ->
                "I could not understand that"

            SpeechRecognizer.ERROR_RECOGNIZER_BUSY ->
                "Voice recognition is busy"

            SpeechRecognizer.ERROR_SERVER ->
                "The speech recognition service had a problem"

            SpeechRecognizer.ERROR_SPEECH_TIMEOUT ->
                "I did not hear anything"

            else ->
                "Voice recognition error"
        }
    }

    /**
     * Tiny internal logging helper so this file does not depend
     * on a project-specific logging framework.
     */
    private object LogHelper {

        fun info(
            message: String
        ) {
            android.util.Log.i(
                "ALFRED-Voice",
                message
            )
        }

        fun error(
            message: String
        ) {
            android.util.Log.e(
                "ALFRED-Voice",
                message
            )
        }
    }
}