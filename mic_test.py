
import numpy as np
import sounddevice as sd


SAMPLE_RATE = 16000
CHUNK_SIZE = 1280


print()
print("=" * 55)
print("              ALFRED MICROPHONE TEST")
print("=" * 55)
print()

print("Opening microphone...")
print("Speak normally for a few seconds.")
print("Press Ctrl+C to stop.")
print()


with sd.RawInputStream(
    samplerate=SAMPLE_RATE,
    blocksize=CHUNK_SIZE,
    dtype="int16",
    channels=1,
) as stream:

    print("Microphone is listening...")
    print()

    while True:

        audio, overflowed = stream.read(
            CHUNK_SIZE
        )

        if overflowed:
            continue

        samples = np.frombuffer(
            audio,
            dtype=np.int16,
        )

        volume = np.max(
            np.abs(samples)
        )

        average = np.mean(
            np.abs(samples)
        )

        print(
            f"Volume: {volume:6.0f} | "
            f"Average: {average:6.1f}"
        )
