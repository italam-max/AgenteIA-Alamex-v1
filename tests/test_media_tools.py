from unittest.mock import MagicMock, patch

from tools import media_tools


@patch("tools.media_tools.overlay_logo")
@patch("tools.media_tools.get_generator")
def test_generate_image_skips_overlay_when_no_logo_file(mock_get_generator, mock_overlay_logo):
    media_tools._load_brand_logo.cache_clear()
    mock_generator = MagicMock()
    mock_generator.generate_image.return_value = b"raw-image-bytes"
    mock_get_generator.return_value = mock_generator

    with patch.object(media_tools, "_BRAND_LOGO_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = media_tools.generate_image.invoke({"prompt": "a red bicycle"})

    mock_generator.generate_image.assert_called_once_with("a red bicycle", "1:1", reference_image=None)
    mock_overlay_logo.assert_not_called()
    assert result == b"raw-image-bytes"
    media_tools._load_brand_logo.cache_clear()


@patch("tools.media_tools.overlay_logo")
@patch("tools.media_tools.get_generator")
def test_generate_image_composites_real_logo_when_file_exists(mock_get_generator, mock_overlay_logo):
    media_tools._load_brand_logo.cache_clear()
    mock_generator = MagicMock()
    mock_generator.generate_image.return_value = b"raw-image-bytes"
    mock_get_generator.return_value = mock_generator
    mock_overlay_logo.return_value = b"composited-image-bytes"

    with patch.object(media_tools, "_BRAND_LOGO_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.read_bytes.return_value = b"logo-bytes"
        result = media_tools.generate_image.invoke({"prompt": "a red bicycle"})

    mock_generator.generate_image.assert_called_once_with("a red bicycle", "1:1", reference_image=b"logo-bytes")
    mock_overlay_logo.assert_called_once_with(b"raw-image-bytes", b"logo-bytes")
    assert result == b"composited-image-bytes"
    media_tools._load_brand_logo.cache_clear()
