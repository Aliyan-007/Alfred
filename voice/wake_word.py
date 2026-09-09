import time
import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280       # 80ms chunk
THRESHOLD = 0.70        # Confidence threshold
MIN_ENERGY_THRESHOLD = 0.004  # Must have actual acoustic sound (eliminates silence triggers)
WAKE_COOLDOWN = 1.0

IS_SPEAKING = threading.Event()
SELECTED_MIC_INDEX = None


def set_speaking(state: bool):
    if state:
        IS_SPEAKING.set()
    else:
        IS_SPEAKING.clear()


def find_microphone():
    global SELECTED_MIC_INDEX
    if SELECTED_MIC_INDEX is not None:
        return SELECTED_MIC_INDEX

    devices = sd.query_devices()
    hostapis = sd.query_hostapis()

    candidates = []
    for index, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            hostapi_name = hostapis[device["hostapi"]]["name"]
            if "wdm-ks" in hostapi_name.lower():
                continue
            candidates.append((index, device["name"], hostapi_name))

    if not candidates:
        SELECTED_MIC_INDEX = None
        return None

    preferred_words = ["hands-free", "headset", "microphone", "mic", "array"]
    for word in preferred_words:
        for index, name, hapi in candidates:
            if word in name.lower():
                print(f"[AUDIO] Selected microphone [{index}]: {name} ({hapi})", flush=True)
                SELECTED_MIC_INDEX = index
                return SELECTED_MIC_INDEX

    default_input = sd.default.device[0]
    if default_input is not None and 0 <= default_input < len(devices):
        SELECTED_MIC_INDEX = default_input
        return SELECTED_MIC_INDEX

    SELECTED_MIC_INDEX = candidates[0][0]
    return SELECTED_MIC_INDEX


def get_audio_rms(pcm_data: np.ndarray) -> float:
    if len(pcm_data) == 0:
        return 0.0
    return float(np.sqrt(np.mean(pcm_data.astype(np.float32) ** 2))) / 32768.0


def wait_for_wake_word(model):
    while IS_SPEAKING.is_set():
        time.sleep(0.1)

    microphone = find_microphone()
    loaded_models = list(model.models.keys())
    model_name = loaded_models[0] if loaded_models else "alfred"

    print(f"\n[AUDIO] Calibrating microphone for [{model_name}]...", flush=True)
    model.reset()

    consecutive_detections = 0

    with sd.InputStream(
        device=microphone,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK_SIZE,
    ) as stream:

        # Warmup buffer: Feed 20 frames to purge initialization state
        for _ in range(20):
            audio_data, _ = stream.read(CHUNK_SIZE)
            pcm = audio_data.flatten()
            model.predict(pcm)

        print(f"Waiting for wake word: [{model_name}]...\n", flush=True)

        while True:
            if IS_SPEAKING.is_set():
                stream.read(CHUNK_SIZE)
                continue

            audio_data, overflowed = stream.read(CHUNK_SIZE)
            if overflowed:
                continue

            pcm = audio_data.flatten()

            # 1. Neutralize DC offset artifact
            pcm = (pcm - np.mean(pcm)).astype(np.int16)

            # 2. Acoustic Energy Gate: Block silent frame artifacts
            energy = get_audio_rms(pcm)
            if energy < MIN_ENERGY_THRESHOLD:
                # Silence in room -> feed to model to keep window rolling, but never trigger
                model.predict(pcm)
                consecutive_detections = 0
                continue

            # 3. Model Inference
            prediction = model.predict(pcm)

            for key, score in prediction.items():
                score_val = float(score)

                if score_val >= THRESHOLD:
                    consecutive_detections += 1
                    # Require 2 frames of confidence or 1 very strong frame (>0.85)
                    if consecutive_detections >= 2 or score_val >= 0.85:
                        print()
                        print("=" * 55)
                        print(f"WAKE WORD DETECTED ({key}: {score_val:.4f})")
                        print("=" * 55)
                        model.reset()
                        time.sleep(WAKE_COOLDOWN)
                        return True
                else:
                    consecutive_detections = 0