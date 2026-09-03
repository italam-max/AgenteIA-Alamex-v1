from unittest.mock import MagicMock, patch

from integrations.media.fal import FalGenerator


def _mock_response(json_data=None, content=None):
    response = MagicMock()
    if json_data is not None:
        response.json.return_value = json_data
    if content is not None:
        response.content = content
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media.fal.requests.get")
@patch("integrations.media.fal.requests.post")
def test_generate_image_downloads_returned_url(mock_post, mock_get):
    mock_post.return_value = _mock_response(
        json_data={"images": [{"url": "https://fal.media/out.png", "width": 1024, "height": 1024}]}
    )
    mock_get.return_value = _mock_response(content=b"fake-png-bytes")

    result = FalGenerator().generate_image("a red bicycle", aspect_ratio="1:1")

    assert result == b"fake-png-bytes"
    assert mock_post.call_args.args[0] == "https://fal.run/fal-ai/flux/schnell"
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Key test-fal-key"
    assert mock_post.call_args.kwargs["json"]["prompt"] == "a red bicycle"
