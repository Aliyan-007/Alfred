import re
import threading

import msvcrt
import sounddevice as sd

from piper import PiperVoice


# =========================================================
# PATHS
# =========================================================

BASE_DIR = __import__("pathlib").Path(__file__).resolve().parent.parent

MODELS_DIR = BASE_DIR / "models" / "piper"

ALFRED_MODEL = MODELS_DIR / "en_GB-alan-medium.onnx"

FRIDAY_MODEL = MODELS_DIR / "ur_PK-aegis_female-medium.onnx"


# =========================================================
# VOICE STORAGE
# =========================================================

_alfred_voice = None
_friday_voice = None


# =========================================================
# LOADING EVENTS
# =========================================================

_alfred_ready = threading.Event()
_friday_ready = threading.Event()

_loading_started = False

_loading_lock = threading.Lock()


# =========================================================
# LOADING ERRORS
# =========================================================

_alfred_error = None
_friday_error = None


# =========================================================
# SPEECH CONTROL
# =========================================================

_stop_event = threading.Event()

_playing = False


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_for_speech(text: str) -> str:
    """
    Convert AI output into plain text suitable for speech.
    """

    # -----------------------------------------------------
    # Remove URLs
    # -----------------------------------------------------

    text = re.sub(
        r"https?://\S+",
        "",
        text,
    )

    # -----------------------------------------------------
    # Remove code blocks
    # -----------------------------------------------------

    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL,
    )

    # -----------------------------------------------------
    # Remove Markdown
    # -----------------------------------------------------

    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")
    text = text.replace("_", "")
    text = text.replace("`", "")

    # -----------------------------------------------------
    # Remove headings
    # -----------------------------------------------------

    text = re.sub(
        r"^\s*#+\s*",
        "",
        text,
        flags=re.MULTILINE,
    )

    # -----------------------------------------------------
    # Remove bullets
    # -----------------------------------------------------

    text = re.sub(
        r"^\s*[-•]\s+",
        "",
        text,
        flags=re.MULTILINE,
    )

    # -----------------------------------------------------
    # Remove brackets
    # -----------------------------------------------------

    text = re.sub(
        r"[\[\]{}()<>]",
        " ",
        text,
    )

    # -----------------------------------------------------
    # Remove decorative symbols
    # -----------------------------------------------------

    text = re.sub(
        r"[|~^=]+",
        " ",
        text,
    )

    # -----------------------------------------------------
    # Remove excessive whitespace
    # -----------------------------------------------------

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# LOAD ALFRED
# =========================================================

def _load_alfred():

    global _alfred_voice
    global _alfred_error

    try:

        print(
            "Loading ALFRED voice...",
            flush=True,
        )

        if not ALFRED_MODEL.exists():

            raise FileNotFoundError(
                f"ALFRED model not found:\n{ALFRED_MODEL}"
            )

        _alfred_voice = PiperVoice.load(
            str(ALFRED_MODEL)
        )

        print(
            "ALFRED voice loaded.",
            flush=True,
        )

    except Exception as error:

        _alfred_error = error

        print(
            f"ALFRED voice loading failed: {error}",
            flush=True,
        )

    finally:

        _alfred_ready.set()


# =========================================================
# LOAD F.R.I.D.A.Y.
# =========================================================

def _load_friday():

    global _friday_voice
    global _friday_error

    try:

        print(
            "Loading F.R.I.D.A.Y. voice...",
            flush=True,
        )

        if not FRIDAY_MODEL.exists():

            raise FileNotFoundError(
                f"F.R.I.D.A.Y. model not found:\n{FRIDAY_MODEL}"
            )

        _friday_voice = PiperVoice.load(
            str(FRIDAY_MODEL)
        )

        print(
            "F.R.I.D.A.Y. voice loaded.",
            flush=True,
        )

    except Exception as error:

        _friday_error = error

        print(
            f"F.R.I.D.A.Y. voice loading failed: {error}",
            flush=True,
        )

    finally:

        _friday_ready.set()


# =========================================================
# INITIALIZE TTS
# =========================================================

