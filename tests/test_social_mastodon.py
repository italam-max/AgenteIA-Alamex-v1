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


@patch("integrations.social.mastodon.requests.get")
def test_get_account_stats_returns_follower_counts(mock_get):
    mock_get.side_effect = [
        _mock_response({"id": "self-1"}),
        _mock_response({"followers_count": 42, "following_count": 10, "statuses_count": 5}),
    ]

    result = MastodonPublisher().get_account_stats()

    assert result == {"followers_count": 42, "following_count": 10, "statuses_count": 5}
    assert mock_get.call_args_list[1].args[0].endswith("/api/v1/accounts/self-1")


@patch("integrations.social.mastodon.requests.get")
def test_get_notifications_extracts_status_and_account(mock_get):
    mock_get.return_value = _mock_response(
        [
            {"status": {"id": "status-1"}, "account": {"id": "acct-1"}},
            {"type": "follow", "account": {"id": "acct-2"}},  # no status — e.g. a follow notification, ignored
        ]
    )

    result = MastodonPublisher().get_notifications()

    assert result == [{"status_id": "status-1", "account_id": "acct-1", "text": ""}]


@patch("integrations.social.mastodon.requests.post")
def test_reply_to_status_sets_in_reply_to_id(mock_post):
    mock_post.return_value = _mock_response({"id": "status-2", "url": "https://instance/@user/status-2"})

    result = MastodonPublisher().reply_to_status("status-1", "Gracias por tu comentario!")

    assert result == {
        "post_id": "status-2",
        "permalink": "https://instance/@user/status-2",
        "raw": {"id": "status-2", "url": "https://instance/@user/status-2"},
    }
    assert mock_post.call_args.kwargs["data"] == {"status": "Gracias por tu comentario!", "in_reply_to_id": "status-1"}


@patch("integrations.social.mastodon.requests.get")
def test_search_accounts_by_hashtag_dedupes_and_excludes_self(mock_get):
    mock_get.side_effect = [
        _mock_response(
            [
                {"account": {"id": "acct-1", "username": "alice"}},
                {"account": {"id": "acct-1", "username": "alice"}},
                {"account": {"id": "self-1", "username": "us"}},
            ]
        ),
        _mock_response({"id": "self-1"}),
    ]

    result = MastodonPublisher().search_accounts_by_hashtag("industria")

    assert result == [{"account_id": "acct-1", "username": "alice"}]
    assert mock_get.call_args_list[0].args[0].endswith("/api/v1/timelines/tag/industria")


@patch("integrations.social.mastodon.requests.post")
def test_follow_account_posts_to_follow_endpoint(mock_post):
    mock_post.return_value = _mock_response({"following": True})

    result = MastodonPublisher().follow_account("acct-1")

    assert result == {"account_id": "acct-1", "raw": {"following": True}}
    assert mock_post.call_args.args[0].endswith("/api/v1/accounts/acct-1/follow")
