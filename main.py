import os
import sys
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
from voice.wake_word import wait_for_wake_word, set_speaking


# =========================================================
# WAKE WORD CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

CANDIDATE_PATHS = [
    BASE_DIR / "alfred.onnx",
    BASE_DIR / "models" / "alfred.onnx",
    BASE_DIR / "voice" / "alfred.onnx",
    Path("D:/alfred/alfred.onnx"),
]

WAKE_WORD_MODEL = None
for candidate in CANDIDATE_PATHS:
    if candidate.exists():
        WAKE_WORD_MODEL = str(candidate)
        break

if not WAKE_WORD_MODEL:
    print("\n[WARNING] 'alfred.onnx' not found! Falling back to alexa_v0.1")
    WAKE_WORD_MODEL = "alexa_v0.1"
else:
    print(f"\n[WAKE WORD] Custom model loaded: {WAKE_WORD_MODEL}")


# =========================================================
# HELPER: SAFE SPEAK
# =========================================================

def safe_speak(text: str, assistant: str = "ALFRED"):
    """Block wake-word detection while Alfred speaks (kills echo bleed)."""
    try:
        set_speaking(True)
        speak(text, assistant)
    except Exception as error:
        print(f"[TTS Error] {error}")
    finally:
        # Extra echo tail to let audio drivers flush
        time.sleep(0.5)
        set_speaking(False)


# =========================================================
# STARTUP BANNER
# =========================================================

print()
print("=" * 55)
print("                    ALFRED")
print("=" * 55)
print()

# Initialize all subsystems
print("Starting ALFRED Brave browser...")
try:
    ensure_brave()
except Exception:
    pass

print("Initializing voice system...")
try:
    initialize_tts(wait=False)
except Exception:
    pass

print("Loading wake-word engine...")
try:
    wake_model = Model(wakeword_models=[WAKE_WORD_MODEL], inference_framework="onnx")
except Exception:
    try:
        wake_model = Model(wakeword_models=[WAKE_WORD_MODEL])
    except Exception as err:
        print(f"Failed loading wake word: {err}")
        raise SystemExit(1)

print("\nALFRED systems ready and online.")
print("Say 'shutdown alfred' to exit.\n")


# =========================================================
# COMMAND PROCESSOR
# =========================================================

def process_command():
    print("Listening for your command...")

    audio_file = record_audio()
    if not audio_file:
        return

    user_input = transcribe_audio(audio_file)
    if not user_input or not user_input.strip():
        return

    print()
    print(f"You: {user_input}")
    print()

    normalized_input = user_input.lower().strip().rstrip(".?!")

    # Discard mic artifacts
    if normalized_input in {"you", "thank you", "thanks", "subtitles by", "bye", "go", "yeah", "yes"}:
        print("[ALFRED] Discarded brief mic artifact.")
        return

    # Program shutdown. Require an explicit shutdown phrase so ordinary
    # microphone noise or casual speech does not terminate the assistant.
    shutdown_phrases = {
        "shutdown alfred",
        "exit alfred",
        "close alfred",
        "quit alfred",
        "alfred shutdown",
    }
    if (
        normalized_input in shutdown_phrases
        or normalized_input.endswith(" shutdown alfred")
        or normalized_input.startswith("shutdown alfred ")
    ):
        print("ALFRED: Goodbye, Sir.")
        safe_speak("Goodbye, Sir.", "ALFRED")
        raise SystemExit

    # Standby
    if normalized_input in {"stop listening", "go to sleep", "stand down"}:
        print("ALFRED: Standing down. Call me when you need me, Sir.")
        safe_speak("Standing down. Call me when you need me, Sir.", "ALFRED")
        return

    # Persona
    try:
        assistant = detect_assistant(user_input)
    except Exception:
        assistant = "ALFRED"

    # Dispatcher
    try:
        tool_result = handle_command(user_input)
        if tool_result is not None:
            if isinstance(tool_result, tuple):
                answer = str(tool_result[1]) if len(tool_result) > 1 and tool_result[1] else str(tool_result[0])
            else:
                answer = str(tool_result)
        else:
            answer = str(ask_brain(user_input))
    except Exception as error:
        answer = f"I encountered an error, Sir: {error}"

    print(f"{assistant}: {answer}")
    print()
    safe_speak(answer, assistant)


# =========================================================
# MAIN LOOP
# =========================================================

while True:
    try:
        wait_for_wake_word(wake_model)
        process_command()
        time.sleep(1.0)

    except SystemExit:
        print("\nALFRED: Shutdown complete.")
        break
    except KeyboardInterrupt:
        print("\nALFRED: Goodbye, Sir.")
        break
    except Exception as error:
        print(f"\nSystem error: {error}\n")
        time.sleep(1.0)