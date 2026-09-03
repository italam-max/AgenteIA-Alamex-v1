import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

_ENDPOINT = "https://fal.run/fal-ai/flux/schnell"

_ASPECT_RATIO_DIMENSIONS = {
    "1:1": (1024, 1024),
    "4:5": (896, 1120),
    "9:16": (768, 1344),
    "16:9": (1344, 768),
}


class FalGenerationFailed(Exception):
    pass


class FalGenerator:
    """Generates images via fal.ai's hosted FLUX.1 [schnell] model (pay-per-use, free signup credits)."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        # FLUX.1 [schnell] is text-to-image only — reference_image is ignored.
        width, height = _ASPECT_RATIO_DIMENSIONS.get(aspect_ratio, _ASPECT_RATIO_DIMENSIONS["1:1"])
        payload = {
            "prompt": prompt,
            "image_size": {"width": width, "height": height},
            "num_images": 1,
            "output_format": "png",
        }
        headers = {"Authorization": f"Key {settings.fal_api_key}"}
        response = requests.post(_ENDPOINT, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()

        images = result.get("images") or []
        if not images:
            raise FalGenerationFailed(f"fal.ai returned no images: {result}")

        image_response = requests.get(images[0]["url"], timeout=60)
        image_response.raise_for_status()
        return image_response.content
