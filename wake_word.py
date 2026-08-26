import time
import numpy as np
import sounddevice as sd

from openwakeword.model import Model


# =========================================================
# CONFIGURATION
# =========================================================

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

MODEL_NAME = "alexa_v0.1"

THRESHOLD = 0.50

WAKE_COOLDOWN = 1.5


# =========================================================
# FIND WORKING MICROPHONE
# =========================================================

def find_microphone():

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

    # Prefer Bluetooth/headset microphones if available
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

    # Otherwise use the default input device
    default_input = sd.default.device[0]

    if (
        default_input is not None
        and default_input >= 0
    ):

        print(
            f"Using default microphone [{default_input}]: "
            f"{devices[default_input]['name']}"
        )

        return default_input

    # Final fallback: first available input device
    index, name, channels = candidates[0]

    print(
        f"Using available microphone [{index}]: {name}"
    )

    return index


# =========================================================
# WAKE WORD LISTENER
# =========================================================

def wait_for_wake_word(
    model,
):
    """
    Block until the local openWakeWord model detects Alexa.
    """

    microphone = find_microphone()

    print()
    print("Waiting for wake word: Alexa...")
    print(
        f"Microphone device: {microphone}"
    )

    with sd.RawInputStream(
        device=microphone,
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

            pcm = np.frombuffer(
                audio,
                dtype=np.int16,
            )

            prediction = model.predict(
                pcm
            )

            score = float(
                prediction.get(
                    MODEL_NAME,
                    0.0,
                )
            )

            # Debug: show meaningful detection scores
            if score > 0.01:

                print(
                    f"Alexa score: {score:.6f}"
                )

            if score >= THRESHOLD:

                print()
                print("=" * 55)
                print(
                    "              WAKE WORD DETECTED"
                )
                print("=" * 55)

                print(
                    f"Detection score: {score:.6f}"
                )

                print()

                time.sleep(
                    WAKE_COOLDOWN
                )

                return True