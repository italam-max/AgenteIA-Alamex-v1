import base64

import requests

from config.settings import settings
from integrations.media._common import DEFAULT_RETRY

_ASPECT_RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "4:5": "1024x1536",
    "9:16": "1024x1536",
    "16:9": "1536x1024",
}


class OpenAIGenerationFailed(Exception):
    pass


class OpenAIGenerator:
    """
    Generates images via OpenAI's image API (gpt-image-2 by default — see
    OPENAI_IMAGE_MODEL_ID). Like Gemini, this backend can take a reference image (e.g. the real
    brand logo) and compose it into the result via the edits endpoint; without one it falls back
    to text-to-image generation.
    """

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.openai_api_key}"}

    @DEFAULT_RETRY
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        size = _ASPECT_RATIO_TO_SIZE.get(aspect_ratio, _ASPECT_RATIO_TO_SIZE["1:1"])

        if reference_image is not None:
            response = requests.post(
                "https://api.openai.com/v1/images/edits",
                headers=self._headers(),
                data={
                    "model": settings.openai_image_model_id,
                    "prompt": (
                        f"Use the attached logo image exactly as provided (do not redraw or alter it) and "
                        f"incorporate it naturally into this scene: {prompt}"
                    ),
                    "size": size,
                },
                files={"image": ("reference.png", reference_image, "image/png")},
                timeout=120,
            )
        else:
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"model": settings.openai_image_model_id, "prompt": prompt, "size": size, "n": 1},
                timeout=120,
            )
        response.raise_for_status()
        result = response.json()

        data = result.get("data") or []
        if data and data[0].get("b64_json"):
            return base64.b64decode(data[0]["b64_json"])

        raise OpenAIGenerationFailed(f"OpenAI response contained no image: {result}")
