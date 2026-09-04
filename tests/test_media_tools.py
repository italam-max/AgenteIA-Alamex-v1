from unittest.mock import MagicMock, patch

from tools import media_tools

_EXPECTED_PROMPT = "a red bicycle" + media_tools._NO_TEXT_SUFFIX


@patch("tools.media_tools.get_generator")
def test_generate_image_skips_compositing_when_no_logo_file(mock_get_generator):
    media_tools._load_brand_logo.cache_clear()
    mock_generator = MagicMock()
    mock_generator.generate_image.return_value = b"raw-image-bytes"
    mock_get_generator.return_value = mock_generator

    with patch.object(media_tools, "_BRAND_LOGO_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = media_tools.generate_image.invoke({"prompt": "a red bicycle", "headline": "Título"})

    mock_generator.generate_image.assert_called_once_with(_EXPECTED_PROMPT, "1:1", reference_image=None)
    assert result == b"raw-image-bytes"
    media_tools._load_brand_logo.cache_clear()


@patch("tools.media_tools.compose_template")
@patch("tools.media_tools.get_generator")
def test_generate_image_composes_template_with_generated_photo(mock_get_generator, mock_compose_template):
    media_tools._load_brand_logo.cache_clear()
    mock_generator = MagicMock()
    mock_generator.generate_image.return_value = b"raw-photo-bytes"
    mock_get_generator.return_value = mock_generator
    mock_compose_template.return_value = b"composed-image-bytes"

    with patch.object(media_tools, "_BRAND_LOGO_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"logo-bytes"
        result = media_tools.generate_image.invoke(
            {"prompt": "a red bicycle", "headline": "Título", "bullets": ["dato 1", "dato 2"], "layout": "premium"}
        )

    mock_generator.generate_image.assert_called_once_with(_EXPECTED_PROMPT, "1:1", reference_image=b"logo-bytes")
    mock_compose_template.assert_called_once_with(
        b"raw-photo-bytes", b"logo-bytes", "Título", ["dato 1", "dato 2"], "1:1", "premium"
    )
    assert result == b"composed-image-bytes"
    media_tools._load_brand_logo.cache_clear()


@patch("tools.media_tools.load_reference_photo")
@patch("tools.media_tools.compose_template")
@patch("tools.media_tools.get_generator")
def test_generate_image_uses_reference_photo_instead_of_generating(
    mock_get_generator, mock_compose_template, mock_load_reference_photo
):
    media_tools._load_brand_logo.cache_clear()
    mock_load_reference_photo.return_value = b"real-product-photo-bytes"
    mock_compose_template.return_value = b"composed-image-bytes"
    mock_generator = MagicMock()
    mock_get_generator.return_value = mock_generator

    with patch.object(media_tools, "_BRAND_LOGO_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"logo-bytes"
        result = media_tools.generate_image.invoke(
            {"prompt": "unused", "headline": "Título", "reference_photo": "mrlg_cabina.jpg"}
        )

    mock_load_reference_photo.assert_called_once_with("mrlg_cabina.jpg")
    mock_generator.generate_image.assert_not_called()
    mock_compose_template.assert_called_once_with(
        b"real-product-photo-bytes", b"logo-bytes", "Título", [], "1:1", "infografia"
    )
    assert result == b"composed-image-bytes"
    media_tools._load_brand_logo.cache_clear()
