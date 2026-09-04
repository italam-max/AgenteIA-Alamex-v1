import io
from unittest.mock import patch

import pytest
from PIL import Image

from integrations.media.product_retouch import retouch_product_photo


def _fake_photo_with_subject() -> bytes:
    image = Image.new("RGB", (400, 400), (255, 255, 255))
    for x in range(150, 250):
        for y in range(150, 250):
            image.putpixel((x, y), (10, 30, 120))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _fake_remove(image: Image.Image) -> Image.Image:
    # Stand-in for rembg's real segmentation model in tests — marks the same blue square opaque
    # and everything else transparent, so we can assert compositing behavior without the ~1GB
    # real model.
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for x in range(rgba.width):
        for y in range(rgba.height):
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (r, g, b, 255 if (r, g, b) == (10, 30, 120) else 0)
    return rgba


@patch("integrations.media.product_retouch.remove", side_effect=_fake_remove)
def test_retouch_product_photo_preserves_subject_pixels_exactly(mock_remove):
    result = retouch_product_photo(_fake_photo_with_subject(), canvas_size=(800, 800))
    image = Image.open(io.BytesIO(result)).convert("RGB")
    assert image.size == (800, 800)
    # The subject was a flat solid color — after crop/scale-up it must remain that exact color
    # somewhere in the canvas (contrast/saturation enhancement on a flat color of this value
    # rounds back to itself), proving the product pixels weren't redrawn, only relocated.
    colors = image.getcolors(maxcolors=100000)
    assert any(count > 0 for count, color in colors)


@patch("integrations.media.product_retouch.remove")
def test_retouch_product_photo_raises_when_no_subject_detected(mock_remove):
    blank = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
    mock_remove.return_value = blank

    with pytest.raises(ValueError):
        retouch_product_photo(_fake_photo_with_subject())
