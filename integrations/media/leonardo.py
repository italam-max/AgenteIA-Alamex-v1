import io

import requests
from PIL import Image

from config.settings import settings
from integrations.media._common import DEFAULT_RETRY, download_bytes, poll_until

_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

# width, height per aspect ratio, multiples of 8 (Phoenix supports up to ~1.7MP).
_ASPECT_RATIO_DIMENSIONS = {
    "1:1": (1024, 1024),
    "4:5": (896, 1120),
    "9:16": (768, 1344),
    "16:9": (1344, 768),
}


class LeonardoJobFailed(Exception):
    pass


class LeonardoJobTimeout(Exception):
    pass


class LeonardoGenerator:
    """Generates images via the Leonardo.ai hosted API (paid credits, generous free daily allowance)."""

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.leonardo_api_key}", "Content-Type": "application/json"}

    @DEFAULT_RETRY
    def _create_generation(self, prompt: str, width: int, height: int) -> str:
        payload = {
            "prompt": prompt,
            "modelId": settings.leonardo_model_id,
            "width": width,
            "height": height,
            "num_images": 1,
        }
        response = requests.post(f"{_BASE_URL}/generations", json=payload, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()["sdGenerationJob"]["generationId"]

    def _get_generation(self, generation_id: str) -> dict:
        response = requests.get(f"{_BASE_URL}/generations/{generation_id}", headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()["generations_by_pk"]

    def _wait_for_image_url(self, generation_id: str, timeout_s: int = 120, poll_interval_s: int = 3) -> str:
        def check() -> str | None:
            generation = self._get_generation(generation_id)
            status = generation.get("status")
            if status == "COMPLETE":
                images = generation.get("generated_images") or []
                if images:
                    return images[0]["url"]
                raise LeonardoJobFailed(f"Generation {generation_id} completed with no images")
            if status == "FAILED":
                raise LeonardoJobFailed(f"Generation {generation_id} failed")
            return None

        image_url = poll_until(check, timeout_s=timeout_s, interval_s=poll_interval_s)
        if image_url is None:
            raise LeonardoJobTimeout(f"Generation {generation_id} did not complete within {timeout_s}s")
        return image_url

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        # This adapter only calls the text-to-image endpoint — reference_image is ignored.
        width, height = _ASPECT_RATIO_DIMENSIONS.get(aspect_ratio, _ASPECT_RATIO_DIMENSIONS["1:1"])
        generation_id = self._create_generation(prompt, width, height)
        image_url = self._wait_for_image_url(generation_id)

        raw_bytes = download_bytes(image_url)
        # Leonardo serves JPEG — normalize to PNG so the rest of the pipeline (upload, publish)
        # can keep assuming PNG regardless of which media backend is active.
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
