from recorder import record_audio
from stt import transcribe_audio


audio_file = record_audio(
    output_file="voice_input.wav",
    duration=5,
)

text = transcribe_audio(audio_file)

print()
print("You said:")
print(text)