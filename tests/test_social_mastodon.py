from unittest.mock import MagicMock, patch

from integrations.social.mastodon import MastodonPublisher


def _mock_response(json_data, status_code=200):
    response = MagicMock()
    response.json.return_value = json_data
    response.status_code = status_code
    response.raise_for_status.return_value = None
    return response


@patch("integrations.social.mastodon.requests.post")
def test_publish_image_uploads_media_then_posts_status(mock_post):
    upload_response = _mock_response({"id": "media-1", "url": "https://instance/media/1"}, status_code=200)
    status_response = _mock_response({"id": "status-1", "url": "https://instance/@user/status-1"}, status_code=200)
    mock_post.side_effect = [upload_response, status_response]

    result = MastodonPublisher().publish_image(b"fake-image-bytes", "Hello Mastodon", alt_text="A red bicycle")

    assert result == {
        "post_id": "status-1",
        "permalink": "https://instance/@user/status-1",
        "raw": {"id": "status-1", "url": "https://instance/@user/status-1"},
    }

    upload_call = mock_post.call_args_list[0]
    assert upload_call.args[0].endswith("/api/v2/media")
    assert upload_call.kwargs["headers"]["Authorization"] == "Bearer test-mastodon-token"
    assert upload_call.kwargs["data"] == {"description": "A red bicycle"}

    status_call = mock_post.call_args_list[1]
    assert status_call.kwargs["data"]["status"] == "Hello Mastodon"
    assert status_call.kwargs["data"]["media_ids[]"] == "media-1"
