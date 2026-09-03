import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

_PERIOD_TO_TIMEDELTA = {"day": timedelta(days=1), "week": timedelta(days=7), "month": timedelta(days=30)}


class MastodonPublisher:
    platform = "mastodon"
    max_caption_length = 500  # Mastodon's default per-instance character limit.

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.mastodon_access_token}"}

    def _url(self, path: str) -> str:
        return f"{settings.mastodon_base_url.rstrip('/')}/{path.lstrip('/')}"

    @lru_cache(maxsize=1)
    def _account_id(self) -> str:
        response = requests.get(
            self._url("/api/v1/accounts/verify_credentials"), headers=self._headers(), timeout=30
        )
        response.raise_for_status()
        return response.json()["id"]

    def get_recent_posts(self, limit: int = 10) -> list[dict]:
        response = requests.get(
            self._url(f"/api/v1/accounts/{self._account_id()}/statuses"),
            params={"limit": limit},
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return [
            {
                "id": status["id"],
                "message": status.get("content", ""),
                "created_at": status.get("created_at"),
                "engagement": {
                    "likes": status.get("favourites_count"),
                    "comments": status.get("replies_count"),
                    "shares": status.get("reblogs_count"),
                },
                "impressions": None,  # Mastodon does not expose impressions/reach for regular accounts.
            }
            for status in response.json()
        ]

    def get_engagement_summary(self, period: str = "week") -> dict:
        posts = self.get_recent_posts(limit=40)
        cutoff = datetime.now(timezone.utc) - _PERIOD_TO_TIMEDELTA.get(period, timedelta(days=7))
        recent = [
            p for p in posts if p["created_at"] and datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) >= cutoff
        ]
        engaged_users = sum(
            (p["engagement"]["likes"] or 0) + (p["engagement"]["comments"] or 0) + (p["engagement"]["shares"] or 0)
            for p in recent
        )
        return {"impressions": None, "engaged_users": engaged_users, "period": period, "sample_size": len(recent)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _upload_media_bytes(self, media_bytes: bytes, content_type: str) -> str:
        response = requests.post(
            self._url("/api/v2/media"),
            headers=self._headers(),
            files={"file": ("media", media_bytes, content_type)},
            timeout=120,
        )
        response.raise_for_status()
        media = response.json()

        if response.status_code == 202 or media.get("url") is None:
            media = self._wait_for_media_processing(media["id"])
        return media["id"]

    def _upload_media_from_url(self, media_url: str, content_type: str) -> str:
        media_bytes = requests.get(media_url, timeout=60).content
        return self._upload_media_bytes(media_bytes, content_type)

    def _wait_for_media_processing(self, media_id: str, timeout_s: int = 120) -> dict:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            response = requests.get(self._url(f"/api/v1/media/{media_id}"), headers=self._headers(), timeout=30)
            response.raise_for_status()
            media = response.json()
            if media.get("url"):
                return media
            time.sleep(3)
        raise TimeoutError(f"Mastodon media {media_id} did not finish processing within {timeout_s}s")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _post_status(self, caption: str, media_id: str) -> dict:
        response = requests.post(
            self._url("/api/v1/statuses"),
            headers=self._headers(),
            data={"status": caption, "media_ids[]": media_id},
            timeout=30,
        )
        response.raise_for_status()
        raw = response.json()
        return {"post_id": raw["id"], "permalink": raw.get("url"), "raw": raw}

    def publish_image(self, image_bytes: bytes, caption: str, content_type: str = "image/png") -> dict:
        media_id = self._upload_media_bytes(image_bytes, content_type)
        return self._post_status(caption, media_id)

    def publish_video(self, video_url: str, caption: str) -> dict:
        media_id = self._upload_media_from_url(video_url, "video/mp4")
        return self._post_status(caption, media_id)
