from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from config.settings import settings
from integrations.media.registry import get_generator
from integrations.media.template_compositor import compose_template
from tools.product_photos_tools import load_reference_photo

_BRAND_LOGO_PATH = Path(__file__).resolve().parent.parent / "brand" / "logo_primary.png"

# Higgsfield's Soul model has no negative_prompt field, and stacking "no text/no words/no
# letters..." into the positive prompt backfired in testing (made up MORE fake text/UI overlays
# — negation in a positive-only prompt is unreliable across diffusion models in general). The
# only prompt-level lever that actually works is avoiding scene elements that invite text in the
# first place (control panels, digital displays, signage, stickers) — enforced in the system
# prompt (agents/prompts/social_media_system.md), not here. Any headline/data text the post needs
# is drawn separately by template_compositor, never by the image generator itself.
_NO_TEXT_SUFFIX = ", clean minimalist surfaces, no signage, no stickers, no plaques"


@lru_cache(maxsize=1)
def _load_brand_logo() -> bytes | None:
    if _BRAND_LOGO_PATH.exists():
        return _BRAND_LOGO_PATH.read_bytes()
    return None


@tool
def generate_image(
    prompt: str,
    headline: str,
    bullets: list[str] | None = None,
    aspect_ratio: str = "1:1",
    layout: str = "infografia",
    reference_photo: str | None = None,
) -> bytes:
    """
    Generate a complete on-brand graphic post. Returns PNG bytes.
    If `reference_photo` names a real photo (see list_reference_photos), it's used as-is instead
    of generating one — more authentic and doesn't spend generation credits. Otherwise `prompt`
    describes the background photo to generate (scene/composition/lighting only — no text/panels,
    those are unreliable from an image generator). `headline` and, in the 'infografia' layout,
    `bullets` are drawn with real fonts by code, so they always render exactly as written. The
    real brand logo is composited automatically — do not describe it in `prompt`.
    """
    logo_bytes = _load_brand_logo()

    photo_bytes = load_reference_photo(reference_photo) if reference_photo else None
    if photo_bytes is None:
        photo_bytes = get_generator(settings.media_generator).generate_image(
            prompt + _NO_TEXT_SUFFIX, aspect_ratio, reference_image=logo_bytes
        )

    if logo_bytes is None:
        return photo_bytes
    return compose_template(photo_bytes, logo_bytes, headline, bullets or [], aspect_ratio, layout)
