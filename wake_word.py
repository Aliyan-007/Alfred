import time
import numpy as np
import sounddevice as sd

from openwakeword.model import Model

from voice.recorder import record_audio
from voice.stt import transcribe_audio
from brain import ask_brain
from assistants.router import detect_assistant


# ============================================================
# CONFIGURATION
# ============================================================

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

MODEL_NAME = "alexa_v0.1"

THRESHOLD = 0.5

WAKE_COOLDOWN = 1.0


# ============================================================
# WAKE WORD LISTENER
# ============================================================

def wait_for_wake_word(model):

    print()
    print("Listening for wake word...")
    print("Say 'Alexa' to activate.")

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=CHUNK_SIZE,
        dtype="int16",
        channels=1,
    ) as stream:

        while True:

            audio, overflowed = stream.read(
                CHUNK_SIZE
            )

            if overflowed:
                continue

            audio = np.frombuffer(
                audio,
                dtype=np.int16
            )

            prediction = model.predict(
                audio
            )

            # IMPORTANT:
            # OpenWakeWord returns:
            #
            # {'alexa_v0.1': score}
            #
            score = float(
                prediction.get(
                    MODEL_NAME,
                    0.0
                )
            )

            if score >= THRESHOLD:

                print()
                print("=" * 55)
                print("              WAKE WORD DETECTED")
                print("=" * 55)
                print()

                print(
                    f"Detection score: {score:.6f}"
                )

                time.sleep(
                    WAKE_COOLDOWN
                )

                return


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_command():

    print()
    print("=" * 55)
    print("              ALFRED ACTIVATED")
    print("=" * 55)
    print()

    print(
        "Listening for your command..."
    )

    print(
        "Speak now."
    )

    print()

    # ========================================================
    # RECORD
    # ========================================================

    audio_file = record_audio()

    if not audio_file:

        print(
            "No audio was recorded."
        )

        return

    print()
    print(
        "Audio recorded."
    )

    # ========================================================
    # SPEECH TO TEXT
    # ========================================================

    print(
        "Transcribing..."
    )

    user_input = transcribe_audio(
        audio_file
    )

    if not user_input:

        print()
        print(
            "I didn't catch that."
        )

        return

    print()
    print(
        f"You: {user_input}"
    )

    print()

    # ========================================================
    # EXIT
    # ========================================================

    normalized_input = (
        user_input
        .lower()
        .strip()
    )

    if normalized_input in {
        "exit",
        "bye",
        "goodbye",
        "good bye",
        "shutdown",
        "shut down",
    }:

        print(
            "ALFRED: Goodbye."
        )

        raise SystemExit


    # ========================================================
    # ASSISTANT ROUTER
    # ========================================================

    try:

        assistant = detect_assistant(
            user_input
        )

    except Exception as error:

        print()
        print(
            "Assistant router error:"
        )
        print(
            error
        )
        print()

        return


    print(
        f"Assistant: {assistant}"
    )

    print()


    # ========================================================
    # SHARED AI BRAIN
    # ========================================================

    print(
        "Thinking..."
    )

    try:

        answer = ask_brain(
            user_input
        )

    except Exception as error:

        print()
        print(
            "Brain error:"
        )
        print(
            error
        )
        print()

        return


    # ========================================================
    # DISPLAY ANSWER
    # ========================================================

    print()
    print("=" * 55)
    print(
        f"{assistant}"
    )
    print("=" * 55)
    print()

    print(
        answer
    )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 55)
    print("                    ALFRED")
    print("             WAKE WORD + BRAIN")
    print("=" * 55)
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

    # ========================================================
    # LOAD WAKE WORD ENGINE
    # ========================================================

    print(
        "Loading wake-word engine..."
    )

    try:

        model = Model(
            wakeword_models=[
                MODEL_NAME
            ]
        )

    except Exception as error:

        print()
        print(
            "Wake-word engine error:"
        )
        print(
            error
        )
        print()

        return

    print(
        "Wake-word engine ready."
    )

    print()

    print("=" * 55)
    print("              ALFRED IS READY")
    print("=" * 55)
    print()

    print(
        "Say 'Alexa' to activate."
    )

    print(
        "Then speak your command."
    )

    print(
        "Say 'exit' to shut down."
    )

    print()
    print(
        "Press Ctrl+C to stop."
    )

    print()


    # ========================================================
    # PERMANENT LOOP
    # ========================================================

    while True:

        try:

            # ------------------------------------------------
            # WAIT FOR ALEXA
            # ------------------------------------------------

            wait_for_wake_word(
                model
            )

            # ------------------------------------------------
            # HANDLE COMMAND
            # ------------------------------------------------

            handle_command()

            # ------------------------------------------------
            # RETURN TO WAKE WORD
            # ------------------------------------------------

            print()
            print("-" * 55)
            print(
                "Returning to wake-word listening..."
            )
            print("-" * 55)

        except SystemExit:

            print()
            print(
                "ALFRED: Goodbye."
            )

            break

        except KeyboardInterrupt:

            print()
            print(
                "ALFRED: Goodbye."
            )

            break

        except Exception as error:

            print()
            print(
                "SYSTEM ERROR:"
            )
            print(
                error
            )
            print()

            time.sleep(1)


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    main()
