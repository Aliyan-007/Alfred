import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

PIPER = BASE_DIR / "piper" / "piper.exe"
MODEL = BASE_DIR / "models" / "piper" / "ur_PK-aegis_female-medium.onnx"
ESPEAK = BASE_DIR / "piper" / "espeak-ng-data"
OUTPUT = BASE_DIR / "aegis_test.wav"


text = "وعلیکم السلام، میرا نام فریڈے ہے۔"


print("Text being sent to Piper:")
print(text)
print()

process = subprocess.Popen(
    [
        str(PIPER),
        "--model",
        str(MODEL),
        "--output_file",
        str(OUTPUT),
        "--espeak_data",
        str(ESPEAK),
    ],
    stdin=subprocess.PIPE,
)

process.stdin.write(text.encode("utf-8"))
process.stdin.close()

exit_code = process.wait()

print()
print("Piper exit code:", exit_code)

if OUTPUT.exists():
    print("WAV created:", OUTPUT)
    print("WAV size:", OUTPUT.stat().st_size, "bytes")
else:
    print("WAV was NOT created.")