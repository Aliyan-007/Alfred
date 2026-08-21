import time

import numpy as np
import sounddevice as sd
import soundfile as sf


SAMPLE_RATE = 16000
CHANNELS = 1

# Lower this if your microphone is quiet.
ENERGY_THRESHOLD = 0.015

# Shorter = faster response after you stop talking.
SILENCE_DURATION = 0.75

# Maximum length of one recording.
MAX_RECORDING_SECONDS = 30

# Maximum time waiting for you to start talking.
START_TIMEOUT = 8


def get_rms(audio):
    """Calculate the volume level of an audio chunk."""
    return float(np.sqrt(np.mean(np.square(audio))))


def record_audio(output_file="voice_input.wav"):
    """
    Wait for speech, then record until the user stops speaking.
    """

    print()
    print("Listening...", flush=True)

    chunk_duration = 0.05
    chunk_size = int(SAMPLE_RATE * chunk_duration)

    recorded_chunks = []

    speech_started = False
    silence_time = 0.0
    waiting_time = 0.0
    total_time = 0.0

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=chunk_size,
    ) as stream:

        while True:

            audio_chunk, overflowed = stream.read(chunk_size)

            if overflowed:
                print(
                    "Warning: microphone buffer overflow.",
                    flush=True,
                )

            audio_chunk = audio_chunk.copy()

            volume = get_rms(audio_chunk)

            total_time += chunk_duration

            # --------------------------------------------
            # WAIT FOR USER TO START SPEAKING
            # --------------------------------------------

            if not speech_started:

                waiting_time += chunk_duration

                if volume >= ENERGY_THRESHOLD:

                    speech_started = True
                    recorded_chunks.append(audio_chunk)
                    silence_time = 0.0

                elif waiting_time >= START_TIMEOUT:

                    print(
                        "No speech detected.",
                        flush=True,
                    )

                    return None

                continue

            # --------------------------------------------
            # USER IS SPEAKING
            # --------------------------------------------

            recorded_chunks.append(audio_chunk)

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
            # SAFETY LIMIT
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

    # Combine chunks.
    audio = np.concatenate(
        recorded_chunks,
        axis=0,
    )

    # Save WAV.
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