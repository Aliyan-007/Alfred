import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000
RECORD_SECONDS = 12

print("========================================")
print("       ALFRED MICROPHONE TEST")
print("========================================")
print()

print("Available audio devices:")
print(sd.query_devices())
print()

input("Press ENTER, then speak for 5 seconds...")

print("Listening...")

audio = sd.rec(
    int(RECORD_SECONDS * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
)

sd.wait()

sf.write(
    "test_recording.wav",
    audio,
    SAMPLE_RATE,
)

print()
print("Recording complete.")
print("Saved: test_recording.wav")