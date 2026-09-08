import os
import time
from pathlib import Path

from openwakeword.model import Model

from assistants.router import detect_assistant
from brain import ask_brain
from tools.browser import ensure_brave
from tools.dispatcher import handle_command
from voice.recorder import record_audio
from voice.stt import transcribe_audio
from voice.tts import initialize_tts, speak
from voice.wake_word import wait_for_wake_word


# =========================================================
# CONFIGURATION
# =========================================================

# If you have custom alfred.onnx in root or models folder:
# WAKE_WORD_MODEL = "models/alfred.onnx" if Path("models/alfred.onnx").exists() else "alexa_v0.1"
WAKE_WORD_MODEL = "alexa_v0.1"


# =========================================================
# STARTUP BANNER
# =========================================================

print()
print("=" * 55)
print("                    ALFRED")
print("=" * 55)
print()
print("Shared AI system online.")
print()
print("English  -> ALFRED")
print("Urdu     -> F.R.I.D.A.Y.")
print()


# =========================================================
# BRAVE BROWSER (CDP)
# =========================================================

print("Starting ALFRED Brave browser...")
try:
    if ensure_brave():
        print("ALFRED Brave browser is ready.")
    else:
        print("WARNING: Brave browser could not be started.")
except Exception as error:
    print(f"Brave startup error: {error}")

print()


# =========================================================
# TTS INITIALIZATION
# =========================================================

print("Initializing voice system...")
try:
    initialize_tts(wait=False)
    print("Voice system initialized.")
except Exception as error:
    print(f"Voice initialization failed: {error}")

print()


# =========================================================
# WAKE WORD ENGINE
# =========================================================

print("Loading wake-word engine...")
try:
    wake_model = Model(wakeword_models=[WAKE_WORD_MODEL])
except Exception as error:
    print(f"Wake-word engine error: {error}")
    raise SystemExit(1)

print("Wake-word engine ready.")
print()
print("ALFRED is ready.")
print(f"Wake phrase active ({WAKE_WORD_MODEL}).")
print("Say 'exit' or 'shutdown alfred' to stop.")
print()


# =========================================================
# PROCESS ONE COMMAND
# =========================================================

def process_command():
    print("Listening for your command...")

    audio_file = record_audio()
    if not audio_file:
        print("No audio was recorded.")
        return

    user_input = transcribe_audio(audio_file)
    if not user_input:
        print("I didn't catch that.")
        return

    print()
    print(f"You: {user_input}")
    print()

    normalized_input = user_input.lower().strip()

    # =====================================================
    # 1. ASSISTANT EXIT / CLOSE APPLICATION
    # =====================================================
    if normalized_input in {
        "exit",
        "bye",
        "goodbye",
        "good bye",
        "quit",
        "shutdown alfred",
        "close alfred",
        "exit alfred",
    }:
        print("ALFRED: Goodbye, Sir.")
        try:
            speak("Goodbye, Sir.", "ALFRED")
        except Exception:
            pass
        raise SystemExit

    # =====================================================
    # 2. RETURN TO SLEEP / WAKE-WORD STANDBY
    # =====================================================
    if normalized_input in {
        "stop listening",
        "go to sleep",
        "go back to sleep",
        "stand down",
        "cancel",
    }:
        print("ALFRED: Returning to wake-word listening, Sir.")
        try:
            speak("Returning to wake-word listening, Sir.", "ALFRED")
        except Exception:
            pass
        return

    # =====================================================
    # 3. ASSISTANT ROUTER (Language / Persona)
    # =====================================================
    try:
        assistant = detect_assistant(user_input)
    except Exception as error:
        print(f"Assistant router error: {error}")
        assistant = "ALFRED"

    # =====================================================
    # 4. DETERMINISTIC DISPATCHER FIRST
    # =====================================================
    try:
        tool_result = handle_command(user_input)

        if tool_result is not None:
            answer = tool_result
        else:
            # 5. AI Brain Fallback
            answer = ask_brain(user_input)

    except Exception as error:
        print(f"Processing error: {error}")
        return

    # =====================================================
    # 6. RESPONSE / TTS
    # =====================================================
    print(f"{assistant}: {answer}")
    print()

    try:
        speak(answer, assistant)
    except Exception as error:
        print(f"TTS error: {error}")

    print()


# =========================================================
# PERMANENT WAKE LOOP
# =========================================================

while True:
    try:
        time.sleep(1.0)
        wait_for_wake_word(wake_model)
        process_command()

        print()
        print("ALFRED is ready.")
        print()

    except SystemExit:
        print()
        print("ALFRED: Shutdown complete.")
        break

    except KeyboardInterrupt:
        print()
        print("ALFRED: Goodbye, Sir.")
        break

    except Exception as error:
        print()
        print(f"System error: {error}")
        print()
        time.sleep(1)