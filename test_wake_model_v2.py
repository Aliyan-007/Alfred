import os
import sys
import math
import csv
import numpy as np
import soundfile as sf
from openwakeword.model import Model


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "alfred.onnx")

AUDIO_PATH = os.path.join(
    BASE_DIR,
    "Record (online-voice-recorder.com).mp3"
)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

# Main wake-word threshold.
THRESHOLD = 0.75

# Scores worth investigating.
HIGH_SCORE = 0.50

# Score considered extremely suspicious.
VERY_HIGH_SCORE = 0.90

# Audio below this RMS is considered "near silence".
# This is intentionally conservative.
SILENCE_RMS = 0.001

# Consecutive chunks separated by less than this amount
# are treated as one event.
EVENT_GAP_SECONDS = 0.40

CSV_PATH = os.path.join(
    BASE_DIR,
    "alfred_diagnostic_results.csv"
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def percentile(values, p):
    if not values:
        return 0.0

    return float(
        np.percentile(
            np.asarray(values, dtype=np.float64),
            p
        )
    )


def format_seconds(seconds):
    minutes = int(seconds // 60)
    remaining = seconds - (minutes * 60)

    return f"{minutes:02d}:{remaining:05.2f}"


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 78)
print("                    ALFRED WAKE WORD DIAGNOSTIC V2")
print("=" * 78)
print()

print(f"[MODEL] {MODEL_PATH}")
print(f"[AUDIO] {AUDIO_PATH}")
print()


# ============================================================
# CHECK FILES
# ============================================================

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
        "Copy the recording into the same folder as "
        "this script."
    )

    sys.exit(1)


# ============================================================
# LOAD AUDIO
# ============================================================

print("[AUDIO] Loading recording...")

try:

    audio, original_sample_rate = sf.read(
        AUDIO_PATH,
        dtype="float32",
        always_2d=False,
    )

except Exception as error:

    print()
    print(
        f"[ERROR] Could not read audio: {error}"
    )

    print()
    print(
        "If this MP3 cannot be read by soundfile, "
        "convert it to WAV first."
    )

    sys.exit(1)


# ============================================================
# MONO
# ============================================================

if audio.ndim == 2:

    print(
        f"[AUDIO] Stereo recording detected: "
        f"{audio.shape[1]} channels"
    )

    audio = np.mean(
        audio,
        axis=1
    )

else:

    print("[AUDIO] Mono recording detected.")


# ============================================================
# CLEAN
# ============================================================

audio = np.asarray(
    audio,
    dtype=np.float32
)

audio = np.nan_to_num(
    audio,
    nan=0.0,
    posinf=0.0,
    neginf=0.0
)

audio = np.clip(
    audio,
    -1.0,
    1.0
)


# ============================================================
# RESAMPLE
# ============================================================

print(
    f"[AUDIO] Original sample rate: "
    f"{original_sample_rate} Hz"
)

if original_sample_rate != SAMPLE_RATE:

    print(
        f"[AUDIO] Resampling to {SAMPLE_RATE} Hz..."
    )

    try:

        from scipy.signal import resample_poly

        gcd = math.gcd(
            int(original_sample_rate),
            SAMPLE_RATE
        )

        up = SAMPLE_RATE // gcd
        down = int(original_sample_rate) // gcd

        audio = resample_poly(
            audio,
            up,
            down
        ).astype(np.float32)

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
            "python -m pip install scipy"
        )

        sys.exit(1)

else:

    print(
        "[AUDIO] Already at 16 kHz."
    )


# ============================================================
# AUDIO INFORMATION
# ============================================================

duration = len(audio) / SAMPLE_RATE

global_rms = float(
    np.sqrt(
        np.mean(
            np.square(audio)
        )
    )
)

global_peak = float(
    np.max(
        np.abs(audio)
    )
)

print()
print("-" * 78)
print("AUDIO INFORMATION")
print("-" * 78)

print(
    f"Duration              : {duration:.2f} seconds"
)

print(
    f"Samples               : {len(audio)}"
)

print(
    f"Sample rate           : {SAMPLE_RATE} Hz"
)

print(
    f"Global RMS            : {global_rms:.6f}"
)

print(
    f"Global Peak           : {global_peak:.6f}"
)

