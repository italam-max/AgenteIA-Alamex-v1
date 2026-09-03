import io
from unittest.mock import MagicMock, patch

from PIL import Image

from integrations.media.leonardo import LeonardoGenerator


def _mock_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


def _fake_jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color="red").save(buffer, format="JPEG")
    return buffer.getvalue()


@patch("integrations.media.leonardo.time.sleep", return_value=None)
@patch("integrations.media.leonardo.requests.get")
@patch("integrations.media.leonardo.requests.post")
def test_generate_image_polls_until_complete_and_returns_png_bytes(mock_post, mock_get, _sleep):
    mock_post.return_value = _mock_response({"sdGenerationJob": {"generationId": "gen-1"}})

    poll_pending = _mock_response({"generations_by_pk": {"status": "PENDING"}})
    poll_complete = _mock_response(
        {"generations_by_pk": {"status": "COMPLETE", "generated_images": [{"url": "https://cdn.leonardo.ai/out.jpg"}]}}
    )
    image_download = MagicMock()
    image_download.content = _fake_jpeg_bytes()
    # requests.get is used both for polling status and for downloading the final image.
    mock_get.side_effect = [poll_pending, poll_complete, image_download]

    result = LeonardoGenerator().generate_image("a red bicycle", aspect_ratio="1:1")

    assert result[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes — confirms JPEG->PNG normalization
    sent_json = mock_post.call_args.kwargs["json"]
    assert sent_json["prompt"] == "a red bicycle"
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-leonardo-key"
