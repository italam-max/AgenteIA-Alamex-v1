import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

_FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "brand" / "fonts"
_HEADLINE_FONT_PATH = _FONTS_DIR / "ArchivoBlack-Regular.ttf"
_BODY_FONT_PATH = _FONTS_DIR / "Inter-Bold.ttf"

_NAVY = (10, 34, 64)
_ACCENT_BLUE = (30, 95, 217)
_WHITE = (255, 255, 255)
_BODY_GRAY = (40, 48, 61)
_PREMIUM_BG = (8, 15, 28)
_GOLD_LIGHT = (245, 214, 150)
_GOLD_DARK = (170, 125, 45)

# Matches the aspect ratios other media generators support (integrations/media/*.py).
_ASPECT_RATIO_DIMENSIONS = {
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
}

_MAX_BULLETS = 4


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.getlength(candidate) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _fit_headline(
    text: str, max_width: int, max_lines: int, start_size: int, min_size: int, upper: bool = True
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(str(_HEADLINE_FONT_PATH), size)
        lines = _wrap_text(text.upper() if upper else text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4
    return font, lines[:max_lines]


def _vertical_gradient(size: tuple[int, int], top_color: tuple, bottom_color: tuple) -> Image.Image:
    width, height = size
    column = Image.new("RGB", (1, max(height, 1)))
    for y in range(max(height, 1)):
        t = y / max(height - 1, 1)
        column.putpixel(
            (0, y),
            tuple(int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3)),
        )
    return column.resize((max(width, 1), max(height, 1)))


def _render_gradient_text(
    lines: list[str], font: ImageFont.FreeTypeFont, line_height: int, max_width: int, top_color: tuple, bottom_color: tuple
) -> Image.Image:
    height = line_height * len(lines)
    mask = Image.new("L", (max_width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    y = 0
    for line in lines:
        mask_draw.text((0, y), line, font=font, fill=255)
        y += line_height
    gradient = _vertical_gradient((max_width, height), top_color, bottom_color)
    rgba = Image.new("RGBA", (max_width, height), (0, 0, 0, 0))
    rgba.paste(gradient, (0, 0), mask=mask)
    return rgba


def _photo_cover_fit(photo_bytes: bytes, size: tuple[int, int]) -> Image.Image:
    photo = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    return ImageOps.fit(photo, size, method=Image.LANCZOS)


def _composite_logo(canvas: Image.Image, logo_bytes: bytes, position: tuple[int, int], target_width: int, chip: bool) -> None:
    """Pastes the real logo pixel-for-pixel. `chip` draws a white rounded rectangle behind it
    first, needed on dark backgrounds where the logo's navy wordmark would disappear."""
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    scale = target_width / logo.width
    logo = logo.resize((target_width, int(logo.height * scale)), Image.LANCZOS)

    x, y = position
    if chip:
        pad = int(target_width * 0.12)
        chip_box = (x - pad, y - pad, x + logo.width + pad, y + logo.height + pad)
        ImageDraw.Draw(canvas).rounded_rectangle(chip_box, radius=pad, fill=_WHITE)

    canvas.paste(logo, (x, y), mask=logo)


def _compose_infografia(photo_bytes: bytes, logo_bytes: bytes, headline: str, bullets: list[str], width: int, height: int) -> Image.Image:
    panel_width = int(width * 0.44)
    skew = int(width * 0.05)
    margin = int(width * 0.06)

    canvas = Image.new("RGB", (width, height), _WHITE)
    photo_fitted = _photo_cover_fit(photo_bytes, (width, height))
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).polygon(
        [(panel_width, 0), (width, 0), (width, height), (panel_width - skew, height)], fill=255
    )
    canvas.paste(photo_fitted, (0, 0), mask=mask)

    draw = ImageDraw.Draw(canvas)
    draw.line([(panel_width, 0), (panel_width - skew, height)], fill=_ACCENT_BLUE, width=max(4, int(width * 0.008)))

    text_max_width = panel_width - skew - 2 * margin
    headline_font, headline_lines = _fit_headline(
        headline, text_max_width, max_lines=4, start_size=int(width * 0.062), min_size=int(width * 0.032)
    )
    line_height = int(headline_font.size * 1.15)
    bullet_font = ImageFont.truetype(str(_BODY_FONT_PATH), int(width * 0.028))
    bullet_line_height = int(bullet_font.size * 1.35)
    bullet_circle_d = int(width * 0.045)

    bullets = bullets[:_MAX_BULLETS]
    bullet_block_lines = [
        _wrap_text(bullet, bullet_font, text_max_width - bullet_circle_d - margin // 2) for bullet in bullets
    ]

    y = int(height * 0.24)
    for line in headline_lines:
        draw.text((margin, y), line, font=headline_font, fill=_NAVY)
        y += line_height

    if bullets:
        y += margin
        for lines in bullet_block_lines:
            circle_xy = (margin, y)
            draw.ellipse(
                [circle_xy, (circle_xy[0] + bullet_circle_d, circle_xy[1] + bullet_circle_d)], fill=_ACCENT_BLUE
            )
            check_font = ImageFont.truetype(str(_BODY_FONT_PATH), int(bullet_circle_d * 0.55))
            draw.text(
                (circle_xy[0] + bullet_circle_d / 2, circle_xy[1] + bullet_circle_d / 2),
                "✓", font=check_font, fill=_WHITE, anchor="mm",
            )
            text_x = margin + bullet_circle_d + margin // 2
            text_y = circle_xy[1] + (bullet_circle_d - bullet_line_height) / 2
            for line in lines:
                draw.text((text_x, text_y), line, font=bullet_font, fill=_BODY_GRAY)
                text_y += bullet_line_height
            y += max(len(lines), 1) * bullet_line_height + margin // 2

    site_font = ImageFont.truetype(str(_BODY_FONT_PATH), int(width * 0.022))
    draw.text((margin, height - margin), "www.alam.mx", font=site_font, fill=_ACCENT_BLUE)

    _composite_logo(canvas, logo_bytes, (margin, margin), int(width * 0.24), chip=False)
    return canvas


def _compose_premium(photo_bytes: bytes, logo_bytes: bytes, headline: str, width: int, height: int) -> Image.Image:
    margin = int(width * 0.07)
    canvas = Image.new("RGB", (width, height), _PREMIUM_BG)
    draw = ImageDraw.Draw(canvas)

    # Thin gold accent lines, top-right corner — decorative, matches the real "premium" ads.
    for offset in (0, int(width * 0.025), int(width * 0.05)):
        draw.line(
            [(width * 0.7 + offset, 0), (width + offset, height * 0.3)],
            fill=_GOLD_DARK, width=max(2, int(width * 0.003)),
        )

    text_max_width = width - 2 * margin
    headline_font, headline_lines = _fit_headline(
        headline, text_max_width, max_lines=3, start_size=int(width * 0.09), min_size=int(width * 0.045)
    )
    line_height = int(headline_font.size * 1.1)
    text_y = int(height * 0.1)
    gradient_text = _render_gradient_text(headline_lines, headline_font, line_height, text_max_width, _GOLD_LIGHT, _GOLD_DARK)

    # Photo starts below wherever the headline actually ends — a fixed offset would overlap
    # the photo box when the headline wraps to 3 lines instead of 1-2.
    photo_top = text_y + len(headline_lines) * line_height + margin
    photo_box = (margin, photo_top, width - margin, height - margin)
    photo_fitted = _photo_cover_fit(photo_bytes, (photo_box[2] - photo_box[0], photo_box[3] - photo_box[1]))
    canvas.paste(photo_fitted, (photo_box[0], photo_box[1]))
    draw.rectangle(photo_box, outline=_GOLD_DARK, width=max(2, int(width * 0.004)))

    canvas.paste(gradient_text, (margin, text_y), mask=gradient_text)

    site_font = ImageFont.truetype(str(_BODY_FONT_PATH), int(width * 0.02))
    draw.text((margin, height - int(margin * 0.6)), "www.alam.mx", font=site_font, fill=_GOLD_LIGHT, anchor="lm")

    _composite_logo(canvas, logo_bytes, (margin, int(margin * 0.5)), int(width * 0.2), chip=True)
    return canvas


def _compose_hero(photo_bytes: bytes, logo_bytes: bytes, headline: str, width: int, height: int) -> Image.Image:
    canvas = _photo_cover_fit(photo_bytes, (width, height))

    gradient_h = int(height * 0.45)
    gradient = Image.new("L", (1, gradient_h), 0)
    for y in range(gradient_h):
        gradient.putpixel((0, y), int(200 * (y / max(gradient_h - 1, 1))))
    gradient = gradient.resize((width, gradient_h))
    overlay = Image.new("RGBA", (width, gradient_h), (0, 0, 0, 0))
    overlay.putalpha(gradient)
    black_layer = Image.new("RGBA", (width, gradient_h), (0, 0, 0, 255))
    black_layer.putalpha(gradient)
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(black_layer, dest=(0, height - gradient_h))
    canvas = canvas.convert("RGB")

    margin = int(width * 0.07)
    draw = ImageDraw.Draw(canvas)
    text_max_width = width - 2 * margin
    headline_font, headline_lines = _fit_headline(
        headline, text_max_width, max_lines=3, start_size=int(width * 0.075), min_size=int(width * 0.04)
    )
    line_height = int(headline_font.size * 1.15)
    total_text_height = line_height * len(headline_lines)
    y = height - margin - int(width * 0.03) - total_text_height
    for line in headline_lines:
        draw.text((margin, y), line, font=headline_font, fill=_WHITE)
        y += line_height

    site_font = ImageFont.truetype(str(_BODY_FONT_PATH), int(width * 0.02))
    draw.text((margin, height - int(margin * 0.5)), "www.alam.mx", font=site_font, fill=_WHITE, anchor="lm")

    _composite_logo(canvas, logo_bytes, (margin, margin), int(width * 0.2), chip=True)
    return canvas


def compose_template(
    photo_bytes: bytes,
    logo_bytes: bytes,
    headline: str,
    bullets: list[str],
    aspect_ratio: str = "1:1",
    layout: str = "infografia",
) -> bytes:
    """
    Builds a full graphic post — not just a background photo: a headline (and, in the
    'infografia' layout, up to 4 bullets) drawn with code next to/over an AI-generated or real
    reference photo. Unlike asking a generative image model to render text, every word here is
    drawn by Pillow from the exact strings passed in, so it can never come out garbled.

    `layout`: 'infografia' (data panel + photo, diagonal seam), 'premium' (dark/gold, one bold
    headline, no bullets), or 'hero' (full-bleed photo, headline overlaid at the bottom).
    """
    width, height = _ASPECT_RATIO_DIMENSIONS.get(aspect_ratio, _ASPECT_RATIO_DIMENSIONS["1:1"])

    if layout == "premium":
        canvas = _compose_premium(photo_bytes, logo_bytes, headline, width, height)
    elif layout == "hero":
        canvas = _compose_hero(photo_bytes, logo_bytes, headline, width, height)
    else:
        canvas = _compose_infografia(photo_bytes, logo_bytes, headline, bullets, width, height)

    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()