print()


# ============================================================
# LOAD MODEL
# ============================================================

print(
    "[MODEL] Loading ALFRED wake-word model..."
)

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


print(
    "[MODEL] Model loaded successfully."
)

print()


# ============================================================
# INSPECT MODEL OUTPUT
# ============================================================

print("-" * 78)
print("MODEL OUTPUT CHECK")
print("-" * 78)

try:

    test_chunk = np.zeros(
        CHUNK_SIZE,
        dtype=np.int16
    )

    test_prediction = model.predict(
        test_chunk
    )

    print(
        f"Prediction dictionary:"
    )

    print(
        test_prediction
    )

    model_names = list(
        test_prediction.keys()
    )

    print()
    print(
        f"Model names: {model_names}"
    )

except Exception as error:

    print(
        f"[WARNING] Could not inspect model: {error}"
    )

    model_names = []


print()


# ============================================================
# RESET
# ============================================================

try:
    model.reset()
except Exception:
    pass


# ============================================================
# ANALYSIS STORAGE
# ============================================================

all_scores = []

high_scores = []

very_high_scores = []

detections = []

near_silence_scores = []

loud_scores = []

chunk_number = 0


# ============================================================
# ANALYSIS
# ============================================================

print("=" * 78)
print("                     ANALYZING RECORDING")
print("=" * 78)
print()

print(
    f"Chunk size            : {CHUNK_SIZE} samples"
)

print(
    f"Chunk duration        : "
    f"{CHUNK_SIZE / SAMPLE_RATE:.3f} seconds"
)

print(
    f"Detection threshold   : {THRESHOLD:.2f}"
)

print(
    f"High score threshold  : {HIGH_SCORE:.2f}"
)

print(
    f"Very high threshold   : {VERY_HIGH_SCORE:.2f}"
)

print(
    f"Near-silence RMS      : {SILENCE_RMS:.6f}"
)

print()


for start in range(
    0,
    len(audio),
    CHUNK_SIZE
):

    end = start + CHUNK_SIZE

    original_chunk = audio[start:end]

    if len(original_chunk) == 0:
        break

    chunk = original_chunk

    if len(chunk) < CHUNK_SIZE:

        padded = np.zeros(
            CHUNK_SIZE,
            dtype=np.float32
        )

        padded[
            :len(chunk)
        ] = chunk

        chunk = padded


    # --------------------------------------------------------
    # AUDIO LEVEL
    # --------------------------------------------------------

    audio_rms = float(
        np.sqrt(
            np.mean(
                np.square(chunk)
            )
        )
    )

    audio_peak = float(
        np.max(
            np.abs(chunk)
        )
    )


    # --------------------------------------------------------
    # MODEL INPUT
    # --------------------------------------------------------

    pcm = np.clip(
        chunk * 32767.0,
        -32768,
        32767
    ).astype(
        np.int16
    )


    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    try:

        prediction = model.predict(
            pcm
        )

    except Exception as error:

        print(
            f"[ERROR] Prediction failed at "
            f"{chunk_number}: {error}"
        )

        chunk_number += 1
        continue


    # --------------------------------------------------------
    # ALFRED SCORE
    # --------------------------------------------------------

    score = 0.0
    model_name = "alfred"

    if "alfred" in prediction:

        score = safe_float(
            prediction["alfred"]
        )

    else:

        for name, value in prediction.items():

            value = safe_float(value)

            if value > score:

                score = value
                model_name = name


    timestamp = (
        chunk_number
        * CHUNK_SIZE
        / SAMPLE_RATE
    )


    # --------------------------------------------------------
    # STORE
    # --------------------------------------------------------

    result = (
        timestamp,
        score,
        audio_rms,
        audio_peak
    )

    all_scores.append(result)


    # --------------------------------------------------------
    # CLASSIFY AUDIO
    # --------------------------------------------------------

    is_near_silence = (
        audio_rms < SILENCE_RMS
    )

    if is_near_silence:

        near_silence_scores.append(
            result
        )

    else:

        loud_scores.append(
            result
        )


    # --------------------------------------------------------
    # SCORE CATEGORIES
    # --------------------------------------------------------

    if score >= HIGH_SCORE:

        high_scores.append(
            result
        )


    if score >= VERY_HIGH_SCORE:

        very_high_scores.append(
            result
        )


    if score >= THRESHOLD:

        detections.append(
            result
        )


    # --------------------------------------------------------
    # PRINT INTERESTING RESULTS
    # --------------------------------------------------------

    if score >= HIGH_SCORE:

        print(
            f"{format_seconds(timestamp)} | "
            f"score={score:.6f} | "
            f"RMS={audio_rms:.6f} | "
            f"peak={audio_peak:.6f}"
        )


    chunk_number += 1


