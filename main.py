from brain import ask_brain
from tools.browser import ensure_brave
from tools.dispatcher import handle_command
from assistants.router import detect_assistant
from voice.recorder import record_audio
from voice.stt import transcribe_audio
from voice.tts import speak, initialize_tts


# =========================================================
# STARTUP
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
print("Starting ALFRED Brave browser...")

if ensure_brave():
    print("ALFRED Brave browser is ready.")
else:
    print("WARNING: ALFRED Brave browser could not be started.")

print()

print()

print("Initializing voice system...")

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

print("Press ENTER to speak.")
print("Say 'exit' to shut down.")

print()


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        # =================================================
        # WAIT FOR ENTER
        # =================================================

        input(
            "Press ENTER to speak: "
        )

        # =================================================
        # RECORD
        # =================================================

        audio_file = record_audio()

        if not audio_file:
            print()
            continue

        # =================================================
        # SPEECH -> TEXT
        # =================================================

        user_input = transcribe_audio(
            audio_file
        )

        if not user_input:

            print(
                "I didn't catch that."
            )

            print()

            continue

        print()
        print(
            f"You: {user_input}"
        )
        print()

        # =================================================
        # EXIT
        # =================================================

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
        }:

            print(
                "ALFRED: Goodbye."
            )

            try:

                speak(
                    "Goodbye.",
                    "ALFRED",
                )

            except Exception:
                pass

            break

        # =================================================
        # ASSISTANT
        # =================================================

        assistant = detect_assistant(
            user_input
        )

        # =================================================
        # COMMAND / AI BRAIN
        # =================================================

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

            print()
            print(
                "Brain error:"
            )
            print(
                error
            )
            print()

            continue

        # =================================================
        # DISPLAY
        # =================================================

        print(
            f"{assistant}: {answer}"
        )

        print()

        # =================================================
        # TTS
        # =================================================

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

    # =====================================================
    # CTRL+C
    # =====================================================

    except KeyboardInterrupt:

        print()
        print(
            "ALFRED: Goodbye.Sir"
        )

        try:

            speak(
                "Goodbye.Sir",
                "ALFRED",
            )

        except Exception:
            pass

        break

    # =====================================================
    # SYSTEM ERROR
    # =====================================================

    except Exception as error:

        print()
        print(
            "System error:"
        )
        print(
            error
        )
        print()