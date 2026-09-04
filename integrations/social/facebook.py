import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

_BASE = "https://graph.facebook.com"


class FacebookPublisher:
    platform = "facebook"
    max_caption_length = 63206  # Facebook's post text limit — effectively no practical constraint.

    def _url(self, path: str) -> str:
        return f"{_BASE}/{settings.fb_graph_api_version}/{path.lstrip('/')}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _get(self, path: str, params: dict | None = None) -> dict:
        params = {**(params or {}), "access_token": settings.fb_page_access_token}
        response = requests.get(self._url(path), params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _post(self, path: str, data: dict) -> dict:
        data = {**data, "access_token": settings.fb_page_access_token}
        response = requests.post(self._url(path), data=data, timeout=60)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _post_multipart(self, path: str, data: dict, file_bytes: bytes, content_type: str) -> dict:
        data = {**data, "access_token": settings.fb_page_access_token}
        response = requests.post(
            self._url(path), data=data, files={"source": ("media", file_bytes, content_type)}, timeout=120
        )
        response.raise_for_status()
        return response.json()

    def get_recent_posts(self, limit: int = 10) -> list[dict]:
        fields = "message,created_time,attachments,insights.metric(post_impressions,post_engaged_users)"
        raw_posts = self._get(f"{settings.fb_page_id}/posts", {"fields": fields, "limit": limit}).get("data", [])

        normalized = []
        for post in raw_posts:
            insight_values = {
                metric["name"]: metric["values"][0]["value"]
                for metric in (post.get("insights", {}).get("data") or [])
            }
            normalized.append(
                {
                    "id": post.get("id"),
                    "message": post.get("message", ""),
                    "created_at": post.get("created_time"),
                    "engagement": {
                        "likes": None,
                        "comments": None,
                        "shares": insight_values.get("post_engaged_users"),
                    },
                    "impressions": insight_values.get("post_impressions"),
                }
            )
        return normalized

    def get_engagement_summary(self, period: str = "week") -> dict:
        metric = "page_impressions,page_engaged_users,page_fans"
        result = self._get(f"{settings.fb_page_id}/insights", {"metric": metric, "period": period})
        values = {row["name"]: row["values"][-1]["value"] for row in result.get("data", [])}
        return {
            "impressions": values.get("page_impressions"),
            "engaged_users": values.get("page_engaged_users"),
            "period": period,
            "sample_size": None,
        }

    def publish_image(
        self, image_bytes: bytes, caption: str, content_type: str = "image/png", alt_text: str | None = None
    ) -> dict:
        data = {"caption": caption}
        if alt_text:
            data["alt_text_custom"] = alt_text
        raw = self._post_multipart(f"{settings.fb_page_id}/photos", data, image_bytes, content_type)
        return {"post_id": raw.get("post_id") or raw.get("id"), "permalink": None, "raw": raw}

    def publish_video(self, video_url: str, caption: str) -> dict:
        raw = self._post(f"{settings.fb_page_id}/videos", {"file_url": video_url, "description": caption})
        return {"post_id": raw.get("post_id") or raw.get("id"), "permalink": None, "raw": raw}
