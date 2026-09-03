import io

from PIL import Image


def overlay_logo(
    image_bytes: bytes,
    logo_bytes: bytes,
    position: str = "bottom-right",
    margin_ratio: float = 0.04,
    logo_width_ratio: float = 0.22,
) -> bytes:
    """
    Pastes the exact real logo file onto a generated image — pixel-for-pixel, not an
    AI-redrawn approximation. Works regardless of which MediaGenerator produced the base image.
    Returns PNG bytes.
    """
    base = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

    target_width = int(base.width * logo_width_ratio)
    scale = target_width / logo.width
    logo = logo.resize((target_width, int(logo.height * scale)), Image.LANCZOS)

    margin = int(base.width * margin_ratio)
    positions = {
        "bottom-right": (base.width - logo.width - margin, base.height - logo.height - margin),
        "bottom-left": (margin, base.height - logo.height - margin),
        "top-right": (base.width - logo.width - margin, margin),
        "top-left": (margin, margin),
    }
    xy = positions.get(position, positions["bottom-right"])

    composed = base.copy()
    composed.alpha_composite(logo, dest=xy)

    buffer = io.BytesIO()
    composed.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()
