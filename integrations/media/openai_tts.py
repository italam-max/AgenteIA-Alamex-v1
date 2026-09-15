import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings


class OpenAITTSGenerationFailed(Exception):
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
def generate_speech(text: str) -> bytes:
    """Converts narration text to spoken audio (mp3 bytes) via OpenAI's text-to-speech API."""
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
        json={
            "model": settings.openai_tts_model_id,
            "voice": settings.openai_tts_voice,
            "input": text,
            "response_format": "mp3",
        },
        timeout=60,
    )
    response.raise_for_status()
    if not response.content:
        raise OpenAITTSGenerationFailed(f"OpenAI TTS response was empty (status {response.status_code})")
    return response.content
