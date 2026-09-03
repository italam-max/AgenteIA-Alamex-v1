from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from config.settings import settings
from integrations.media.compositing import overlay_logo
from integrations.media.registry import get_generator

_BRAND_LOGO_PATH = Path(__file__).resolve().parent.parent / "brand" / "logo_primary.png"


@lru_cache(maxsize=1)
def _load_brand_logo() -> bytes | None:
    if _BRAND_LOGO_PATH.exists():
        return _BRAND_LOGO_PATH.read_bytes()
    return None


@tool
def generate_image(prompt: str, aspect_ratio: str = "1:1") -> bytes:
    """
    Generate an on-brand image from a text prompt. Returns PNG bytes.
    Passes the real brand logo (brand/logo_primary.png) as a reference image to generators that
    support image-conditioned generation (e.g. Gemini); regardless of backend, the exact real
    logo file is then composited onto the result (bottom-right corner) for guaranteed fidelity —
    it is pasted pixel-for-pixel, never AI-redrawn.
    """
    logo_bytes = _load_brand_logo()
    image_bytes = get_generator(settings.media_generator).generate_image(
        prompt, aspect_ratio, reference_image=logo_bytes
    )
    if logo_bytes is not None:
        image_bytes = overlay_logo(image_bytes, logo_bytes)
    return image_bytes
