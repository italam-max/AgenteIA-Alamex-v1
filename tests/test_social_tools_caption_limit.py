from unittest.mock import MagicMock, patch

from tools.social_tools import publish_image_post


@patch("tools.social_tools.get_publisher")
def test_publish_image_post_truncates_caption_over_platform_limit(mock_get_publisher):
    mock_publisher = MagicMock()
    mock_publisher.max_caption_length = 10
    mock_publisher.publish_image.return_value = {"post_id": "1", "permalink": None, "raw": {}}
    mock_get_publisher.return_value = mock_publisher

    result = publish_image_post.invoke({"platform": "mastodon", "image_bytes": b"x", "caption": "0123456789ABCDEF"})

    sent_caption = mock_publisher.publish_image.call_args.args[1]
    assert sent_caption == "012345678…"
    assert len(sent_caption) == 10
    assert result["caption"] == sent_caption  # the actually-published text, not the pre-truncation draft


@patch("tools.social_tools.get_publisher")
def test_publish_image_post_truncates_at_word_boundary(mock_get_publisher):
    mock_publisher = MagicMock()
    mock_publisher.max_caption_length = 20
    mock_publisher.publish_image.return_value = {"post_id": "1", "permalink": None, "raw": {}}
    mock_get_publisher.return_value = mock_publisher

    publish_image_post.invoke({"platform": "mastodon", "image_bytes": b"x", "caption": "hello wonderful world today"})

    sent_caption = mock_publisher.publish_image.call_args.args[1]
    assert sent_caption == "hello wonderful…"
    assert len(sent_caption) <= 20


@patch("tools.social_tools.get_publisher")
def test_publish_image_post_leaves_caption_under_limit_untouched(mock_get_publisher):
    mock_publisher = MagicMock()
    mock_publisher.max_caption_length = 500
    mock_publisher.publish_image.return_value = {"post_id": "1", "permalink": None, "raw": {}}
    mock_get_publisher.return_value = mock_publisher

    publish_image_post.invoke({"platform": "facebook", "image_bytes": b"x", "caption": "short caption"})

    sent_caption = mock_publisher.publish_image.call_args.args[1]
    assert sent_caption == "short caption"
