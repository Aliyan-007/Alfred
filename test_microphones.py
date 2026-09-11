import sounddevice as sd
import numpy as np

DEVICE_INDEX = 1
SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

print("Starting microphone test...")
print("Speak into your microphone.")
print("Press CTRL+C to stop.\n")

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

            pcm = np.frombuffer(audio, dtype=np.int16)

            volume = np.sqrt(
                np.mean(pcm.astype(np.float32) ** 2)
            )

            # Convert to a simple percentage
            level = min(100, int(volume / 327.68))

            bars = int(level / 100 * 40)

            print(
                f"\rMic level: "
                f"[{'#' * bars}{'-' * (40 - bars)}] "
                f"{level:3d}%",
                end="",
                flush=True
            )

except KeyboardInterrupt:
    print("\n\nMicrophone test stopped.")