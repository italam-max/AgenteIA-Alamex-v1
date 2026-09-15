import requests

from config.settings import settings
from integrations.media._common import DEFAULT_RETRY, download_bytes, poll_until

_BASE_URL = "https://api.siliconflow.com/v1"
_POLL_INTERVAL_SECONDS = 5
_POLL_TIMEOUT_SECONDS = 300

# SiliconFlow takes a fixed pixel size, not a ratio string — mapped per
# https://docs.siliconflow.com (9:16 -> 720x1280, 16:9 -> 1280x720, 1:1 -> 960x960). "4:5" has no
# exact match; falls back to the vertical size since it's closer to portrait than to square.
_ASPECT_RATIO_TO_SIZE = {
    "1:1": "960x960",
    "4:5": "720x1280",
    "9:16": "720x1280",
    "16:9": "1280x720",
}


class SiliconFlowVideoGenerationFailed(Exception):
    pass


class SiliconFlowVideoGenerator:
    """
    Generates a short silent b-roll clip via SiliconFlow's hosted Wan2.2 text-to-video model.
    Async job API: submit -> poll /video/status -> download the result url (valid ~1h).
    """

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.siliconflow_api_key}", "Content-Type": "application/json"}

    @DEFAULT_RETRY
    def generate_video(self, prompt: str, aspect_ratio: str = "9:16") -> bytes:
        if not settings.siliconflow_api_key:
            raise SiliconFlowVideoGenerationFailed("SILICONFLOW_API_KEY no está configurado en .env — necesario para generar video.")

        submit_response = requests.post(
            f"{_BASE_URL}/video/submit",
            headers=self._headers(),
            json={
                "model": settings.siliconflow_video_model_id,
                "prompt": prompt,
                "image_size": _ASPECT_RATIO_TO_SIZE.get(aspect_ratio, "720x1280"),
            },
            timeout=60,
        )
        submit_response.raise_for_status()
        request_id = submit_response.json()["requestId"]

        result = self._poll_until_done(request_id)

        videos = (result.get("results") or {}).get("videos") or []
        if not videos:
            raise SiliconFlowVideoGenerationFailed(f"SiliconFlow returned no video: {result}")

        return download_bytes(videos[0]["url"], timeout=120)

    def _poll_until_done(self, request_id: str) -> dict:
        def check() -> dict | None:
            status_response = requests.post(
                f"{_BASE_URL}/video/status", headers=self._headers(), json={"requestId": request_id}, timeout=30
            )
            status_response.raise_for_status()
            result = status_response.json()
            status = result.get("status")
            if status == "Failed":
                raise SiliconFlowVideoGenerationFailed(f"SiliconFlow video generation failed: {result.get('reason')}")
            return result if status == "Succeed" else None

        result = poll_until(check, timeout_s=_POLL_TIMEOUT_SECONDS, interval_s=_POLL_INTERVAL_SECONDS)
        if result is None:
            raise SiliconFlowVideoGenerationFailed(f"SiliconFlow video generation timed out after {_POLL_TIMEOUT_SECONDS}s")
        return result