# ============================================================
# BASIC STATISTICS
# ============================================================

scores = [
    item[1]
    for item in all_scores
]

rms_values = [
    item[2]
    for item in all_scores
]

peak_values = [
    item[3]
    for item in all_scores
]


# ============================================================
# GROUP CONSECUTIVE DETECTIONS
# ============================================================

events = []

if detections:

    current_event = [
        detections[0]
    ]

    for item in detections[1:]:

        previous = current_event[-1]

        time_gap = (
            item[0] - previous[0]
        )

        if time_gap <= EVENT_GAP_SECONDS:

            current_event.append(item)

        else:

            events.append(
                current_event
            )

            current_event = [
                item
            ]

    events.append(
        current_event
    )


# ============================================================
# EVENT SUMMARIES
# ============================================================

event_summaries = []

for event in events:

    start_time = event[0][0]
    end_time = event[-1][0]

    maximum = max(
        event,
        key=lambda item: item[1]
    )

    minimum_rms = min(
        event,
        key=lambda item: item[2]
    )

    event_summaries.append(
        {
            "start": start_time,
            "end": end_time,
            "duration": end_time - start_time,
            "max_score": maximum[1],
            "max_score_time": maximum[0],
            "minimum_rms": minimum_rms[2],
            "minimum_rms_score": minimum_rms[1],
            "chunks": len(event),
        }
    )


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 78)
print("                         RESULTS")
print("=" * 78)
print()

print(
    f"Recording duration       : {duration:.2f}s"
)

print(
    f"Chunks analyzed          : {len(all_scores)}"
)

print(
    f"Detection threshold      : {THRESHOLD:.2f}"
)

print(
    f"High scores >= {HIGH_SCORE:.2f}     : "
    f"{len(high_scores)}"
)

print(
    f"Very high >= {VERY_HIGH_SCORE:.2f}  : "
    f"{len(very_high_scores)}"
)

print(
    f"Raw detections           : "
    f"{len(detections)}"
)

print(
    f"Grouped detection events : "
    f"{len(events)}"
)

print()


# ============================================================
# SCORE STATISTICS
# ============================================================

if scores:

    print("-" * 78)
    print("MODEL SCORE STATISTICS")
    print("-" * 78)

    print(
        f"Minimum score : {min(scores):.6f}"
    )

    print(
        f"Maximum score : {max(scores):.6f}"
    )

    print(
        f"Mean score    : {np.mean(scores):.6f}"
    )

    print(
        f"Median score  : {np.median(scores):.6f}"
    )

    print(
        f"90th percentile: {percentile(scores, 90):.6f}"
    )

    print(
        f"95th percentile: {percentile(scores, 95):.6f}"
    )

    print(
        f"99th percentile: {percentile(scores, 99):.6f}"
    )

    print()


# ============================================================
# NEAR-SILENCE ANALYSIS
# ============================================================

print("-" * 78)
print("NEAR-SILENCE ANALYSIS")
print("-" * 78)

print(
    f"Near-silence chunks : "
    f"{len(near_silence_scores)}"
)

if near_silence_scores:

    silence_scores = [
        item[1]
        for item in near_silence_scores
    ]

    max_silence = max(
        near_silence_scores,
        key=lambda item: item[1]
    )

    print(
        f"Average score       : "
        f"{np.mean(silence_scores):.6f}"
    )

    print(
        f"Maximum score       : "
        f"{max_silence[1]:.6f}"
    )

    print(
        f"Maximum score time  : "
        f"{max_silence[0]:.2f}s"
    )

    print(
        f"95th percentile     : "
        f"{percentile(silence_scores, 95):.6f}"
    )

    print(
        f"99th percentile     : "
        f"{percentile(silence_scores, 99):.6f}"
    )

    silence_detections = [
        item
        for item in near_silence_scores
        if item[1] >= THRESHOLD
    ]

    print(
        f"Silent chunks >= threshold : "
        f"{len(silence_detections)}"
    )

