from typing import Protocol


class SocialPublisher(Protocol):
    """
    Common contract every platform adapter implements, so agents/tools call one API
    regardless of which network is behind it. Add a new network by writing one class
    that satisfies this contract and registering it in integrations/social/registry.py
    — nothing above this layer needs to change.
    """

    max_caption_length: int
    """Hard character limit this platform enforces on post text — used to truncate defensively."""

    def get_recent_posts(self, limit: int = 10) -> list[dict]:
        """Each item: {id, message, created_at, engagement: {likes, comments, shares}, impressions}."""
        ...

    def get_engagement_summary(self, period: str = "week") -> dict:
        """{"impressions": int | None, "engaged_users": int | None, "period": str, "sample_size": int}."""
        ...

    def publish_image(
        self, image_bytes: bytes, caption: str, content_type: str = "image/png", alt_text: str | None = None
    ) -> dict:
        """{"post_id": str, "permalink": str | None, "raw": dict}. `alt_text` is an accessibility
        description of the image, shown to screen readers — platforms that don't support it ignore it."""
        ...

    def publish_video(self, video_url: str, caption: str) -> dict:
        """{"post_id": str, "permalink": str | None, "raw": dict}."""
        ...
