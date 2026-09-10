import os
import sys
import numpy as np
import soundfile as sf
from openwakeword.model import Model


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "alfred.onnx")

# Your uploaded recording.
# Change this if you copy the recording somewhere else.
AUDIO_PATH = os.path.join(
    BASE_DIR,
    "Record (online-voice-recorder.com).mp3"
)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

THRESHOLD = 0.75

# Anything above this is worth investigating.
HIGH_SCORE = 0.50


# ============================================================
# CHECK FILES
# ============================================================

print()
print("=" * 70)
print("                 ALFRED WAKE WORD TEST")
print("=" * 70)
print()

print(f"[MODEL] {MODEL_PATH}")
print(f"[AUDIO] {AUDIO_PATH}")
print()

if not os.path.exists(MODEL_PATH):
    print("[ERROR] alfred.onnx was not found.")
    print()
    print("Expected:")
    print(MODEL_PATH)
    sys.exit(1)

if not os.path.exists(AUDIO_PATH):
    print("[ERROR] Recording was not found.")
    print()
    print("Expected:")
    print(AUDIO_PATH)
    print()
    print(
        "Copy your recording into the same folder as "
        "test_wake_model.py."
    )
    sys.exit(1)


# ============================================================
# LOAD AUDIO
# ============================================================

print("[AUDIO] Loading recording...")

try:
    audio, sample_rate = sf.read(
        AUDIO_PATH,
        dtype="float32",
        always_2d=False,
    )
except Exception as error:
    print()
    print(f"[ERROR] Could not read audio: {error}")
    print()
    print(
        "If this MP3 cannot be read by soundfile on your system, "
        "convert the recording to WAV first."
    )
    sys.exit(1)


# ============================================================
# CONVERT TO MONO
# ============================================================

if audio.ndim == 2:

    print(
        f"[AUDIO] Stereo recording detected: "
        f"{audio.shape[1]} channels"
    )

    audio = np.mean(
        audio,
        axis=1,
    )

else:

    print("[AUDIO] Mono recording detected.")


# ============================================================
# RESAMPLE TO 16 KHZ
# ============================================================

print(
    f"[AUDIO] Original sample rate: "
    f"{sample_rate} Hz"
)

if sample_rate != SAMPLE_RATE:

    print(
        f"[AUDIO] Resampling to {SAMPLE_RATE} Hz..."
    )

    try:
        from scipy.signal import resample_poly

        # Calculate integer resampling ratio.
        import math

        gcd = math.gcd(
            sample_rate,
            SAMPLE_RATE,
        )

        up = SAMPLE_RATE // gcd
        down = sample_rate // gcd

        audio = resample_poly(
            audio,
            up,
            down,
        ).astype(
            np.float32
        )

    except Exception as error:

        print()
        print(
            f"[ERROR] Resampling failed: {error}"
        )
        print()
        print(
            "Install scipy with:"
        )
        print(
            "pip install scipy"
        )

        sys.exit(1)

else:

    print(
        "[AUDIO] Recording is already 16 kHz."
    )


# ============================================================
# CLEAN AUDIO
# ============================================================

audio = np.asarray(
    audio,
    dtype=np.float32,
)

audio = np.nan_to_num(
    audio,
    nan=0.0,
    posinf=0.0,
    neginf=0.0,
)

# Prevent accidental clipping.
audio = np.clip(
    audio,
    -1.0,
    1.0,
)


# ============================================================
# AUDIO INFORMATION
# ============================================================

duration = len(audio) / SAMPLE_RATE

rms = float(
    np.sqrt(
        np.mean(
            np.square(audio)
        )
    )
)

peak = float(
    np.max(
        np.abs(audio)
    )
)

print()
print("-" * 70)
print("AUDIO INFORMATION")
print("-" * 70)

print(
    f"Duration       : {duration:.2f} seconds"
)

print(
    f"Samples        : {len(audio)}"
)

print(
    f"RMS level      : {rms:.6f}"
)

print(
    f"Peak level     : {peak:.6f}"
)

print()


# ============================================================
# LOAD WAKE WORD MODEL
# ============================================================

print("[MODEL] Loading ALFRED wake-word model...")

try:

    model = Model(
        wakeword_models=[
            MODEL_PATH
        ],
        inference_framework="onnx",
    )