else:

    print(
        "No chunks were classified as near-silence."
    )

print()


# ============================================================
# MINIMUM RMS THAT PRODUCED HIGH SCORE
# ============================================================

high_rms_candidates = [
    item
    for item in all_scores
    if item[1] >= HIGH_SCORE
]

print("-" * 78)
print("QUIETEST AUDIO PRODUCING A HIGH SCORE")
print("-" * 78)

if high_rms_candidates:

    quietest = min(
        high_rms_candidates,
        key=lambda item: item[2]
    )

    print(
        f"Timestamp : {quietest[0]:.2f}s"
    )

    print(
        f"Score     : {quietest[1]:.6f}"
    )

    print(
        f"RMS       : {quietest[2]:.8f}"
    )

    print(
        f"Peak      : {quietest[3]:.8f}"
    )

else:

    print(
        "No high-score chunks found."
    )

print()


# ============================================================
# GROUPED EVENTS
# ============================================================

if event_summaries:

    print("-" * 78)
    print("FALSE-POSITIVE / DETECTION EVENTS")
    print("-" * 78)

    for index, event in enumerate(
        event_summaries,
        start=1
    ):

        print()

        print(
            f"EVENT #{index}"
        )

        print(
            f"  Start          : "
            f"{event['start']:.2f}s"
        )

        print(
            f"  End            : "
            f"{event['end']:.2f}s"
        )

        print(
            f"  Duration       : "
            f"{event['duration']:.2f}s"
        )

        print(
            f"  Chunks         : "
            f"{event['chunks']}"
        )

        print(
            f"  Maximum score  : "
            f"{event['max_score']:.6f}"
        )

        print(
            f"  Max score time : "
            f"{event['max_score_time']:.2f}s"
        )

        print(
            f"  Minimum RMS    : "
            f"{event['minimum_rms']:.8f}"
        )

        print(
            f"  Score at min RMS: "
            f"{event['minimum_rms_score']:.6f}"
        )

else:

    print(
        "No detection events."
    )

print()


# ============================================================
# TIMELINE
# ============================================================

print("-" * 78)
print("SCORE TIMELINE")
print("-" * 78)

print()

print(
    "Time       Score       RMS         Peak"
)

print(
    "-" * 50
)

# Print approximately one row every 0.5 seconds.
last_printed = -1.0

for item in all_scores:

    timestamp, score, rms, peak = item

    if timestamp - last_printed >= 0.48:

        print(
            f"{timestamp:6.2f}s   "
            f"{score:9.6f}   "
            f"{rms:9.6f}   "
            f"{peak:9.6f}"
        )

        last_printed = timestamp

print()


# ============================================================
# MAXIMUM SCORE
# ============================================================

if all_scores:

    maximum = max(
        all_scores,
        key=lambda item: item[1]
    )

    print("-" * 78)
    print("MAXIMUM MODEL SCORE")
    print("-" * 78)

    print(
        f"Timestamp : {maximum[0]:.2f}s"
    )

    print(
        f"Score     : {maximum[1]:.6f}"
    )

    print(
        f"RMS       : {maximum[2]:.8f}"
    )

    print(
        f"Peak      : {maximum[3]:.8f}"
    )

    print()


# ============================================================
# PERCENTAGES
# ============================================================

total_chunks = len(all_scores)

if total_chunks:

    high_percentage = (
        len(high_scores)
        / total_chunks
        * 100
    )

    detection_percentage = (
        len(detections)
        / total_chunks
        * 100
    )

    silence_detection_count = len([
        item
        for item in near_silence_scores
        if item[1] >= THRESHOLD
    ])

    if near_silence_scores:

        silence_detection_percentage = (
            silence_detection_count
            / len(near_silence_scores)
            * 100
        )

    else:

        silence_detection_percentage = 0.0

    print("-" * 78)
    print("RATIO ANALYSIS")
    print("-" * 78)

    print(
        f"Chunks above HIGH_SCORE : "
        f"{high_percentage:.2f}%"
    )

    print(
        f"Chunks above THRESHOLD  : "
        f"{detection_percentage:.2f}%"
    )

    print(
        f"Near-silence detections  : "
        f"{silence_detection_percentage:.2f}% "
        f"of near-silence chunks"
    )

    print()


