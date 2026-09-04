import io

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from rembg import remove

_BG_TOP = (245, 246, 248)
_BG_BOTTOM = (212, 216, 222)
_SHADOW_COLOR = (20, 24, 30)


def _studio_gradient(size: tuple[int, int]) -> Image.Image:
    width, height = size
    column = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        column.putpixel((0, y), tuple(int(_BG_TOP[i] + (_BG_BOTTOM[i] - _BG_TOP[i]) * t) for i in range(3)))
    return column.resize((width, height))


def _drop_shadow(size: tuple[int, int], center_x: int, bottom_y: int, width_ratio: float) -> Image.Image:
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    ellipse_w = int(size[0] * width_ratio)
    ellipse_h = int(ellipse_w * 0.22)
    box = (center_x - ellipse_w // 2, bottom_y - ellipse_h // 2, center_x + ellipse_w // 2, bottom_y + ellipse_h // 2)
    ImageDraw.Draw(shadow).ellipse(box, fill=(*_SHADOW_COLOR, 110))
    return shadow.filter(ImageFilter.GaussianBlur(radius=size[0] * 0.02))


def retouch_product_photo(photo_bytes: bytes, canvas_size: tuple[int, int] = (1600, 1600)) -> bytes:
    """
    Cuts the real product out of its original (often cluttered/factory-floor) background using
    ML-based segmentation (rembg — deterministic, not generative: it classifies pixels as
    foreground/background, it never invents or redraws the product), color-enhances just the
    product pixels, and composites it onto a clean studio gradient with a soft grounding shadow.
    Every pixel of the actual product is copied unchanged from the source photo — only the
    background around it and its overall contrast/saturation change. Returns PNG bytes.
    """
    foreground = remove(Image.open(io.BytesIO(photo_bytes)).convert("RGBA"))

    bbox = foreground.getbbox()
    if bbox is None:
        raise ValueError("rembg found no foreground subject in this photo")
    foreground = foreground.crop(bbox)

    enhanced_rgb = ImageEnhance.Contrast(foreground.convert("RGB")).enhance(1.08)
    enhanced_rgb = ImageEnhance.Color(enhanced_rgb).enhance(1.12)
    enhanced_rgb = ImageEnhance.Sharpness(enhanced_rgb).enhance(1.15)
    enhanced = Image.merge("RGBA", (*enhanced_rgb.split(), foreground.split()[-1]))

    max_fg_width = int(canvas_size[0] * 0.72)
    max_fg_height = int(canvas_size[1] * 0.72)
    scale = min(max_fg_width / enhanced.width, max_fg_height / enhanced.height, 1.0)
    if scale < 1.0:
        enhanced = enhanced.resize((int(enhanced.width * scale), int(enhanced.height * scale)), Image.LANCZOS)

    canvas = _studio_gradient(canvas_size).convert("RGBA")
    paste_x = (canvas_size[0] - enhanced.width) // 2
    paste_y = int(canvas_size[1] * 0.85) - enhanced.height

    shadow = _drop_shadow(canvas_size, canvas_size[0] // 2, paste_y + enhanced.height, width_ratio=0.5)
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(enhanced, dest=(paste_x, paste_y))

    buffer = io.BytesIO()
    canvas.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()
