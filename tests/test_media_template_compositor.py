import io

from PIL import Image

from integrations.media.template_compositor import _load_logo_variants, _wrap_text, compose_template


def _solid_png(color=(120, 140, 160), size=(800, 800)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def _real_logo_bytes() -> bytes:
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "brand" / "logo_primary.png"
    return path.read_bytes()


def test_compose_template_returns_correct_canvas_size_per_aspect_ratio():
    result = compose_template(_solid_png(), _real_logo_bytes(), "Título de prueba", ["dato uno"], "4:5")
    image = Image.open(io.BytesIO(result))
    assert image.size == (1080, 1350)


def test_compose_template_handles_empty_bullets():
    result = compose_template(_solid_png(), _real_logo_bytes(), "Solo headline, sin bullets", [], "1:1")
    image = Image.open(io.BytesIO(result))
    assert image.size == (1080, 1080)


def test_compose_template_caps_bullets_at_four():
    # Should not raise even with more than _MAX_BULLETS entries.
    bullets = [f"dato {i}" for i in range(10)]
    result = compose_template(_solid_png(), _real_logo_bytes(), "Muchos datos", bullets, "1:1")
    assert Image.open(io.BytesIO(result)).size == (1080, 1080)


def test_load_logo_variants_derives_real_transparency_and_white_recolor():
    color_logo, white_logo = _load_logo_variants(_real_logo_bytes())

    # The source PNG has no real alpha channel (flat white background baked into the pixels) — a
    # degenerate/failed color-key would leave alpha uniformly 255 everywhere.
    assert color_logo.mode == "RGBA"
    alpha_values = set(color_logo.split()[-1].getdata())
    assert alpha_values != {255}
    assert 0 in alpha_values  # background corners should key out to fully transparent

    # Corner pixels are background in this logo — should be transparent in both variants.
    corner_alpha = color_logo.getpixel((0, 0))[3]
    assert corner_alpha < 10

    # White variant: same alpha shape, but every non-transparent pixel is pure white.
    assert list(white_logo.split()[-1].getdata()) == list(color_logo.split()[-1].getdata())
    opaque_pixels = [px for px in white_logo.getdata() if px[3] > 200]
    assert opaque_pixels  # sanity: the logo mark itself must still be present
    assert all(px[:3] == (255, 255, 255) for px in opaque_pixels)


def test_wrap_text_splits_long_text_to_fit_width():
    from PIL import ImageFont

    from integrations.media.template_compositor import _BODY_FONT_PATH

    font = ImageFont.truetype(str(_BODY_FONT_PATH), 30)
    lines = _wrap_text("Hasta 2000 kg de capacidad y 26 personas por viaje", font, max_width=200)
    assert len(lines) > 1
    for line in lines:
        assert font.getlength(line) <= 200 or " " not in line
