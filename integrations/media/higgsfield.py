from higgsfield_client.http.client import SyncClient

from config.settings import settings
from integrations.media._common import DEFAULT_RETRY, download_bytes

# Higgsfield doesn't support 4:5 — map to the closest supported ratio.
_ASPECT_RATIO_MAP = {
    "1:1": "1:1",
    "4:5": "3:4",
    "9:16": "9:16",
    "16:9": "16:9",
}


class HiggsfieldGenerationFailed(Exception):
    pass


class HiggsfieldGenerator:
    """Generates images via Higgsfield AI's hosted Soul model (paid, async job API)."""

    def _client(self) -> SyncClient:
        # A fresh client built with our own api_key, instead of the package's module-level
        # singleton (which reads HF_KEY from the process env) — avoids mutating global env state,
        # which would be unsafe if another key/account were ever used concurrently.
        return SyncClient(api_key=f"{settings.higgsfield_api_key_id}:{settings.higgsfield_api_key_secret}")

    @DEFAULT_RETRY
    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        # Soul v2 standard is text-to-image only — reference_image is ignored.
        result = self._client().subscribe(
            settings.higgsfield_model_id,
            arguments={
                "prompt": prompt,
                "aspect_ratio": _ASPECT_RATIO_MAP.get(aspect_ratio, "1:1"),
                "resolution": "1080p",
            },
        )

        images = result.get("images") or []
        if not images:
            raise HiggsfieldGenerationFailed(f"Higgsfield returned no images: {result}")

        return download_bytes(images[0]["url"])
