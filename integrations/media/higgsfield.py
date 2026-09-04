import os

import requests
from higgsfield_client import subscribe
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

# Higgsfield doesn't support 4:5 — map to the closest supported ratio.
_ASPECT_RATIO_MAP = {
    "1:1": "1:1",
    "4:5": "3:4",
    "9:16": "9:16",
    "16:9": "16:9",
}


class HiggsfieldGenerationFailed(Exception):
    pass


class HiggsfieldGenerator:
    """Generates images via Higgsfield AI's hosted Soul model (paid, async job API)."""

    def _ensure_credentials_in_env(self) -> None:
        # higgsfield_client reads credentials lazily from the process env on first call,
        # not from a constructor — this project's settings live in .env instead, so wire
        # them into os.environ right before use.
        os.environ["HF_KEY"] = f"{settings.higgsfield_api_key_id}:{settings.higgsfield_api_key_secret}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        # Soul v2 standard is text-to-image only — reference_image is ignored.
        self._ensure_credentials_in_env()
        result = subscribe(
            settings.higgsfield_model_id,
            arguments={
                "prompt": prompt,
                "aspect_ratio": _ASPECT_RATIO_MAP.get(aspect_ratio, "1:1"),
                "resolution": "1080p",
            },
        )

        images = result.get("images") or []
        if not images:
            raise HiggsfieldGenerationFailed(f"Higgsfield returned no images: {result}")

        image_response = requests.get(images[0]["url"], timeout=60)
        image_response.raise_for_status()
        return image_response.content
