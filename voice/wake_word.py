import time

import numpy as np
import sounddevice as sd


# =========================================================
# CONFIGURATION
# =========================================================

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

# Exact prediction key returned by D:\alfred\alfred.onnx
MODEL_NAME = "alfred"

# Wake-word confidence threshold.
THRESHOLD = 0.55

# Number of consecutive strong model predictions required.
REQUIRED_DETECTIONS = 2

# Minimum microphone RMS level required before a wake
# prediction can be accepted.
#
# This prevents very quiet background/noise from activating
# the wake-word model.
MIN_AUDIO_LEVEL = 0.015

# Ignore the detector briefly after successful activation.
WAKE_COOLDOWN = 1.0

# Any score below this is treated as not wake-like.
LOW_CONFIDENCE_THRESHOLD = 0.20


# =========================================================
# GLOBAL SPEAKING STATE
# =========================================================

_IS_SPEAKING = False


def set_speaking(value: bool):
    """
    Enable or disable wake-word detection while ALFRED
    is speaking.
    """
    global _IS_SPEAKING
    _IS_SPEAKING = bool(value)


def is_speaking():
    """
    Return True when ALFRED is currently speaking.
    """
    return _IS_SPEAKING


# =========================================================
# FIND WORKING MICROPHONE
# =========================================================

def find_microphone():
    """
    Find a usable input microphone.

    Preference order:
        1. Headset
        2. Hands-Free
        3. Microphone
        4. Mic
        5. Default input
        6. First available input
    """

    print()
    print("Searching for an available microphone...")

    devices = sd.query_devices()

    candidates = []

    for index, device in enumerate(devices):

        if device["max_input_channels"] > 0:

            candidates.append(
                (
                    index,
                    device["name"],
                    device["max_input_channels"],
                )
            )

    if not candidates:

        raise RuntimeError(
            "No microphone device was found."
        )

    preferred_words = [
        "headset",
        "hands-free",
        "microphone",
        "mic",
    ]

    for word in preferred_words:

        for index, name, channels in candidates:

            if word.lower() in name.lower():

                print(
                    f"Using microphone [{index}]: {name}"
                )

                return index

    # -----------------------------------------------------
    # Default input fallback
    # -----------------------------------------------------

    default_input = sd.default.device[0]

    if (
        default_input is not None
        and default_input >= 0
        and default_input < len(devices)
    ):

        print(
            f"Using default microphone [{default_input}]: "
            f"{devices[default_input]['name']}"
        )

        return default_input

    # -----------------------------------------------------
    # First available microphone fallback
    # -----------------------------------------------------

    index, name, channels = candidates[0]

    print(
        f"Using available microphone [{index}]: {name}"
    )

    return index


# =========================================================
# AUDIO LEVEL
# =========================================================

def _get_audio_level(pcm):
    """
    Calculate RMS microphone level.

    Returns a normalized value approximately between
    0.0 and 1.0 for normal int16 microphone audio.
    """

    if pcm.size == 0:
        return 0.0

    samples = pcm.astype(np.float32) / 32768.0

    return float(
        np.sqrt(
            np.mean(
                samples * samples
            )
        )
    )


# =========================================================
# WAKE WORD LISTENER
# =========================================================