# ============================================================
# DIAGNOSIS
# ============================================================

print("=" * 78)
print("                         DIAGNOSIS")
print("=" * 78)
print()


if not all_scores:

    print(
        "ERROR: No model predictions were produced."
    )

elif not detections:

    print(
        "GOOD: No ALFRED detections exceeded the "
        f"{THRESHOLD:.2f} threshold."
    )

    if high_scores:

        print()
        print(
            "However, the model produced some high scores."
        )

        print(
            "Those should be reviewed before using the "
            "model in a live listener."
        )

    else:

        print()
        print(
            "The model remained relatively quiet "
            "on this recording."
        )

else:

    print(
        "WARNING: ALFRED produced detections."
    )

    print()

    if silence_detection_count > 0:

        print(
            "CRITICAL FINDING:"
        )

        print(
            f"{silence_detection_count} near-silent "
            "chunk(s) produced scores above the "
            f"{THRESHOLD:.2f} threshold."
        )

        print()

        print(
            "This strongly suggests that the model "
            "is producing false positives on extremely "
            "low-level audio."
        )

    else:

        print(
            "The detections occurred during measurable "
            "audio activity."
        )

        print(
            "This makes microphone/background audio or "
            "preprocessing more likely."
        )

    print()

    if max(scores) >= 0.99:

        print(
            "The model is producing extremely "
            "high-confidence scores."
        )

        print(
            "Increasing the threshold alone is "
            "unlikely to solve the problem."
        )

    print()

    print(
        "Recommended investigation order:"
    )

    print(
        "  1. Verify audio preprocessing."
    )

    print(
        "  2. Test the model with pure digital silence."
    )

    print(
        "  3. Test another known-good wake-word model "
        "with the same audio."
    )

    print(
        "  4. Test ALFRED with a known-negative recording."
    )

    print(
        "  5. If ALFRED still scores near 1.0 on silence, "
        "investigate the custom ONNX model/training."
    )


# ============================================================
# CSV EXPORT
# ============================================================

print()
print("=" * 78)
print("                         CSV EXPORT")
print("=" * 78)
print()

try:

    with open(
        CSV_PATH,
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
            "timestamp",
            "score",
            "rms",
            "peak",
            "near_silence",
            "above_high_score",
            "above_threshold",
            "above_very_high"
        ])

        for (
            timestamp,
            score,
            rms,
            peak
        ) in all_scores:

            writer.writerow([
                f"{timestamp:.4f}",
                f"{score:.8f}",
                f"{rms:.8f}",
                f"{peak:.8f}",
                rms < SILENCE_RMS,
                score >= HIGH_SCORE,
                score >= THRESHOLD,
                score >= VERY_HIGH_SCORE
            ])

    print(
        f"Saved detailed results to:"
    )

    print(
        CSV_PATH
    )

except Exception as error:

    print(
        f"[WARNING] Could not save CSV: {error}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 78)
print("                       FINAL SUMMARY")
print("=" * 78)
print()

if all_scores:

    maximum = max(
        all_scores,
        key=lambda item: item[1]
    )

    print(
        f"Maximum score       : "
        f"{maximum[1]:.6f}"
    )

    print(
        f"Maximum score time  : "
        f"{maximum[0]:.2f}s"
    )

    print(
        f"Maximum-score RMS   : "
        f"{maximum[2]:.8f}"
    )

    print(
        f"Raw detections      : "
        f"{len(detections)}"
    )

    print(
        f"Detection events    : "
        f"{len(events)}"
    )

    print(
        f"Near-silence chunks : "
        f"{len(near_silence_scores)}"
    )

    print(
        f"Silent false hits   : "
        f"{len([x for x in near_silence_scores if x[1] >= THRESHOLD])}"
    )

print()

print("=" * 78)
print("                       TEST COMPLETE")
print("=" * 78)
print()
