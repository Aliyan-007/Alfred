from collections import deque
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from voice.wake_word import find_microphone

SAMPLE_RATE = 16000
CHANNELS = 1

SILENCE_DURATION = 0.8
MIN_SPEECH_DURATION = 0.45
MAX_RECORDING_SECONDS = 30.0
START_TIMEOUT = 4.0
PRE_BUFFER_DURATION = 0.25


def get_rms(audio):
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio))))


def record_audio(output_file="voice_input.wav"):
    time.sleep(0.15)
    microphone = find_microphone()

    print("\nListening for command...", flush=True)

    chunk_duration = 0.05
    chunk_size = int(SAMPLE_RATE * chunk_duration)

    pre_buffer_chunks = int(PRE_BUFFER_DURATION / chunk_duration)
    pre_buffer = deque(maxlen=pre_buffer_chunks)

    recorded_chunks = []
    speech_started = False
    speech_start_time = 0.0
    silence_time = 0.0
    waiting_time = 0.0
    total_time = 0.0
    trigger_hits = 0

    try:
        with sd.InputStream(
            device=microphone,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=chunk_size,
        ) as stream:

            noise_samples = []
            for _ in range(5):
                chk, _ = stream.read(chunk_size)
                noise_samples.append(get_rms(chk))

            ambient_floor = float(np.mean(noise_samples)) if noise_samples else 0.003
            energy_trigger = max(0.006, min(0.030, ambient_floor * 2.0))

            print(
                f"[MIC] Ambient noise: {ambient_floor:.4f} | Dynamic trigger: {energy_trigger:.4f}",
                flush=True,
            )

            while True:
                audio_chunk, _ = stream.read(chunk_size)
                audio_chunk = audio_chunk.copy()
                volume = get_rms(audio_chunk)
                total_time += chunk_duration

                if not speech_started:
                    pre_buffer.append(audio_chunk)
                    waiting_time += chunk_duration

                    if volume >= energy_trigger:
                        trigger_hits += 1
                    else:
                        trigger_hits = max(0, trigger_hits - 1)

                    if trigger_hits >= 2:
                        print(
                            f"\n[RECORDER] Speech detected! (Volume: {volume:.4f})",
                            flush=True,
                        )
                        speech_started = True
                        speech_start_time = time.time()
                        recorded_chunks.extend(list(pre_buffer))
                        pre_buffer.clear()
                        silence_time = 0.0
                        trigger_hits = 0

                    elif waiting_time >= START_TIMEOUT:
                        print("\n[RECORDER] No speech detected (timed out).", flush=True)
                        return None

                    continue

                recorded_chunks.append(audio_chunk)

                if volume < energy_trigger:
                    silence_time += chunk_duration
                else:
                    silence_time = 0.0

                if silence_time >= SILENCE_DURATION:
                    if (time.time() - speech_start_time) < MIN_SPEECH_DURATION:
                        print("\n[RECORDER] Too short to count as a command; resetting.", flush=True)
                        speech_started = False
                        recorded_chunks.clear()
                        silence_time = 0.0
                        trigger_hits = 0
                        continue
                    break

                if total_time >= MAX_RECORDING_SECONDS:
                    print("\n[RECORDER] Max duration reached.", flush=True)
                    break

    except Exception as error:
        print(f"\n[RECORDER ERROR]: {error}", flush=True)
        return None

    if not recorded_chunks:
        return None

    audio = np.concatenate(recorded_chunks, axis=0)
    sf.write(output_file, audio, SAMPLE_RATE)
    print("[RECORDER] Recording complete.", flush=True)
    return output_file