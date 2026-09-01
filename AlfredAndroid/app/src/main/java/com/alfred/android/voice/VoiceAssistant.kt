package com.alfred.android.voice

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
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
) : TextToSpeech.OnInitListener {

    private var speechRecognizer: SpeechRecognizer? = null

    private var textToSpeech: TextToSpeech? = null

    private var ttsReady = false

    private var isListening = false

    private var continuousMode = false

    private var destroyed = false

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

    fun startListening(
        continuous: Boolean = false
    ) {

        continuousMode =
            continuous

        if (destroyed) {
            return
        }

        if (
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED
        ) {

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

        startRecognition()
    }

    private fun startRecognition() {

        if (destroyed) {
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

                    val message =
                        recognitionErrorMessage(
                            error
                        )

                    if (
                        continuousMode &&
                        !destroyed &&
                        error != SpeechRecognizer.ERROR_CLIENT
                    ) {

                        onError(
                            message
                        )

                        restartRecognition()
                    } else {

                        onError(
                            message
                        )
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

                    if (
                        text.isNullOrBlank()
                    ) {

                        if (
                            continuousMode &&
                            !destroyed
                        ) {

                            restartRecognition()

                        } else {

                            onError(
                                "I did not hear anything"
                            )
                        }

                        return
                    }

                    onResult(
                        text
                    )

                    if (
                        continuousMode &&
                        !destroyed
                    ) {

                        restartRecognition()
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

                putExtra(
                    RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                    false
                )

                putExtra(
                    RecognizerIntent.EXTRA_MAX_RESULTS,
                    3
                )
            }

        speechRecognizer?.startListening(
            intent
        )
    }

    private fun restartRecognition() {

        if (
            destroyed ||
            !continuousMode
        ) {
            return
        }

        Thread {
            try {

                Thread.sleep(
                    500
                )

            } catch (
                ignored: InterruptedException
            ) {
            }

            if (
                !destroyed &&
                continuousMode
            ) {

                android.os.Handler(
                    android.os.Looper.getMainLooper()
                ).post {

                    if (
                        !destroyed &&
                        continuousMode
                    ) {

                        startRecognition()
                    }
                }
            }

        }.start()
    }

    fun stopListening() {

        continuousMode =
            false

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

        continuousMode = false

        stopRecognizerOnly()

        textToSpeech?.stop()

        textToSpeech?.shutdown()

        textToSpeech = null

        ttsReady = false

        isListening = false
    }
}