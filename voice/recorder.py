import time

import numpy as np
import sounddevice as sd
import soundfile as sf


SAMPLE_RATE = 16000
CHANNELS = 1

ENERGY_THRESHOLD = 0.015
SILENCE_DURATION = 0.75
MAX_RECORDING_SECONDS = 30
START_TIMEOUT = 8


# =========================================================
# MICROPHONE DETECTION
# =========================================================

def find_microphone():

    devices = sd.query_devices()

    candidates = []

    for index, device in enumerate(devices):

        if device["max_input_channels"] > 0:

            candidates.append(
                (
                    index,
                    device["name"],
                )
            )

    if not candidates:

        raise RuntimeError(
            "No microphone device found."
        )

    # Prefer headset / hands-free microphones.
    preferred_words = [
        "hands-free",
        "headset",
        "microphone",
        "mic",
    ]

    for word in preferred_words:

        for index, name in candidates:

            if word in name.lower():

                print(
                    f"Using microphone [{index}]: {name}",
                    flush=True,
                )

                return index

    # Try Windows default input.
    default_input = sd.default.device[0]

    if (
        default_input is not None
        and default_input >= 0
        and default_input < len(devices)
    ):

        print(
            f"Using default microphone "
            f"[{default_input}]: "
            f"{devices[default_input]['name']}",
            flush=True,
        )

        return default_input

    # Final fallback.
    index, name = candidates[0]

    print(
        f"Using available microphone "
        f"[{index}]: {name}",
        flush=True,
    )

    return index


# =========================================================
# AUDIO LEVEL
# =========================================================

def get_rms(audio):

    return float(
        np.sqrt(
            np.mean(
                np.square(audio)
            )
        )
    )


# =========================================================
# RECORD AUDIO
# =========================================================

def record_audio(
    output_file="voice_input.wav",
):

    microphone = find_microphone()

    print()
    print(
        "Listening...",
        flush=True,
    )

    chunk_duration = 0.05

    chunk_size = int(
        SAMPLE_RATE * chunk_duration
    )

    recorded_chunks = []

    speech_started = False
    silence_time = 0.0
    waiting_time = 0.0
    total_time = 0.0

    with sd.InputStream(
        device=microphone,
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=chunk_size,
    ) as stream:

        while True:

            audio_chunk, overflowed = stream.read(
                chunk_size
            )

            if overflowed:

                print(
                    "Warning: microphone buffer overflow.",
                    flush=True,
                )

            audio_chunk = audio_chunk.copy()

            volume = get_rms(
                audio_chunk
            )

            total_time += chunk_duration

            # Debug volume display
            if volume > 0.003:

                print(
                    f"Mic level: {volume:.4f}",
                    flush=True,
                )

            # --------------------------------------------
            # WAIT FOR USER TO START SPEAKING
            # --------------------------------------------

            if not speech_started:

                waiting_time += chunk_duration

                if volume >= ENERGY_THRESHOLD:

                    print(
                        "Speech detected.",
                        flush=True,
                    )

                    speech_started = True

                    recorded_chunks.append(
                        audio_chunk
                    )

                    silence_time = 0.0

                elif waiting_time >= START_TIMEOUT:

                    print(
                        "No speech detected.",
                        flush=True,
                    )

                    return None

                continue

            # --------------------------------------------
            # RECORD SPEECH
            # --------------------------------------------

            recorded_chunks.append(
                audio_chunk
            )

            if volume < ENERGY_THRESHOLD:

                silence_time += chunk_duration

            else:

                silence_time = 0.0

            # --------------------------------------------
            # USER STOPPED SPEAKING
            # --------------------------------------------

            if silence_time >= SILENCE_DURATION:

                break

            # --------------------------------------------
            # MAXIMUM RECORDING LIMIT
            # --------------------------------------------

            if total_time >= MAX_RECORDING_SECONDS:

                print(
                    "Maximum recording time reached.",
                    flush=True,
                )

                break

    if not recorded_chunks:

        print(
            "No audio recorded.",
            flush=True,
        )

        return None

    audio = np.concatenate(
        recorded_chunks,
        axis=0,
    )

    sf.write(
        output_file,
        audio,
        SAMPLE_RATE,
    )

    print(
        "Recording complete.",
        flush=True,
    )

    return output_file