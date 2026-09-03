from langchain_core.tools import tool

from integrations.social.registry import get_publisher


def _truncate_caption(caption: str, max_length: int) -> str:
    """Defensive safety net — the agent is instructed to respect platform limits, but LLM output
    can't be guaranteed to stay under a hard technical constraint like Mastodon's 500 chars."""
    if len(caption) <= max_length:
        return caption
    ellipsis = "…"
    budget = max_length - len(ellipsis)
    truncated = caption[:budget]
    # Prefer cutting at a word boundary so we don't chop a word (or hashtag) in half.
    last_space = truncated.rfind(" ")
    if last_space > budget * 0.5:  # back off to the space as long as we keep at least half the budget
        truncated = truncated[:last_space]
    return truncated.rstrip() + ellipsis


@tool
def get_recent_posts(platform: str, limit: int = 10) -> list[dict]:
    """Fetch recent posts + per-post engagement from a social platform ('facebook', 'mastodon', ...)."""
    return get_publisher(platform).get_recent_posts(limit)


@tool
def get_engagement_summary(platform: str, period: str = "week") -> dict:
    """Fetch an aggregate engagement/reach summary for a social platform over the given period."""
    return get_publisher(platform).get_engagement_summary(period)


@tool
def publish_image_post(platform: str, image_bytes: bytes, caption: str) -> dict:
    """Publish an image post (raw PNG bytes) with a caption to a social platform. Returns {post_id, permalink, caption}."""
    publisher = get_publisher(platform)
    final_caption = _truncate_caption(caption, publisher.max_caption_length)
    result = publisher.publish_image(image_bytes, final_caption)
    return {**result, "caption": final_caption}


@tool
def publish_video_post(platform: str, video_url: str, caption: str) -> dict:
    """Publish a video post with a caption to a social platform. Returns {post_id, permalink, caption}."""
    publisher = get_publisher(platform)
    final_caption = _truncate_caption(caption, publisher.max_caption_length)
    result = publisher.publish_video(video_url, final_caption)
    return {**result, "caption": final_caption}
