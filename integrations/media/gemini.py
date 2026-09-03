import base64

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

_ASPECT_RATIO_TEXT = {
    "1:1": "square (1:1 aspect ratio)",
    "4:5": "portrait (4:5 aspect ratio)",
    "9:16": "vertical (9:16 aspect ratio)",
    "16:9": "widescreen (16:9 aspect ratio)",
}


class GeminiGenerationFailed(Exception):
    pass


class GeminiGenerator:
    """
    Generates images via the Gemini API (gemini-2.5-flash-image, aka "nano banana"). Free tier
    available directly via API key, no billing required. Unlike text-to-image-only backends, this
    one can take a reference image (e.g. the real brand logo) and compose it into the result.
    """

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        aspect_text = _ASPECT_RATIO_TEXT.get(aspect_ratio, _ASPECT_RATIO_TEXT["1:1"])
        parts: list[dict] = [{"text": f"{prompt}\n\nGenerate a {aspect_text} image."}]
        if reference_image is not None:
            parts.insert(
                0,
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(reference_image).decode("ascii"),
                    }
                },
            )
            parts[1]["text"] = (
                f"Use the attached logo image exactly as provided (do not redraw or alter it) and "
                f"incorporate it naturally into this scene: {prompt}\n\nGenerate a {aspect_text} image."
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_image_model_id}:generateContent"
        response = requests.post(
            url,
            headers={"x-goog-api-key": settings.gemini_api_key, "Content-Type": "application/json"},
            json={"contents": [{"parts": parts}]},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        candidates = result.get("candidates") or []
        for candidate in candidates:
            for part in candidate.get("content", {}).get("parts", []):
                inline_data = part.get("inlineData") or part.get("inline_data")
                if inline_data and inline_data.get("data"):
                    return base64.b64decode(inline_data["data"])

        raise GeminiGenerationFailed(f"Gemini response contained no image: {result}")
