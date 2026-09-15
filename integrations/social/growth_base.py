from typing import Protocol


class GrowthCapablePublisher(Protocol):
    """
    Extra capabilities needed for the autonomous growth mission (agents/growth_mission.py):
    reading follower stats, replying to mentions, and discovering/following relevant accounts.
    Not part of `SocialPublisher` since not every platform has this open discovery model
    (Facebook doesn't, and Instagram/TikTok/X don't expose a follow-account endpoint at all on
    their official APIs) — only `MastodonPublisher` implements this today, where following via
    API is both technically available and within the platform's own norms.
    """

    def get_account_stats(self) -> dict:
        """{"followers_count": int, "following_count": int, "statuses_count": int}."""
        ...

    def get_notifications(self, limit: int = 20) -> list[dict]:
        """Recent mentions to reply to. Each item: {status_id, account_id, text}."""
        ...

    def reply_to_status(self, status_id: str, text: str) -> dict:
        """{"post_id": str, "permalink": str | None, "raw": dict}."""
        ...

    def search_accounts_by_hashtag(self, hashtag: str, limit: int = 20) -> list[dict]:
        """Accounts posting under `hashtag`, excluding our own. Each item: {account_id, username}."""
        ...

    def follow_account(self, account_id: str) -> dict:
        """{"account_id": str, "raw": dict}."""
        ...
