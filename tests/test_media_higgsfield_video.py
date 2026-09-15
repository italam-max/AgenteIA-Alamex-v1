from unittest.mock import MagicMock, patch

import pytest

from config.settings import settings
from integrations.media.higgsfield_video import HiggsfieldVideoGenerationFailed, HiggsfieldVideoGenerator


@patch("integrations.media.higgsfield_video.download_bytes")
@patch("integrations.media.higgsfield_video.SyncClient")
def test_generate_video_downloads_returned_url(mock_sync_client_cls, mock_download_bytes):
    mock_client = MagicMock()
    mock_client.subscribe.return_value = {"videos": [{"url": "https://higgsfield.ai/out.mp4"}]}
    mock_sync_client_cls.return_value = mock_client
    mock_download_bytes.return_value = b"fake-mp4-bytes"

    result = HiggsfieldVideoGenerator().generate_video("a red bicycle riding by", aspect_ratio="9:16")

    assert result == b"fake-mp4-bytes"
    assert mock_sync_client_cls.call_args.kwargs["api_key"] == "test-higgsfield-key-id:test-higgsfield-key-secret"
    assert mock_client.subscribe.call_args.args[0] == "test-higgsfield-video-model"
    assert mock_client.subscribe.call_args.kwargs["arguments"]["prompt"] == "a red bicycle riding by"
    assert mock_client.subscribe.call_args.kwargs["arguments"]["aspect_ratio"] == "9:16"
    mock_download_bytes.assert_called_once_with("https://higgsfield.ai/out.mp4", timeout=120)


@patch("integrations.media.higgsfield_video.SyncClient")
def test_generate_video_maps_unsupported_aspect_ratio(mock_sync_client_cls):
    mock_client = MagicMock()
    mock_client.subscribe.return_value = {"videos": [{"url": "https://higgsfield.ai/out.mp4"}]}
    mock_sync_client_cls.return_value = mock_client

    with patch("integrations.media.higgsfield_video.download_bytes", return_value=b"x"):
        HiggsfieldVideoGenerator().generate_video("a red bicycle", aspect_ratio="4:5")

    assert mock_client.subscribe.call_args.kwargs["arguments"]["aspect_ratio"] == "3:4"


def test_generate_video_fails_clearly_without_model_id(monkeypatch):
    monkeypatch.setattr(settings, "higgsfield_video_model_id", None)

    with pytest.raises(HiggsfieldVideoGenerationFailed):
        HiggsfieldVideoGenerator().generate_video("a red bicycle")


@patch("integrations.media.higgsfield_video.download_bytes")
@patch("integrations.media.higgsfield_video.SyncClient")
def test_generate_video_accepts_singular_video_object_shape(mock_sync_client_cls, mock_download_bytes):
    mock_client = MagicMock()
    mock_client.subscribe.return_value = {"video": {"url": "https://higgsfield.ai/out.mp4"}}
    mock_sync_client_cls.return_value = mock_client
    mock_download_bytes.return_value = b"fake-mp4-bytes"

    result = HiggsfieldVideoGenerator().generate_video("a red bicycle")

    assert result == b"fake-mp4-bytes"


@patch("integrations.media.higgsfield_video.SyncClient")
def test_generate_video_raises_when_no_video_returned(mock_sync_client_cls):
    mock_client = MagicMock()
    mock_client.subscribe.return_value = {"videos": []}
    mock_sync_client_cls.return_value = mock_client

    with pytest.raises(HiggsfieldVideoGenerationFailed):
        HiggsfieldVideoGenerator().generate_video("a red bicycle")
