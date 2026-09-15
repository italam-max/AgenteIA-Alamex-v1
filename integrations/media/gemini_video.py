import requests

from config.settings import settings
from integrations.media._common import DEFAULT_RETRY, download_bytes, poll_until

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_POLL_INTERVAL_SECONDS = 5
# Google documents Veo request latency as 11s-6min; poll a bit past the high end before giving up.
_POLL_TIMEOUT_SECONDS = 420


class GeminiVideoGenerationFailed(Exception):
    pass


class GeminiVideoGenerator:
    """
    Generates a short silent b-roll clip via Google's Veo (text-to-video) through the Gemini API
    — same GEMINI_API_KEY as integrations/media/gemini.py's image generator, different model.
    Video generation is a long-running operation: submit, poll until done, download the mp4.
    """

    def _headers(self) -> dict:
        return {"x-goog-api-key": settings.gemini_api_key, "Content-Type": "application/json"}

    @DEFAULT_RETRY
    def generate_video(self, prompt: str, aspect_ratio: str = "9:16") -> bytes:
        if not settings.gemini_api_key:
            raise GeminiVideoGenerationFailed("GEMINI_API_KEY no está configurado en .env — necesario para generar video.")

        response = requests.post(
            f"{_BASE_URL}/models/{settings.gemini_video_model_id}:predictLongRunning",
            headers=self._headers(),
            json={
                "instances": [{"prompt": prompt}],
                "parameters": {"aspectRatio": aspect_ratio, "resolution": "720p", "durationSeconds": "6"},
            },
            timeout=60,
        )
        response.raise_for_status()
        operation_name = response.json()["name"]

        operation = self._poll_until_done(operation_name)

        if operation.get("error"):
            raise GeminiVideoGenerationFailed(f"Veo video generation failed: {operation['error']}")

        try:
            video_uri = operation["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]["uri"]
        except (KeyError, IndexError) as exc:
            raise GeminiVideoGenerationFailed(f"Veo response missing video uri: {operation}") from exc

        return download_bytes(video_uri, timeout=120, headers=self._headers())

    def _poll_until_done(self, operation_name: str) -> dict:
        def check() -> dict | None:
            status_response = requests.get(f"{_BASE_URL}/{operation_name}", headers=self._headers(), timeout=30)
            status_response.raise_for_status()
            operation = status_response.json()
            return operation if operation.get("done") else None

        operation = poll_until(check, timeout_s=_POLL_TIMEOUT_SECONDS, interval_s=_POLL_INTERVAL_SECONDS)
        if operation is None:
            raise GeminiVideoGenerationFailed(f"Veo video generation timed out after {_POLL_TIMEOUT_SECONDS}s")
        return operation
