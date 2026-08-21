from voice.stt import transcribe_audio


audio_file = "test_recording.wav"

print("Sending recording to Groq Whisper...")

text = transcribe_audio(audio_file)

print()
print("Alfred heard:")
print(text)