import time

import numpy as np
import sounddevice as sd
from openwakeword.model import Model


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

MODEL_PATH = r"D:\alfred\alfred.onnx"

DEVICE_INDEX = 1
SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

THRESHOLD = 0.40
COOLDOWN = 2.0


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

print("Loading Alfred model...")

model = Model(
    wakeword_models=[MODEL_PATH],
    inference_framework="onnx",
)

print("Model loaded.")
print()


# --------------------------------------------------
# SHOW MICROPHONE
# --------------------------------------------------

print("Starting microphone...")
print(f"Device index : {DEVICE_INDEX}")
print(f"Sample rate  : {SAMPLE_RATE}")
print(f"Chunk size   : {CHUNK_SIZE}")
print()
print("Listening...")
print("Speak into the microphone.")
print("Press CTRL+C to stop.")
print()


last_detection = 0.0


# --------------------------------------------------
# MICROPHONE LOOP
# --------------------------------------------------

try:

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=CHUNK_SIZE,
        device=DEVICE_INDEX,
        dtype="int16",
        channels=1,
    ) as stream:

        while True:

            audio, overflowed = stream.read(CHUNK_SIZE)

            if overflowed:
                print("\nWARNING: audio overflow")

            # Convert microphone data
            pcm = np.frombuffer(
                audio,
                dtype=np.int16
            )

            if len(pcm) == 0:
                continue


            # --------------------------------------
            # MICROPHONE VOLUME
            # --------------------------------------

            volume = np.sqrt(
                np.mean(
                    pcm.astype(np.float32) ** 2
                )
            )

            # Convert volume into a simple 0-100-ish value
            volume_display = min(
                100,
                int(volume / 327.68)
            )


            # --------------------------------------
            # ALFRED PREDICTION
            # --------------------------------------

            try:

                result = model.predict(pcm)

                score = float(
                    result.get("alfred", 0.0)
                )

            except Exception as e:

                print(
                    f"\nPrediction error: {e}",
                    flush=True
                )

                continue


            # --------------------------------------
            # DISPLAY LIVE STATUS
            # --------------------------------------

            bar_length = 30

            volume_bars = int(
                volume_display / 100 * bar_length
            )

            score_bars = int(
                min(score, 1.0) * bar_length
            )

            volume_bar = (
                "#" * volume_bars
                + "-" * (bar_length - volume_bars)
            )

            score_bar = (
                "#" * score_bars
                + "-" * (bar_length - score_bars)
            )


            print(
                f"\rMic [{volume_bar}] "
                f"{volume_display:3d}%   "
                f"Alfred [{score_bar}] "
                f"{score:.3f}",
                end="",
                flush=True
            )


            # --------------------------------------
            # WAKE WORD DETECTION
            # --------------------------------------

            if score >= THRESHOLD:

                now = time.monotonic()

                if now - last_detection >= COOLDOWN:

                    print(
                        f"\n\n"
                        f"================================\n"
                        f"   ALFRED DETECTED!\n"
                        f"   Score: {score:.3f}\n"
                        f"================================\n",
                        flush=True
                    )

                    last_detection = now


except KeyboardInterrupt:

    print("\n\nStopped.")

except Exception as e:

    print("\n\nMICROPHONE ERROR:")
    print(e)