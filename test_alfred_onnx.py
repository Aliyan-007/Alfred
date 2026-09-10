
import os
import sys
import numpy as np

from openwakeword.model import Model


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "alfred.onnx")

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

DURATION_SECONDS = 10

# Number of chunks to ignore while the openWakeWord
# feature pipeline warms up.
WARMUP_CHUNKS = 5


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 78)
print("                 ALFRED ONNX MODEL ISOLATION TEST")
print("=" * 78)
print()

print(f"Model: {MODEL_PATH}")
print()


# ============================================================
# CHECK MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):
    print("[ERROR] alfred.onnx was not found.")
    print()
    print("Expected:")
    print(MODEL_PATH)
    sys.exit(1)


# ============================================================
# MODEL CREATION
# ============================================================

def create_model():

    print("[MODEL] Creating fresh ALFRED model instance...")

    try:
        model = Model(
            wakeword_models=[MODEL_PATH],
            inference_framework="onnx",
        )

    except Exception:

        try:
            model = Model(
                wakeword_models=[MODEL_PATH]
            )

        except Exception as error:
            print()
            print(f"[ERROR] Could not load model: {error}")
            sys.exit(1)

    print("[MODEL] Loaded.")
    print()

    return model


# ============================================================
# AUDIO GENERATORS
# ============================================================

def generate_silence():

    samples = SAMPLE_RATE * DURATION_SECONDS

    return np.zeros(
        samples,
        dtype=np.float32,
    )


def generate_low_noise():

    samples = SAMPLE_RATE * DURATION_SECONDS

    rng = np.random.default_rng(12345)

    return (
        rng.normal(
            0.0,
            0.0001,
            samples,
        )
    ).astype(np.float32)


def generate_medium_noise():

    samples = SAMPLE_RATE * DURATION_SECONDS

    rng = np.random.default_rng(12345)

    return (
        rng.normal(
            0.0,
            0.005,
            samples,
        )
    ).astype(np.float32)


def generate_loud_noise():

    samples = SAMPLE_RATE * DURATION_SECONDS

    rng = np.random.default_rng(12345)

    return (
        rng.normal(
            0.0,
            0.05,
            samples,
        )
    ).astype(np.float32)


def generate_impulses():

    samples = SAMPLE_RATE * DURATION_SECONDS

    audio = np.zeros(
        samples,
        dtype=np.float32,
    )

    # Harmless synthetic impulses at fixed positions.
    positions = [
        int(1.0 * SAMPLE_RATE),
        int(3.0 * SAMPLE_RATE),
        int(5.0 * SAMPLE_RATE),
        int(7.0 * SAMPLE_RATE),
        int(9.0 * SAMPLE_RATE),
    ]

    for position in positions:

        length = min(
            160,
            samples - position,
        )

        if length > 0:

            audio[
                position:
                position + length
            ] = np.linspace(
                0.2,
                0.0,
                length,
                dtype=np.float32,
            )

    return audio


# ============================================================
# MODEL TEST
# ============================================================

def test_model(
    test_name,
    audio,
):

    print()
    print("=" * 78)
    print(f"TEST: {test_name}")
    print("=" * 78)
    print()

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

    print(f"Audio RMS : {rms:.10f}")
    print(f"Audio peak: {peak:.10f}")
    print()

    # IMPORTANT:
    # Every test gets a completely fresh model instance.
    #
    # This prevents state from a previous test from
    # influencing the next test.

    model = create_model()

    scores = []

    chunk_number = 0

    for start in range(
        0,
        len(audio),
        CHUNK_SIZE,
    ):

        end = start + CHUNK_SIZE

        chunk = audio[start:end]

        if len(chunk) < CHUNK_SIZE:

            padded = np.zeros(
                CHUNK_SIZE,
                dtype=np.float32,
            )

            padded[
                :len(chunk)
            ] = chunk

            chunk = padded

        # Convert [-1, +1] float audio to int16 PCM.
        pcm = (
            chunk * 32767.0
        ).astype(np.int16)

        try:

            prediction = model.predict(
                pcm
            )

        except Exception as error:

            print()
            print(
                f"[ERROR] Prediction failed "
                f"at chunk {chunk_number}: {error}"
            )

            return None

        if "alfred" in prediction:

            try:
                score = float(
                    prediction["alfred"]
                )

            except Exception:
                score = 0.0

        else:

            score = 0.0

            for name, value in prediction.items():

                try:
                    value = float(value)
                except Exception:
                    continue

                score = max(
                    score,
                    value,
                )

        # Ignore initial feature-pipeline warmup.
        if chunk_number >= WARMUP_CHUNKS:
            scores.append(score)

        chunk_number += 1

    if not scores:

        print("[ERROR] No usable scores.")
        return None

    scores = np.asarray(
        scores,
        dtype=np.float64,
    )

    max_index = int(
        np.argmax(scores)
    )

    max_score = float(
        np.max(scores)
    )

    min_score = float(
        np.min(scores)
    )

    mean_score = float(
        np.mean(scores)
    )

    median_score = float(
        np.median(scores)
    )

    p95 = float(
        np.percentile(
            scores,
            95,
        )
    )

    p99 = float(
        np.percentile(
            scores,
            99,
        )
    )

    above_50 = int(
        np.sum(
            scores >= 0.50
        )
    )

    above_75 = int(
        np.sum(
            scores >= 0.75
        )
    )

    above_90 = int(
        np.sum(
            scores >= 0.90
        )
    )

    total = len(scores)

    max_time = (
        (max_index + WARMUP_CHUNKS)
        * CHUNK_SIZE
        / SAMPLE_RATE
    )

    print("-" * 78)
    print("MODEL OUTPUT")
    print("-" * 78)

    print(
        f"Chunks tested       : {total}"
    )

    print(
        f"Minimum score      : {min_score:.9f}"
    )

    print(
        f"Maximum score      : {max_score:.9f}"
    )

    print(
        f"Mean score         : {mean_score:.9f}"
    )

    print(
        f"Median score       : {median_score:.9f}"
    )

    print(
        f"95th percentile    : {p95:.9f}"
    )

    print(
        f"99th percentile    : {p99:.9f}"
    )

    print(
        f"Maximum score time : {max_time:.2f}s"
    )

    print()

    print(
        f">= 0.50            : "
        f"{above_50}/{total} "
        f"({above_50 / total * 100:.2f}%)"
    )

    print(
        f">= 0.75            : "
        f"{above_75}/{total} "
        f"({above_75 / total * 100:.2f}%)"
    )

    print(
        f">= 0.90            : "
        f"{above_90}/{total} "
        f"({above_90 / total * 100:.2f}%)"
    )

    print()

    # Show the strongest individual outputs.
    top_count = min(
        10,
        len(scores),
    )

    top_indices = np.argsort(
        scores
    )[-top_count:][::-1]

    print("-" * 78)
    print("TOP MODEL SCORES")
    print("-" * 78)

    for index in top_indices:

        actual_chunk = (
            int(index)
            + WARMUP_CHUNKS
        )

        timestamp = (
            actual_chunk
            * CHUNK_SIZE
            / SAMPLE_RATE
        )

        print(
            f"{timestamp:7.2f}s | "
            f"{scores[index]:.9f}"
        )

    print()

    return {
        "name": test_name,
        "min": min_score,
        "max": max_score,
        "mean": mean_score,
        "median": median_score,
        "p95": p95,
        "p99": p99,
        "above_50": above_50,
        "above_75": above_75,
        "above_90": above_90,
        "total": total,
    }


