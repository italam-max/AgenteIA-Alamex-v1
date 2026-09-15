from higgsfield_client.http.client import SyncClient

from config.settings import settings
from integrations.media._common import DEFAULT_RETRY, download_bytes

# Confirmed against Higgsfield's live OpenAPI spec (docs.higgsfield.ai/docs/openapi.json) for
# bytedance/seedance text-to-video endpoints, which take these exact literal values. NOTE: Kling
# text-to-video endpoints (kling-video/*/text-to-video) do NOT accept aspect_ratio at all — don't
# point HIGGSFIELD_VIDEO_MODEL_ID at one of those if vertical video matters.
_ASPECT_RATIO_MAP = {
    "1:1": "1:1",
    "4:5": "3:4",
    "9:16": "9:16",
    "16:9": "16:9",
}


class HiggsfieldVideoGenerationFailed(Exception):
    pass


def _extract_video_url(result: dict) -> str | None:
    """
    Higgsfield's video job result shape isn't confirmed identical to the image job's
    (`{"images": [...]}`) — some docs show a singular `{"video": {"url": ...}}` instead of a
    `{"videos": [...]}` array. Accept either so a real response tells us which one is actually
    used instead of a wrong guess silently failing every call.
    """
    videos = result.get("videos")
    if videos:
        return videos[0].get("url")
    video = result.get("video")
    if isinstance(video, dict):
        return video.get("url")
    return None


class HiggsfieldVideoGenerator:
    """
    Generates a short silent b-roll clip via Higgsfield's hosted video model (paid, async job
    API) — same `subscribe(model_id, arguments=...)` job client as the image generator in
    integrations/media/higgsfield.py, just a different model_id. HIGGSFIELD_VIDEO_MODEL_ID has no
    safe default (unlike the image Soul model) since it's opt-in per README/settings.py.
    """

    def _client(self) -> SyncClient:
        # A fresh client built with our own api_key, instead of the package's module-level
        # singleton (which reads HF_KEY from the process env) — avoids mutating global env state,
        # which would be unsafe if another key/account were ever used concurrently.
        return SyncClient(api_key=f"{settings.higgsfield_api_key_id}:{settings.higgsfield_api_key_secret}")

    @DEFAULT_RETRY
    def generate_video(self, prompt: str, aspect_ratio: str = "9:16") -> bytes:
        if not settings.higgsfield_video_model_id:
            raise HiggsfieldVideoGenerationFailed(
                "HIGGSFIELD_VIDEO_MODEL_ID no está configurado en .env — necesario para generar video."
            )

        result = self._client().subscribe(
            settings.higgsfield_video_model_id,
            arguments={
                "prompt": prompt,
                "aspect_ratio": _ASPECT_RATIO_MAP.get(aspect_ratio, "9:16"),
            },
        )

        video_url = _extract_video_url(result)
        if not video_url:
            raise HiggsfieldVideoGenerationFailed(f"Higgsfield returned no video: {result}")

        return download_bytes(video_url, timeout=120)