except Exception:

    try:

        model = Model(
            wakeword_models=[
                MODEL_PATH
            ]
        )

    except Exception as error:

        print()
        print(
            f"[ERROR] Could not load model: {error}"
        )
        sys.exit(1)


print("[MODEL] Model loaded successfully.")
print()


# ============================================================
# SHOW MODEL OUTPUT NAMES
# ============================================================

print("-" * 70)
print("MODEL OUTPUT")
print("-" * 70)

try:

    test_chunk = np.zeros(
        CHUNK_SIZE,
        dtype=np.int16,
    )

    test_prediction = model.predict(
        test_chunk
    )

    print(
        f"Prediction dictionary: "
        f"{test_prediction}"
    )

    model_names = list(
        test_prediction.keys()
    )

    print(
        f"Detected model names: "
        f"{model_names}"
    )

except Exception as error:

    print(
        f"[WARNING] Could not inspect model output: "
        f"{error}"
    )

    model_names = []


print()


# ============================================================
# RESET MODEL STATE
# ============================================================

try:
    model.reset()
except Exception:
    pass


# ============================================================
# RUN TEST
# ============================================================

print("=" * 70)
print("STARTING RECORDING ANALYSIS")
print("=" * 70)
print()

print(
    "The recording will now be fed into the wake-word model."
)

print(
    f"Detection threshold : {THRESHOLD:.2f}"
)

print(
    f"High-score warning  : {HIGH_SCORE:.2f}"
)

print()


detections = []

high_scores = []

all_scores = []

chunk_number = 0


for start in range(
    0,
    len(audio),
    CHUNK_SIZE,
):

    end = start + CHUNK_SIZE

    chunk = audio[start:end]

    if len(chunk) < CHUNK_SIZE:

        # Pad final chunk.
        padded = np.zeros(
            CHUNK_SIZE,
            dtype=np.float32,
        )

        padded[
            :len(chunk)
        ] = chunk

        chunk = padded


    # --------------------------------------------------------
    # Convert float [-1, 1] to int16 PCM.
    # This matches the microphone input used by your
    # wake-word listener.
    # --------------------------------------------------------

    pcm = (
        chunk * 32767.0
    ).astype(
        np.int16
    )


    # --------------------------------------------------------
    # Calculate audio level.
    # --------------------------------------------------------

    audio_rms = float(
        np.sqrt(
            np.mean(
                np.square(
                    chunk
                )
            )
        )
    )

    audio_peak = float(
        np.max(
            np.abs(
                chunk
            )
        )
    )


    # --------------------------------------------------------
    # Run wake-word model.
    # --------------------------------------------------------

    try:

        prediction = model.predict(
            pcm
        )

    except Exception as error:

        print(
            f"[ERROR] Model prediction failed "
            f"at chunk {chunk_number}: {error}"
        )

        chunk_number += 1
        continue


    # --------------------------------------------------------
    # Find ALFRED score.
    # --------------------------------------------------------

    score = 0.0
    model_name = "alfred"

    if "alfred" in prediction:

        try:

            score = float(
                prediction["alfred"]
            )

        except (
            TypeError,
            ValueError,
        ):

            score = 0.0

    else:

        # Fallback: strongest model output.
        for name, value in prediction.items():

            try:

                value = float(value)

            except (
                TypeError,
                ValueError,
            ):

                continue

            if value > score:

                score = value
                model_name = name


    timestamp = (
        chunk_number
        * CHUNK_SIZE
        / SAMPLE_RATE
    )

    all_scores.append(
        (
            timestamp,
            score,
            audio_rms,
            audio_peak,
        )
    )


    # --------------------------------------------------------
    # Print interesting results.
    # --------------------------------------------------------

    if score >= HIGH_SCORE:

        print(
            f"[HIGH SCORE] "
            f"{timestamp:7.2f}s | "
            f"{model_name}: {score:.6f} | "
            f"RMS: {audio_rms:.6f} | "
            f"Peak: {audio_peak:.6f}"
        )

        high_scores.append(
            (
                timestamp,
                score,
                audio_rms,
                audio_peak,
            )
        )


    # --------------------------------------------------------
    # Detection threshold.
    # --------------------------------------------------------

    if score >= THRESHOLD:

        print(
            f""
        )

        print(
            f""
        )

        print(
            f"[!!! DETECTION !!!] "
            f"{timestamp:.2f}s"
        )

        print(
            f"    Model : {model_name}"
        )

        print(
            f"    Score : {score:.6f}"
        )

        print(
            f"    RMS   : {audio_rms:.6f}"
        )

        print(
            f"    Peak  : {audio_peak:.6f}"
        )

        print()

        detections.append(
            (
                timestamp,
                score,
                audio_rms,
                audio_peak,
            )
        )


    chunk_number += 1


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 70)
print("                         RESULTS")
print("=" * 70)
print()


