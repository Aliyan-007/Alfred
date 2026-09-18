import time

import numpy as np
import sounddevice as sd
from openwakeword.model import Model
from voice.wake_word import (
    CHUNK_SIZE,
    MIN_AUDIO_LEVEL,
    REQUIRED_DETECTIONS,
    SAMPLE_RATE,
    THRESHOLD,
    _get_audio_level,
    find_microphone,
)


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

MODEL_PATH = r"D:\alfred\alfred.onnx"

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
device_index = find_microphone()
print(f"Device index : {device_index}")
print(f"Sample rate  : {SAMPLE_RATE}")
print(f"Chunk size   : {CHUNK_SIZE}")
print()
print("Listening...")
print("Speak into the microphone.")
print("Press CTRL+C to stop.")
print()


last_detection = 0.0
consecutive_detections = 0


# --------------------------------------------------
# MICROPHONE LOOP
# --------------------------------------------------

try:
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=CHUNK_SIZE,
        device=device_index,
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

            if _get_audio_level(pcm) < MIN_AUDIO_LEVEL:
                consecutive_detections = 0
                continue

            if score >= THRESHOLD:
                consecutive_detections += 1

                now = time.monotonic()

                if consecutive_detections >= REQUIRED_DETECTIONS and now - last_detection >= COOLDOWN:

                    print(
                        f"\n\n"
                        f"================================\n"
                        f"   ALFRED DETECTED!\n"
                        f"   Score: {score:.3f}\n"
                        f"================================\n",
                        flush=True
                    )

                    last_detection = now
                    consecutive_detections = 0
            else:
                consecutive_detections = 0


except KeyboardInterrupt:

    print("\n\nStopped.")

except Exception as e:

    print("\n\nMICROPHONE ERROR:")
    print(e)