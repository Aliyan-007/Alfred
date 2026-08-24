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

THRESHOLD = 0.70

WAKE_COOLDOWN = 1.5


# =========================================================
# WAKE WORD LISTENER
# =========================================================

def wait_for_wake_word(
    model,
):
    """
    Block until the local openWakeWord model detects Alexa.
    """

    print()
    print(
        "Waiting for wake word: Alexa..."
    )

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

            if score >= THRESHOLD:

                print()
                print(
                    "=" * 55
                )
                print(
                    "              WAKE WORD DETECTED"
                )
                print(
                    "=" * 55
                )
                print(
                    f"Detection score: {score:.6f}"
                )
                print()

                time.sleep(
                    WAKE_COOLDOWN
                )

                return True