print(
    f"Recording duration : {duration:.2f} seconds"
)

print(
    f"Chunks analyzed    : {chunk_number}"
)

print(
    f"Threshold          : {THRESHOLD:.2f}"
)

print(
    f"High scores        : {len(high_scores)}"
)

print(
    f"Detections         : {len(detections)}"
)

print()


# ============================================================
# SHOW DETECTIONS
# ============================================================

if detections:

    print("-" * 70)
    print("DETECTION TIMESTAMPS")
    print("-" * 70)

    for (
        timestamp,
        score,
        audio_rms,
        audio_peak,
    ) in detections:

        print(
            f"{timestamp:8.2f}s | "
            f"score={score:.6f} | "
            f"RMS={audio_rms:.6f} | "
            f"peak={audio_peak:.6f}"
        )

else:

    print(
        "No wake-word detections above threshold."
    )

print()


# ============================================================
# FIND MAXIMUM SCORE
# ============================================================

if all_scores:

    max_result = max(
        all_scores,
        key=lambda item: item[1],
    )

    (
        max_timestamp,
        max_score,
        max_rms,
        max_peak,
    ) = max_result

    print("-" * 70)
    print("MAXIMUM MODEL SCORE")
    print("-" * 70)

    print(
        f"Timestamp : {max_timestamp:.2f}s"
    )

    print(
        f"Score     : {max_score:.6f}"
    )

    print(
        f"RMS       : {max_rms:.6f}"
    )

    print(
        f"Peak      : {max_peak:.6f}"
    )

    print()


# ============================================================
# DIAGNOSIS
# ============================================================

print("=" * 70)
print("                         DIAGNOSIS")
print("=" * 70)
print()


if len(detections) == 0:

    print(
        "GOOD: The recording did not trigger ALFRED "
        f"at the {THRESHOLD:.2f} threshold."
    )

    print()

    if high_scores:

        print(
            "However, the model produced some moderately "
            "high scores."
        )

        print(
            "This means the microphone/audio may still "
            "be challenging for the model."
        )

    else:

        print(
            "The model appears quiet on this recording."
        )


else:

    print(
        "WARNING: The model detected ALFRED "
        "inside this recording."
    )

    print()

    print(
        f"It produced {len(detections)} "
        "detection(s) above the threshold."
    )

    print()

    print(
        "This is important:"
    )

    print(
        "If you were SILENT at these timestamps, "
        "your custom wake-word model is producing "
        "false positives."
    )

    print()

    print(
        "Changing REQUIRED_DETECTIONS alone will "
        "not solve the underlying problem."
    )

    print(
        "The next step should be testing the model's "
        "training/calibration or microphone input."
    )


# ============================================================
# FINAL INTERPRETATION
# ============================================================

print()
print("=" * 70)
print("                       NEXT STEP")
print("=" * 70)
print()

if detections:

    print(
        "Please send me the RESULTS section from this test."
    )

    print(
        "Especially send:"
    )

    print(
        "  1. Maximum model score"
    )

    print(
        "  2. Detection timestamps"
    )

    print(
        "  3. RMS / Peak values"
    )

    print(
        "  4. Number of detections"
    )

    print()

    print(
        "Then we can determine whether the problem is:"
    )

    print(
        "  - the ALFRED ONNX model,"
    )

    print(
        "  - the audio preprocessing,"
    )

    print(
        "  - the microphone,"
    )

    print(
        "  - or speaker/microphone feedback."
    )

else:

    print(
        "The recording did not reproduce the false trigger."
    )

    print(
        "In that case, the next test should be performed "
        "directly from microphone input."
    )

print()
print("=" * 70)
print("                         TEST COMPLETE")
print("=" * 70)
print()