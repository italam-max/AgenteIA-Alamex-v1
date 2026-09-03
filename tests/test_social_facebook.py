from unittest.mock import MagicMock, patch

from integrations.social.facebook import FacebookPublisher


def _mock_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


@patch("integrations.social.facebook.requests.get")
def test_get_recent_posts_normalizes_shape(mock_get):
    mock_get.return_value = _mock_response(
        {
            "data": [
                {
                    "id": "1",
                    "message": "hi",
                    "created_time": "2026-08-01T00:00:00+0000",
                    "insights": {"data": [{"name": "post_impressions", "values": [{"value": 42}]}]},
                }
            ]
        }
    )

    posts = FacebookPublisher().get_recent_posts(limit=5)

    assert posts == [
        {
            "id": "1",
            "message": "hi",
            "created_at": "2026-08-01T00:00:00+0000",
            "engagement": {"likes": None, "comments": None, "shares": None},
            "impressions": 42,
        }
    ]
    called_url = mock_get.call_args.args[0]
    assert "posts" in called_url
    assert mock_get.call_args.kwargs["params"]["limit"] == 5
    assert mock_get.call_args.kwargs["params"]["access_token"] == "test-fb-token"


@patch("integrations.social.facebook.requests.post")
def test_publish_image_uploads_bytes_and_normalizes_result(mock_post):
    mock_post.return_value = _mock_response({"id": "789", "post_id": "123456_789"})

    result = FacebookPublisher().publish_image(b"fake-png-bytes", "Hello world")

    assert result["post_id"] == "123456_789"
    sent_data = mock_post.call_args.kwargs["data"]
    assert sent_data["caption"] == "Hello world"
    sent_files = mock_post.call_args.kwargs["files"]
    assert sent_files["source"][1] == b"fake-png-bytes"
