import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def _get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing from .env")
    return Groq(api_key=api_key)


def transcribe_audio(audio_file: str) -> str:
    """
    Transcribe English, Urdu, Roman Urdu, or mixed speech.

    Whisper automatically detects the spoken language.
    """
    client = _get_client()

    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(
                audio_file,
                file.read(),
            ),
            model="whisper-large-v3",
            response_format="text",
        )

    return transcription.strip()