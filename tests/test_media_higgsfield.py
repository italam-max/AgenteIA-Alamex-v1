import os
from unittest.mock import MagicMock, patch

from integrations.media.higgsfield import HiggsfieldGenerator


def _mock_response(content=None):
    response = MagicMock()
    response.content = content
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media.higgsfield.requests.get")
@patch("integrations.media.higgsfield.subscribe")
def test_generate_image_downloads_returned_url(mock_subscribe, mock_get):
    mock_subscribe.return_value = {"images": [{"url": "https://higgsfield.ai/out.png"}]}
    mock_get.return_value = _mock_response(content=b"fake-png-bytes")

    result = HiggsfieldGenerator().generate_image("a red bicycle", aspect_ratio="9:16")

    assert result == b"fake-png-bytes"
    assert mock_subscribe.call_args.args[0] == "higgsfield-ai/soul/v2/standard"
    assert mock_subscribe.call_args.kwargs["arguments"]["prompt"] == "a red bicycle"
    assert mock_subscribe.call_args.kwargs["arguments"]["aspect_ratio"] == "9:16"
    assert os.environ["HF_KEY"] == "test-higgsfield-key-id:test-higgsfield-key-secret"


@patch("integrations.media.higgsfield.subscribe")
def test_generate_image_maps_unsupported_aspect_ratio(mock_subscribe):
    mock_subscribe.return_value = {"images": [{"url": "https://higgsfield.ai/out.png"}]}
    with patch("integrations.media.higgsfield.requests.get", return_value=_mock_response(content=b"x")):
        HiggsfieldGenerator().generate_image("a red bicycle", aspect_ratio="4:5")

    assert mock_subscribe.call_args.kwargs["arguments"]["aspect_ratio"] == "3:4"
