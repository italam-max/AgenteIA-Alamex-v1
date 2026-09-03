import io

from PIL import Image

from integrations.media.compositing import overlay_logo


def _png_bytes(size: tuple[int, int], color) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", size, color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_overlay_logo_places_logo_in_bottom_right_corner():
    base = _png_bytes((1000, 1000), (255, 0, 0, 255))
    logo = _png_bytes((200, 100), (0, 255, 0, 255))

    result = overlay_logo(base, logo)
    composed = Image.open(io.BytesIO(result)).convert("RGB")

    assert composed.size == (1000, 1000)
    # Logo (220x110 after scaling to 22% width) sits within [740,960]x[850,960] with a 40px margin.
    logo_area_pixel = composed.getpixel((900, 900))
    assert logo_area_pixel == (0, 255, 0)
    # A pixel near the top-left should remain untouched (still red).
    top_left_pixel = composed.getpixel((10, 10))
    assert top_left_pixel == (255, 0, 0)
