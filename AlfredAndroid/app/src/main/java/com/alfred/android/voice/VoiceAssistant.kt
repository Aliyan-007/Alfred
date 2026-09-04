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
import androidx.core.content.ContextCompat
import java.util.Locale

class VoiceAssistant(
    private val context: Context,
    private val onListeningChanged: (Boolean) -> Unit,
    private val onResult: (String) -> Unit,
    private val onError: (String) -> Unit,
    private val onWakeWordDetected: () -> Unit = {},
) : TextToSpeech.OnInitListener {

    private enum class ListeningMode {
        IDLE,
        WAKE_WORD,
        COMMAND
    }

    private var speechRecognizer: SpeechRecognizer? = null

    private var textToSpeech: TextToSpeech? = null

    private var ttsReady = false

    private var isListening = false

    private var listeningMode =
        ListeningMode.IDLE

    private var destroyed = false

    private val mainHandler =
        Handler(
            Looper.getMainLooper()
        )

    init {

        textToSpeech =
            TextToSpeech(
                context.applicationContext,
                this
            )
    }

    override fun onInit(
        status: Int
    ) {

        if (
            status == TextToSpeech.SUCCESS
        ) {

            ttsReady = true

            textToSpeech?.language =
                Locale.US

            textToSpeech?.setSpeechRate(
                1.0f
            )

            textToSpeech?.setPitch(
                1.0f
            )
        }
    }

    /**
     * Starts wake-word mode.
     *
     * The recognizer continuously listens for
     * "Alfred", "Hey Alfred", etc.
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

        if (
            !SpeechRecognizer.isRecognitionAvailable(
                context
            )
        ) {

            onError(
                "Speech recognition is not available on this phone"
            )

            return
        }

        listeningMode =
            ListeningMode.WAKE_WORD

        startRecognition()
    }

    /**
     * Starts normal command listening.
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
            !SpeechRecognizer.isRecognitionAvailable(
                context
            )
        ) {

            onError(
                "Speech recognition is not available on this phone"
            )

            return
        }

        listeningMode =
            ListeningMode.COMMAND

        startRecognition()
    }

    /**
     * Kept for compatibility with the existing service.
     *
     * continuous=true now means command listening
     * that restarts after every recognition result.
     */
    fun startListening(
        continuous: Boolean = false
    ) {

        if (continuous) {

            startCommandListening()

        } else {

            startCommandListening()
        }
    }

    private fun startRecognition() {

        if (
            destroyed ||
            listeningMode == ListeningMode.IDLE
        ) {
            return
        }

        stopRecognizerOnly()

        speechRecognizer =
            SpeechRecognizer.createSpeechRecognizer(
                context
            )

        speechRecognizer?.setRecognitionListener(
            object : RecognitionListener {

                override fun onReadyForSpeech(
                    params: Bundle?
                ) {

                    isListening = true

                    onListeningChanged(
                        true
                    )
                }

                override fun onBeginningOfSpeech() {
                }

                override fun onRmsChanged(
                    rmsdB: Float
                ) {
                }

                override fun onBufferReceived(
                    buffer: ByteArray?
                ) {
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

                    if (destroyed) {
                        return
                    }

                    val message =
                        recognitionErrorMessage(
                            error
                        )

                    when (
                        listeningMode
                    ) {

                        ListeningMode.WAKE_WORD -> {

                            /*
                             * Wake mode should keep
                             * listening after normal
                             * recognition errors.
                             */
                            if (
                                error !=
                                SpeechRecognizer.ERROR_CLIENT
                            ) {

                                restartRecognition()
                            }
                        }

                        ListeningMode.COMMAND -> {

                            onError(
                                message
                            )
                        }

                        ListeningMode.IDLE -> {
                        }
                    }
                }

                override fun onResults(
                    results: Bundle?
                ) {

                    isListening = false

                    onListeningChanged(
                        false
                    )

                    val matches =
                        results?.getStringArrayList(
                            SpeechRecognizer.RESULTS_RECOGNITION
                        )

                    val text =
                        matches
                            ?.firstOrNull()
                            ?.trim()
                            .orEmpty()

                    when (
                        listeningMode
                    ) {

                        ListeningMode.WAKE_WORD -> {

                            if (
                                containsWakeWord(
                                    text
                                )
                            ) {

                                android.util.Log.i(
                                    TAG,
                                    "Wake word detected: $text"
                                )

                                /*
                                 * Stop wake recognition
                                 * before handing control
                                 * to command mode.
                                 */
                                stopRecognizerOnly()

                                onWakeWordDetected()

                            } else {

                                /*
                                 * Nothing relevant.
                                 * Continue waiting for
                                 * Alfred.
                                 */
                                restartRecognition()
                            }
                        }

                        ListeningMode.COMMAND -> {

                            if (
                                text.isBlank()
                            ) {

                                onError(
                                    "I did not hear anything"
                                )

                                return
                            }

                            onResult(
                                text
                            )
                        }

                        ListeningMode.IDLE -> {
                        }
                    }
                }

                override fun onPartialResults(
                    partialResults: Bundle?
                ) {
                }

                override fun onEvent(
                    eventType: Int,
                    params: Bundle?
                ) {
                }
            }
        )

        val intent =
            Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            ).apply {

                putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                    RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                )

                putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE,
                    Locale.getDefault()
                )

                putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                    Locale.getDefault()
                )

                /*
                 * We only need the final result.
                 */
                putExtra(
                    RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                    false
                )

                putExtra(
                    RecognizerIntent.EXTRA_MAX_RESULTS,
                    3
                )
            }

        try {

            speechRecognizer?.startListening(
                intent
            )

        } catch (
            error: Exception
        ) {

            android.util.Log.e(
                TAG,
                "Failed to start SpeechRecognizer",
                error
            )

            isListening = false

            onListeningChanged(
                false
            )

            onError(
                error.message
                    ?: "Could not start voice recognition"
            )
        }
    }

    private fun containsWakeWord(
        text: String
    ): Boolean {

        if (text.isBlank()) {
            return false
        }

        val normalized =
            text
                .lowercase(Locale.US)
                .replace(
                    Regex("[^a-z0-9 ]"),
                    " "
                )
                .replace(
                    Regex("\\s+"),
                    " "
                )
                .trim()

        if (normalized.isBlank()) {
            return false
        }

        val words =
            normalized.split(" ")

        /*
         * Accept:
         *
         * Alfred
         * hey Alfred
         * hello Alfred
         * okay Alfred
         * hi Alfred
         *
         * Also tolerates common STT variations.
         */
        val wakeWords =
            setOf(
                "alfred",
                "alford",
                "alfred",
                "alfred"
            )

        return words.any { word ->
            word in wakeWords
        }
    }

    private fun restartRecognition() {

        if (
            destroyed ||
            listeningMode == ListeningMode.IDLE
        ) {
            return
        }

        mainHandler.postDelayed(
            {

                if (
                    !destroyed &&
                    listeningMode !=
                    ListeningMode.IDLE
                ) {

                    startRecognition()
                }

            },
            500L
        )
    }

    fun stopListening() {

        listeningMode =
            ListeningMode.IDLE

        stopRecognizerOnly()

        isListening = false

        onListeningChanged(
            false
        )
    }

    private fun stopRecognizerOnly() {

        try {

            speechRecognizer?.stopListening()

        } catch (
            ignored: Exception
        ) {
        }

        try {

            speechRecognizer?.cancel()

        } catch (
            ignored: Exception
        ) {
        }

        try {

            speechRecognizer?.destroy()

        } catch (
            ignored: Exception
        ) {
        }

        speechRecognizer =
            null
    }

    fun speak(
        text: String
    ) {

        if (
            !ttsReady ||
            text.isBlank() ||
            destroyed
        ) {
            return
        }

        val cleanText =
            cleanForSpeech(
                text
            )

        if (
            cleanText.isBlank()
        ) {
            return
        }

        textToSpeech?.speak(
            cleanText,
            TextToSpeech.QUEUE_FLUSH,
            null,
            "alfred_voice"
        )
    }

    private fun cleanForSpeech(
        text: String
    ): String {

        return text
            .replace(
                Regex("[^A-Za-z0-9 .,!?'-]"),
                " "
            )
            .replace(
                Regex("\\s+"),
                " "
            )
            .trim()
    }

    private fun hasMicrophonePermission(): Boolean {

        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
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

    fun destroy() {

        destroyed = true

        listeningMode =
            ListeningMode.IDLE

        mainHandler.removeCallbacksAndMessages(
            null
        )

        stopRecognizerOnly()

        textToSpeech?.stop()

        textToSpeech?.shutdown()

        textToSpeech = null

        ttsReady = false

        isListening = false
    }

    companion object {

        private const val TAG =
            "ALFRED-Voice"
    }
}