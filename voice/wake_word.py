import time

import numpy as np
import sounddevice as sd


SAMPLE_RATE = 16000
CHUNK_SIZE = 1280
MODEL_NAME = "alfred"
THRESHOLD = 0.70
REQUIRED_DETECTIONS = 3
MIN_AUDIO_LEVEL = 0.025
WAKE_COOLDOWN = 1.0
LOW_CONFIDENCE_THRESHOLD = 0.20

_IS_SPEAKING = False


def set_speaking(value: bool):
    global _IS_SPEAKING
    _IS_SPEAKING = bool(value)


def is_speaking():
    return _IS_SPEAKING


def _input_device_candidates(excluded=None):
    devices = sd.query_devices()
    excluded = set(excluded or ())
    candidates = []

    for index, device in enumerate(devices):
        if index in excluded or device.get("max_input_channels", 0) <= 0:
            continue
        name = str(device.get("name", f"Input {index}"))
        print(f"[MIC] Found input device: [{index}] {name}")
        candidates.append((index, name))

    if not candidates:
        raise RuntimeError("No input-capable microphone device was found.")

    default_input = sd.default.device[0]
    if isinstance(default_input, int) and any(index == default_input for index, _ in candidates):
        candidates.sort(key=lambda candidate: candidate[0] != default_input)

    return candidates


def find_microphone(excluded=None):
    """Return the first input device that opens and returns an audio block."""
    print("\n[MIC] Searching for an available microphone...")
    failures = []

    for index, name in _input_device_candidates(excluded):
        print(f"[MIC] Testing microphone [{index}]...")
        try:
            with sd.RawInputStream(
                device=index,
                samplerate=SAMPLE_RATE,
                blocksize=CHUNK_SIZE,
                dtype="int16",
                channels=1,
            ) as stream:
                stream.read(CHUNK_SIZE)
        except Exception as error:
            failures.append(f"[{index}] {name}: {error}")
            print(f"[MIC] Microphone [{index}] unavailable, trying next device...")
            continue

        print(f"[MIC] Using microphone [{index}]: {name}")
        return index

    details = "; ".join(failures)
    raise RuntimeError(f"No input microphone could be opened. {details}")


def _get_audio_level(pcm):
    if pcm.size == 0:
        return 0.0
    samples = pcm.astype(np.float32) / 32768.0
    return float(np.sqrt(np.mean(samples * samples)))


def wait_for_wake_word(model):
    """Block until the wake word is detected, recovering failed microphones."""
    excluded = set()

    while True:
        microphone = find_microphone(excluded)
        print("\nWaiting for wake word...")
        print(f"Microphone device: {microphone}")
        print(f"Wake threshold: {THRESHOLD:.2f}")
        print(f"Required confirmations: {REQUIRED_DETECTIONS}")
        print(f"Minimum audio level: {MIN_AUDIO_LEVEL:.4f}")
        consecutive_detections = 0

        try:
            with sd.RawInputStream(
                device=microphone,
                samplerate=SAMPLE_RATE,
                blocksize=CHUNK_SIZE,
                dtype="int16",
                channels=1,
            ) as stream:
                while True:
                    if is_speaking():
                        consecutive_detections = 0
                        time.sleep(0.05)
                        continue

                    audio, overflowed = stream.read(CHUNK_SIZE)
                    if overflowed:
                        consecutive_detections = 0
                        continue

                    pcm = np.frombuffer(audio, dtype=np.int16)
                    audio_level = _get_audio_level(pcm)
                    if audio_level < MIN_AUDIO_LEVEL:
                        consecutive_detections = 0
                        continue

                    try:
                        prediction = model.predict(pcm)
                        score = float(prediction.get(MODEL_NAME, 0.0))
                    except Exception as error:
                        print(f"[WAKE WORD] Prediction error: {error}")
                        consecutive_detections = 0
                        continue

                    if score < LOW_CONFIDENCE_THRESHOLD:
                        consecutive_detections = 0
                        continue

                    if score >= 0.10:
                        print(f"[WAKE] {MODEL_NAME}: {score:.6f} | Audio: {audio_level:.4f}")

                    if score >= THRESHOLD:
                        consecutive_detections += 1
                        print(f"[WAKE] Strong detection {consecutive_detections}/{REQUIRED_DETECTIONS} ({score:.6f})")
                        if consecutive_detections >= REQUIRED_DETECTIONS:
                            print("\n" + "=" * 55)
                            print("              WAKE WORD DETECTED")
                            print("=" * 55)
                            print(f"Model: {MODEL_NAME}")
                            print(f"Detection score: {score:.6f}")
                            print(f"Audio level: {audio_level:.4f}\n")
                            time.sleep(WAKE_COOLDOWN)
                            return True
                    else:
                        consecutive_detections = 0
        except (OSError, RuntimeError, sd.PortAudioError) as error:
            print(f"[MIC] Microphone [{microphone}] failed during recording: {error}")
            excluded.add(microphone)
