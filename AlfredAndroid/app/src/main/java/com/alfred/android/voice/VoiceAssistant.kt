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

class VoiceAssistant(
    private val context: Context,
    private val wakeWordEngine: WakeWordEngine,
    private val onListeningChanged: (Boolean) -> Unit,
    private val onResult: (String) -> Unit,
    private val onError: (String) -> Unit,
    private val onWakeWordDetected: () -> Unit = {},
) : TextToSpeech.OnInitListener {

    private enum class ListeningMode {
        IDLE,
        WAKE_WORD,
        COMMAND,
    }

    private var speechRecognizer: SpeechRecognizer? = null
    private var textToSpeech: TextToSpeech? = null
    private var ttsReady = false
    private var isListening = false
    private var listeningMode = ListeningMode.IDLE
    private var destroyed = false
    private val utteranceCallbacks = ConcurrentHashMap<String, () -> Unit>()
    private val mainHandler = Handler(Looper.getMainLooper())

    init {
        textToSpeech = TextToSpeech(context.applicationContext, this)
    }

    override fun onInit(status: Int) {
        if (status != TextToSpeech.SUCCESS) return

        ttsReady = true
        configureBritishMaleVoice()
        textToSpeech?.setSpeechRate(0.96f)
        textToSpeech?.setPitch(0.98f)
        textToSpeech?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) = Unit
            override fun onDone(utteranceId: String?) = finishUtterance(utteranceId)
            @Deprecated("Deprecated in Android API")
            override fun onError(utteranceId: String?) = finishUtterance(utteranceId)
            override fun onError(utteranceId: String?, errorCode: Int) = finishUtterance(utteranceId)
        })
    }

    /** Starts genuine local wake-word detection. SpeechRecognizer is NOT used here. */
    fun startWakeWordListening() {
        if (destroyed) return
        if (!hasMicrophonePermission()) {
            onError("Microphone permission is not granted")
            return
        }

        stopRecognizerOnly()
        listeningMode = ListeningMode.WAKE_WORD
        isListening = false
        onListeningChanged(false)
        wakeWordEngine.start()
    }

    /** Starts normal speech recognition after the wake word or during a conversation. */
    fun startCommandListening() {
        if (destroyed) return
        if (!hasMicrophonePermission()) {
            onError("Microphone permission is not granted")
            return
        }
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            onError("Speech recognition is not available on this phone")
            return
        }

        wakeWordEngine.stop()
        listeningMode = ListeningMode.COMMAND
        startRecognition()
    }

    /** Kept for compatibility with existing callers; it is command listening only. */
    fun startListening(continuous: Boolean = false) = startCommandListening()

    private fun startRecognition() {
        if (destroyed || listeningMode != ListeningMode.COMMAND) return

        stopRecognizerOnly()
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                isListening = true
                onListeningChanged(true)
            }

            override fun onBeginningOfSpeech() = Unit
            override fun onRmsChanged(rmsdB: Float) = Unit
            override fun onBufferReceived(buffer: ByteArray?) = Unit

            override fun onEndOfSpeech() {
                isListening = false
                onListeningChanged(false)
            }

            override fun onError(error: Int) {
                isListening = false
                onListeningChanged(false)
                if (destroyed || listeningMode != ListeningMode.COMMAND) return
                onError(recognitionErrorMessage(error))
            }

            override fun onResults(results: Bundle?) {
                isListening = false
                onListeningChanged(false)

                val text = results
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                    ?.trim()
                    .orEmpty()

                if (listeningMode != ListeningMode.COMMAND) return
                if (text.isBlank()) {
                    onError("I did not hear anything")
                    return
                }
                onResult(text)
            }

            override fun onPartialResults(partialResults: Bundle?) = Unit
            override fun onEvent(eventType: Int, params: Bundle?) = Unit
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
        }

        try {
            speechRecognizer?.startListening(intent)
        } catch (error: Exception) {
            isListening = false
            onListeningChanged(false)
            onError(error.message ?: "Could not start voice recognition")
        }
    }

    fun stopListening() {
        listeningMode = ListeningMode.IDLE
        wakeWordEngine.stop()
        stopRecognizerOnly()
        isListening = false
        onListeningChanged(false)
    }

    private fun stopRecognizerOnly() {
        try { speechRecognizer?.stopListening() } catch (_: Exception) { }
        try { speechRecognizer?.cancel() } catch (_: Exception) { }
        try { speechRecognizer?.destroy() } catch (_: Exception) { }
        speechRecognizer = null
    }

    fun speak(text: String, onDone: (() -> Unit)? = null) {
        if (text.isBlank() || destroyed) {
            onDone?.invoke()
            return
        }

        val cleanText = cleanForSpeech(text)
        if (cleanText.isBlank() || !ttsReady || textToSpeech == null) {
            onDone?.invoke()
            return
        }

        val utteranceId = "alfred-${UUID.randomUUID()}"
        if (onDone != null) utteranceCallbacks[utteranceId] = onDone

        val result = textToSpeech?.speak(
            cleanText,
            TextToSpeech.QUEUE_FLUSH,
            null,
            utteranceId,
        )

        if (result == TextToSpeech.ERROR) {
            utteranceCallbacks.remove(utteranceId)
            onDone?.invoke()
        }
    }

    private fun finishUtterance(utteranceId: String?) {
        if (utteranceId == null) return
        utteranceCallbacks.remove(utteranceId)?.let { callback -> mainHandler.post(callback) }
    }

    private fun configureBritishMaleVoice() {
        val tts = textToSpeech ?: return
        val voices = runCatching { tts.voices }.getOrNull().orEmpty()
        val britishVoices = voices.filter {
            it.locale.language == Locale.UK.language && it.locale.country == Locale.UK.country
        }
        val maleHints = listOf("male", "alan", "arthur", "george", "rjs", "daniel")

        val selected = britishVoices.sortedWith(
            compareByDescending<android.speech.tts.Voice> { voice ->
                val name = voice.name.lowercase(Locale.US)
                maleHints.count { hint -> hint in name }
            }.thenBy { it.isNetworkConnectionRequired }
                .thenByDescending { it.quality }
                .thenBy { it.latency }
        ).firstOrNull()

        if (selected != null) {
            tts.setVoice(selected)
            android.util.Log.i(TAG, "Selected British TTS voice: ${selected.name}")
        } else {
            tts.setLanguage(Locale.UK)
            android.util.Log.w(TAG, "No dedicated British voice found; using en-GB fallback")
        }
    }

    private fun cleanForSpeech(text: String): String = text
        .replace(Regex("https?://\\S+"), "web link")
        .replace(Regex("[^A-Za-z0-9 .,!?'-]"), " ")
        .replace(Regex("\\s+"), " ")
        .trim()

    private fun hasMicrophonePermission(): Boolean =
        ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED

    private fun recognitionErrorMessage(error: Int): String = when (error) {
        SpeechRecognizer.ERROR_AUDIO -> "There was an audio problem"
        SpeechRecognizer.ERROR_CLIENT -> "Voice recognition stopped"
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission is required"
        SpeechRecognizer.ERROR_NETWORK -> "A network error occurred"
        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Voice recognition timed out"
        SpeechRecognizer.ERROR_NO_MATCH -> "I could not understand that"
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Voice recognition is busy"
        SpeechRecognizer.ERROR_SERVER -> "The speech recognition service had a problem"
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "I did not hear anything"
        else -> "Voice recognition error"
    }

    fun destroy() {
        destroyed = true
        listeningMode = ListeningMode.IDLE
        mainHandler.removeCallbacksAndMessages(null)
        wakeWordEngine.release()
        stopRecognizerOnly()
        textToSpeech?.stop()
        textToSpeech?.shutdown()
        textToSpeech = null
        ttsReady = false
        utteranceCallbacks.clear()
        isListening = false
    }

    companion object {
        private const val TAG = "ALFRED-Voice"
    }
}
