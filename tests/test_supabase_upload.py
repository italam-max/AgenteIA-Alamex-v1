from unittest.mock import MagicMock, patch

from integrations.supabase_client import upload_public_image


@patch("integrations.supabase_client.get_client")
def test_upload_public_image_uploads_and_returns_public_url(mock_get_client):
    mock_bucket = MagicMock()
    mock_bucket.get_public_url.return_value = "https://example.supabase.co/storage/v1/object/public/post-media/x.png"
    mock_get_client.return_value.storage.from_.return_value = mock_bucket

    url = upload_public_image(b"fake-png-bytes", content_type="image/png")

    assert url == "https://example.supabase.co/storage/v1/object/public/post-media/x.png"
    upload_call = mock_bucket.upload.call_args
    assert upload_call.args[1] == b"fake-png-bytes"
    assert upload_call.args[2] == {"content-type": "image/png"}
    assert upload_call.args[0].endswith(".png")
