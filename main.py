from openwakeword.model import Model

from brain import ask_brain
from tools.dispatcher import handle_command
from tools.browser import ensure_brave
from assistants.router import detect_assistant
from voice.recorder import record_audio
from voice.stt import transcribe_audio
from voice.tts import speak, initialize_tts
from voice.wake_word import wait_for_wake_word
import time

from openwakeword.model import Model


# =========================================================
# CONFIGURATION
# =========================================================

WAKE_WORD_MODEL = "alexa_v0.1"


# =========================================================
# STARTUP
# =========================================================

print()

print(
    "=" * 55
)

print(
    "                    ALFRED"
)

print(
    "=" * 55
)

print()

print(
    "Shared AI system online."
)

print()

print(
    "English  -> ALFRED"
)

print(
    "Urdu     -> F.R.I.D.A.Y."
)

print()


# =========================================================
# BRAVE
# =========================================================

print(
    "Starting ALFRED Brave browser..."
)

try:

    if ensure_brave():

        print(
            "ALFRED Brave browser is ready."
        )

    else:

        print(
            "WARNING: Brave browser could not be started."
        )

except Exception as error:

    print(
        "Brave startup error:"
    )

    print(
        error
    )

print()


# =========================================================
# TTS
# =========================================================

print(
    "Initializing voice system..."
)

try:

    initialize_tts(
        wait=False
    )

    print(
        "Voice system initialized."
    )

except Exception as error:

    print(
        "Voice initialization failed:"
    )

    print(
        error
    )

print()


# =========================================================
# WAKE WORD
# =========================================================

print(
    "Loading wake-word engine..."
)

try:

    wake_model = Model(
        wakeword_models=[
            WAKE_WORD_MODEL
        ]
    )

except Exception as error:

    print(
        "Wake-word engine error:"
    )

    print(
        error
    )

    raise SystemExit(1)

print(
    "Wake-word engine ready."
)

print()

print(
    "ALFRED is ready."
)

print(
    "Say 'Alexa' to activate."
)

print(
    "Say 'exit' to shut down ALFRED."
)

print()


# =========================================================
# PROCESS ONE COMMAND
# =========================================================

def process_command():

    print(
        "Listening for your command..."
    )

    audio_file = record_audio()

    if not audio_file:

        print(
            "No audio was recorded."
        )

        return


    user_input = transcribe_audio(
        audio_file
    )

    if not user_input:

        print(
            "I didn't catch that."
        )

        return

    print()

    print(
        f"You: {user_input}"
    )

    print()

    normalized_input = (
        user_input
        .lower()
        .strip()
    )

    # =====================================================
    # EXIT
    # =====================================================

    # =====================================================
# EXIT / SHUTDOWN
# =====================================================

    if normalized_input in {
        "exit",
        "bye",
        "goodbye",
        "good bye",
        " shutdown",
        "shut down",
        "shutdown alfred",
    }:

        print(
            "ALFRED: Goodbye, Sir."
        )

        try:
            speak(
                "Goodbye, Sir.",
                "ALFRED",
            )
        except Exception:
            pass

        raise SystemExit


# =====================================================
# RETURN TO WAKE-WORD LISTENING
# =====================================================

        if normalized_input in {
            "stop listening",
            "go back to sleep",
        }:

            print(
                "ALFRED: Returning to wake-word listening, Sir."
            )

            try:
                speak(
                    "Returning to wake-word listening, Sir.",
                    "ALFRED",
                )
            except Exception:
                pass

            return


# ---------------------------------------------------------
# FULL SHUTDOWN
# ---------------------------------------------------------

    
    # =====================================================
    # ASSISTANT ROUTER
    # =====================================================

    try:

        assistant = detect_assistant(
            user_input
        )

    except Exception as error:

        print(
            "Assistant router error:"
        )

        print(
            error
        )

        return

    # =====================================================
    # DISPATCHER FIRST
    # =====================================================

    try:

        tool_result = handle_command(
            user_input
        )

        if tool_result is not None:

            answer = tool_result

        else:

            answer = ask_brain(
                user_input
            )

    except Exception as error:

        print(
            "Brain error:"
        )

        print(
            error
        )

        return

    # =====================================================
    # RESPONSE
    # =====================================================

    print(
        f"{assistant}: {answer}"
    )

    print()

    try:

        speak(
            answer,
            assistant,
        )

    except Exception as error:

        print(
            "TTS error:"
        )

        print(
            error
        )

    print()


# =========================================================
# PERMANENT WAKE LOOP
# =========================================================

while True:

    try:

        time.sleep(1.5)

        wait_for_wake_word(
            wake_model
        )

        process_command()

        print()

        print(
            "ALFRED is ready."
        )

        print()

    except SystemExit:

        print()
        print(
            "ALFRED: Shutdown complete."
        )

        break

    except KeyboardInterrupt:

        print()

        print(
            "ALFRED: Goodbye, Sir."
        )

        break

    except Exception as error:

        print()

        print(
            "System error:"
        )

        print(
            error
        )

        print()

        time.sleep(
            1
        )