def wait_for_wake_word(model):
    """
    Block until the ALFRED wake word is detected.

    False-positive protection:

        1. Uses the exact 'alfred' model output.
        2. Requires multiple consecutive detections.
        3. Requires sufficient microphone audio energy.
        4. Resets confirmation when audio becomes quiet.
        5. Resets confirmation when model confidence drops.
        6. Ignores detection while ALFRED is speaking.
        7. Applies a short cooldown after activation.
    """

    microphone = find_microphone()

    print()
    print("Waiting for wake word...")
    print(
        f"Microphone device: {microphone}"
    )
    print(
        f"Wake threshold: {THRESHOLD:.2f}"
    )
    print(
        f"Required confirmations: "
        f"{REQUIRED_DETECTIONS}"
    )
    print(
        f"Minimum audio level: "
        f"{MIN_AUDIO_LEVEL:.4f}"
    )

    consecutive_detections = 0

    with sd.RawInputStream(
        device=microphone,
        samplerate=SAMPLE_RATE,
        blocksize=CHUNK_SIZE,
        dtype="int16",
        channels=1,
    ) as stream:

        while True:

            # -------------------------------------------------
            # Ignore microphone while ALFRED is speaking.
            # -------------------------------------------------

            if is_speaking():

                consecutive_detections = 0

                time.sleep(0.05)

                continue

            # -------------------------------------------------
            # Read microphone audio.
            # -------------------------------------------------

            audio, overflowed = stream.read(
                CHUNK_SIZE
            )

            if overflowed:

                consecutive_detections = 0

                continue

            pcm = np.frombuffer(
                audio,
                dtype=np.int16,
            )

            if pcm.size == 0:

                consecutive_detections = 0

                continue

            # -------------------------------------------------
            # AUDIO ENERGY GATE
            #
            # Do not allow an extremely quiet microphone
            # chunk to activate the wake-word model.
            # -------------------------------------------------

            audio_level = _get_audio_level(pcm)

            if audio_level < MIN_AUDIO_LEVEL:

                if consecutive_detections > 0:

                    print(
                        "[WAKE] Audio too quiet; "
                        "confirmation reset."
                    )

                consecutive_detections = 0
                continue

            # -------------------------------------------------
            # RUN CUSTOM ALFRED MODEL
            # -------------------------------------------------

            try:

                prediction = model.predict(pcm)

            except Exception as error:

                print(
                    f"[WAKE WORD] Prediction error: "
                    f"{error}"
                )

                consecutive_detections = 0

                continue

            # -------------------------------------------------
            # READ ONLY THE ALFRED MODEL
            #
            # No fallback to another model.
            # -------------------------------------------------

            try:

                score = float(
                    prediction.get(
                        MODEL_NAME,
                        0.0,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                score = 0.0

            # -------------------------------------------------
            # LOW CONFIDENCE FILTER
            # -------------------------------------------------

            if score < LOW_CONFIDENCE_THRESHOLD:

                if consecutive_detections > 0:

                    print(
                        "[WAKE] Confidence reset."
                    )

                consecutive_detections = 0
                continue

            # -------------------------------------------------
            # DEBUG ONLY FOR MEANINGFUL SCORES
            # -------------------------------------------------

            if score >= 0.10:

                print(
                    f"[WAKE] {MODEL_NAME}: "
                    f"{score:.6f} | "
                    f"Audio: {audio_level:.4f}"
                )

            # -------------------------------------------------
            # CONFIDENCE CONFIRMATION
            # -------------------------------------------------

            if score >= THRESHOLD:

                consecutive_detections += 1

                print(
                    f"[WAKE] Strong detection "
                    f"{consecutive_detections}/"
                    f"{REQUIRED_DETECTIONS} "
                    f"({score:.6f})"
                )

                # -------------------------------------------------
                # Require all consecutive confirmations.
                # -------------------------------------------------

                if (
                    consecutive_detections
                    >= REQUIRED_DETECTIONS
                ):

                    print()
                    print("=" * 55)
                    print(
                        "              WAKE WORD DETECTED"
                    )
                    print("=" * 55)
                    print(
                        f"Model: {MODEL_NAME}"
                    )
                    print(
                        f"Detection score: "
                        f"{score:.6f}"
                    )
                    print(
                        f"Audio level: "
                        f"{audio_level:.4f}"
                    )
                    print()

                    consecutive_detections = 0

                    # -------------------------------------------------
                    # Prevent immediate retriggering from the same
                    # spoken audio.
                    # -------------------------------------------------

                    time.sleep(
                        WAKE_COOLDOWN
                    )

                    return True

            else:

                # -------------------------------------------------
                # Confidence dropped below threshold.
                # Break the confirmation chain.
                # -------------------------------------------------

                if consecutive_detections > 0:

                    print(
                        "[WAKE] Confirmation reset."
                    )

                consecutive_detections = 0