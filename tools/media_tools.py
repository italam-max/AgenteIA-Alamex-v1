from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from config.settings import settings
from integrations.media.openai_tts import generate_speech
from integrations.media.registry import get_generator, get_video_generator
from integrations.media.template_compositor import compose_template
from integrations.media.video_compositor import compose_voiceover_video
from tools.product_photos_tools import load_reference_photo

_BRAND_LOGO_PATH = Path(__file__).resolve().parent.parent / "brand" / "logo_primary.png"

# Higgsfield's Soul model has no negative_prompt field, and stacking "no text/no words/no
# letters..." into the positive prompt backfired in testing (made up MORE fake text/UI overlays
# — negation in a positive-only prompt is unreliable across diffusion/video models in general).
# The only prompt-level lever that actually works is avoiding scene elements that invite text in
# the first place (control panels, digital displays, signage, stickers) — enforced in the system
# prompt (agents/prompts/social_media_system.md), not here. Applied to both generate_image and
# generate_video: any headline/data text a post needs is drawn separately by template_compositor
# (images only — there's no equivalent compositing step for video), never by the generator itself.
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
    is_real_photo = photo_bytes is not None
    if photo_bytes is None:
        # Not passing logo_bytes as reference_image here on purpose: backends that support it
        # (gemini/openai) take that as an instruction to draw the logo *into* the generated scene
        # (e.g. onto a beam or building facade) — in practice a warped/misspelled re-render of it,
        # duplicating the crisp, correctly-placed logo compose_template adds below. One correct
        # logo beats one correct + one garbled.
        photo_bytes = get_generator(settings.media_generator).generate_image(prompt + _NO_TEXT_SUFFIX, aspect_ratio)

    if logo_bytes is None:
        return photo_bytes
    return compose_template(
        photo_bytes, logo_bytes, headline, bullets or [], aspect_ratio, layout, anchor_bottom=is_real_photo
    )


@tool
def generate_video(prompt: str, narration: str, aspect_ratio: str = "9:16") -> bytes:
    """
    Generate a short video post: a silent b-roll clip (backend chosen by VIDEO_GENERATOR) with an
    OpenAI-narrated voiceover muxed on top (looped to cover the narration's length). Returns mp4
    bytes. `prompt` describes the visual scene only — no on-screen text/logo, there is no
    compositing step for video like there is for images. `narration` is the spoken voiceover script.
    """
    video_bytes = get_video_generator(settings.video_generator).generate_video(prompt + _NO_TEXT_SUFFIX, aspect_ratio)
    audio_bytes = generate_speech(narration)
    return compose_voiceover_video(video_bytes, audio_bytes)