# ============================================================
# RUN TESTS
# ============================================================

results = []

results.append(
    test_model(
        "PURE DIGITAL SILENCE",
        generate_silence(),
    )
)

results.append(
    test_model(
        "VERY LOW LEVEL NOISE",
        generate_low_noise(),
    )
)

results.append(
    test_model(
        "MEDIUM NOISE",
        generate_medium_noise(),
    )
)

results.append(
    test_model(
        "LOUD NOISE",
        generate_loud_noise(),
    )
)

results.append(
    test_model(
        "SYNTHETIC IMPULSES",
        generate_impulses(),
    )
)


# ============================================================
# FINAL COMPARISON
# ============================================================

print()
print("=" * 78)
print("                         FINAL COMPARISON")
print("=" * 78)
print()

print(
    f"{'TEST':<28}"
    f"{'MAX':>12}"
    f"{'MEAN':>12}"
    f"{'P95':>12}"
    f"{'>=0.75':>12}"
)

print("-" * 78)

for result in results:

    if result is None:
        continue

    percentage = (
        result["above_75"]
        / result["total"]
        * 100
    )

    print(
        f"{result['name']:<28}"
        f"{result['max']:>12.6f}"
        f"{result['mean']:>12.6f}"
        f"{result['p95']:>12.6f}"
        f"{percentage:>11.2f}%"
    )


# ============================================================
# DIAGNOSIS
# ============================================================

print()
print("=" * 78)
print("                         DIAGNOSIS")
print("=" * 78)
print()

silence_result = results[0]

if silence_result is None:

    print(
        "[ERROR] Silence test failed."
    )

    sys.exit(1)


silence_max = silence_result["max"]
silence_mean = silence_result["mean"]
silence_p95 = silence_result["p95"]
silence_above = silence_result["above_75"]


if silence_max >= 0.99:

    print(
        "CRITICAL:"
    )

    print()

    print(
        "The ALFRED ONNX model produces an extremely "
        "high score on PURE DIGITAL SILENCE."
    )

    print()

    print(
        f"Maximum silence score : {silence_max:.9f}"
    )

    print(
        f"Mean silence score    : {silence_mean:.9f}"
    )

    print(
        f"95th percentile       : {silence_p95:.9f}"
    )

    print(
        f"Silence chunks >= 0.75: {silence_above}"
    )

    print()

    print(
        "This strongly indicates that the problem is "
        "inside the model or its expected input/preprocessing."
    )

    print()

    print(
        "DO NOT change the microphone listener yet."
    )


elif silence_max >= 0.75:

    print(
        "WARNING:"
    )

    print()

    print(
        "The model produces false-positive-level "
        "scores on pure digital silence."
    )

    print(
        f"Maximum silence score: {silence_max:.9f}"
    )

    print()

    print(
        "The ONNX model requires further investigation."
    )


else:

    print(
        "GOOD:"
    )

    print()

    print(
        "The ONNX model does not strongly activate "
        "on pure digital silence."
    )

    print()

    print(
        "That means the previous recording problem may "
        "involve preprocessing, audio content, or "
        "microphone/input conditions."
    )


print()
print("=" * 78)
print("                         TEST COMPLETE")
print("=" * 78)
print()