def initialize_tts(wait=False):
    """
    Start loading both voices in parallel.

    wait=False:
        Return immediately.

    wait=True:
        Wait until both voices are loaded.
    """

    global _loading_started

    with _loading_lock:

        if not _loading_started:

            _loading_started = True

            print(
                "Starting voice system...",
                flush=True,
            )

            # -------------------------------------------------
            # ALFRED loading thread
            # -------------------------------------------------

            alfred_thread = threading.Thread(
                target=_load_alfred,
                name="ALFRED-TTS-Loader",
                daemon=True,
            )

            # -------------------------------------------------
            # F.R.I.D.A.Y. loading thread
            # -------------------------------------------------

            friday_thread = threading.Thread(
                target=_load_friday,
                name="FRIDAY-TTS-Loader",
                daemon=True,
            )

            # -------------------------------------------------
            # Start both at the same time
            # -------------------------------------------------

            alfred_thread.start()
            friday_thread.start()

    # ---------------------------------------------------------
    # Optional wait
    # ---------------------------------------------------------

    if wait:

        _alfred_ready.wait()
        _friday_ready.wait()

        if _alfred_error:

            raise RuntimeError(
                f"ALFRED voice failed to load: "
                f"{_alfred_error}"
            )

        if _friday_error:

            raise RuntimeError(
                f"F.R.I.D.A.Y. voice failed to load: "
                f"{_friday_error}"
            )

        print(
            "TTS engine ready.",
            flush=True,
        )


# =========================================================
# WAIT FOR SPECIFIC VOICE
# =========================================================

def _wait_for_voice(assistant_name: str):

    if not _loading_started:

        initialize_tts(
            wait=False
        )

    if assistant_name == "ALFRED":

        print(
            "Waiting for ALFRED voice...",
            end="\r",
            flush=True,
        )

        _alfred_ready.wait()

        if _alfred_error:

            raise RuntimeError(
                f"ALFRED voice failed to load: "
                f"{_alfred_error}"
            )

        return _alfred_voice

    if assistant_name == "F.R.I.D.A.Y.":

        print(
            "Waiting for F.R.I.D.A.Y. voice...",
            end="\r",
            flush=True,
        )

        _friday_ready.wait()

        if _friday_error:

            raise RuntimeError(
                f"F.R.I.D.A.Y. voice failed to load: "
                f"{_friday_error}"
            )

        return _friday_voice

    raise ValueError(
        f"Unknown assistant: {assistant_name}"
    )


# =========================================================
# GET VOICE
# =========================================================

def get_voice(assistant_name: str):

    return _wait_for_voice(
        assistant_name
    )


# =========================================================
# CHECK STATUS
# =========================================================

def voices_ready() -> bool:

    return (
        _alfred_ready.is_set()
        and _friday_ready.is_set()
        and _alfred_voice is not None
        and _friday_voice is not None
    )


# =========================================================
# STOP SPEAKING
# =========================================================

def stop_speaking():

    global _playing

    _stop_event.set()

    try:

        sd.stop()

    except Exception:
        pass

    _playing = False


# =========================================================
# KEYBOARD MONITOR
# =========================================================

def _watch_for_stop():

    global _playing

    while _playing:

        try:

            if msvcrt.kbhit():

                key = msvcrt.getwch()

                # ENTER = stop current speech

                if key in ("\r", "\n"):

                    print(
                        "\nSpeech stopped.",
                        flush=True,
                    )

                    stop_speaking()

                    return

        except Exception:

            return


# =========================================================
# SPEAK
# =========================================================

def speak(
    text: str,
    assistant_name: str,
):
    """
    Speak text using the already-loaded Piper voice.

    Audio is streamed directly to the speakers.
    """

    global _playing

    clean_text = clean_for_speech(
        text
    )

    if not clean_text:
        return

    try:

        # -----------------------------------------------------
        # Get already-loaded voice
        #
        # If it is still loading, this waits only for the
        # required voice.
        # -----------------------------------------------------

        voice = get_voice(
            assistant_name
        )

        # -----------------------------------------------------
        # Reset stop state
        # -----------------------------------------------------

        _stop_event.clear()

        _playing = True

        # -----------------------------------------------------
        # Start ENTER watcher
        # -----------------------------------------------------

        keyboard_thread = threading.Thread(
            target=_watch_for_stop,
            name="TTS-Stop-Listener",
            daemon=True,
        )

        keyboard_thread.start()

        # -----------------------------------------------------
        # Generate Piper audio
        # -----------------------------------------------------

        audio_chunks = voice.synthesize(
            clean_text
        )

        # -----------------------------------------------------
        # Open audio output
        # -----------------------------------------------------

        stream = sd.RawOutputStream(
            samplerate=voice.config.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=0,
        )

        stream.start()

        try:

            # -------------------------------------------------
            # Stream audio immediately
            # -------------------------------------------------

            for chunk in audio_chunks:

                if _stop_event.is_set():

                    break

                stream.write(
                    chunk.audio_int16_bytes
                )

        finally:

            try:
                stream.stop()
            except Exception:
                pass

            try:
                stream.close()
            except Exception:
                pass

    except Exception as error:

        print()
        print(
            "TTS error:"
        )
        print(
            repr(error)
        )
        print()

    finally:

        _playing = False

        _stop_event.clear()
        