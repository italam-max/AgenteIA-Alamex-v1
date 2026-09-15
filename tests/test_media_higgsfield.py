from unittest.mock import MagicMock, patch

from integrations.media.higgsfield import HiggsfieldGenerator


def _mock_response(content=None):
    response = MagicMock()
    response.content = content
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media.higgsfield.download_bytes")
@patch("integrations.media.higgsfield.SyncClient")
def test_generate_image_downloads_returned_url(mock_sync_client_cls, mock_download_bytes):
    mock_client = MagicMock()
    mock_client.subscribe.return_value = {"images": [{"url": "https://higgsfield.ai/out.png"}]}
    mock_sync_client_cls.return_value = mock_client
    mock_download_bytes.return_value = b"fake-png-bytes"

    result = HiggsfieldGenerator().generate_image("a red bicycle", aspect_ratio="9:16")

    assert result == b"fake-png-bytes"
    assert mock_sync_client_cls.call_args.kwargs["api_key"] == "test-higgsfield-key-id:test-higgsfield-key-secret"
    assert mock_client.subscribe.call_args.args[0] == "higgsfield-ai/soul/v2/standard"
    assert mock_client.subscribe.call_args.kwargs["arguments"]["prompt"] == "a red bicycle"
    assert mock_client.subscribe.call_args.kwargs["arguments"]["aspect_ratio"] == "9:16"
    mock_download_bytes.assert_called_once_with("https://higgsfield.ai/out.png")


@patch("integrations.media.higgsfield.SyncClient")
def test_generate_image_maps_unsupported_aspect_ratio(mock_sync_client_cls):
    mock_client = MagicMock()
    mock_client.subscribe.return_value = {"images": [{"url": "https://higgsfield.ai/out.png"}]}
    mock_sync_client_cls.return_value = mock_client

    with patch("integrations.media.higgsfield.download_bytes", return_value=b"x"):
        HiggsfieldGenerator().generate_image("a red bicycle", aspect_ratio="4:5")

    assert mock_client.subscribe.call_args.kwargs["arguments"]["aspect_ratio"] == "3:4"
