from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Which SocialPublisher adapters (integrations/social/registry.py) this run targets.
_REQUIRED_FIELDS_BY_PLATFORM = {
    "facebook": ["fb_page_id", "fb_page_access_token"],
    "mastodon": ["mastodon_base_url", "mastodon_access_token"],
}

# Which MediaGenerator adapter (integrations/media/registry.py) needs which credentials.
_REQUIRED_FIELDS_BY_MEDIA_GENERATOR = {
    "local": [],
    "leonardo": ["leonardo_api_key"],
    "fal": ["fal_api_key"],
    "gemini": ["gemini_api_key"],
    "higgsfield": ["higgsfield_api_key_id", "higgsfield_api_key_secret"],
    "openai": ["openai_api_key"],
}

# Which video generator adapter (integrations/media/registry.py) needs which credentials.
_REQUIRED_FIELDS_BY_VIDEO_GENERATOR = {
    "gemini": ["gemini_api_key"],
    "siliconflow": ["siliconflow_api_key"],
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str

    # Image generation: self-hosted (no per-image API credits). See integrations/media/registry.py.
    media_generator: str = "local"
    local_image_model_id: str = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    media_device: str = "cuda"
    huggingface_token: str | None = None

    # Leonardo.ai (integrations/media/leonardo.py) — Phoenix 1.0 by default.
    leonardo_api_key: str | None = None
    leonardo_model_id: str = "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3"

    # fal.ai (integrations/media/fal.py) — FLUX.1 [schnell].
    fal_api_key: str | None = None

    # Gemini (integrations/media/gemini.py) — supports a reference image (e.g. the brand logo).
    gemini_api_key: str | None = None
    gemini_image_model_id: str = "gemini-2.5-flash-image"

    # Higgsfield AI (integrations/media/higgsfield.py) — "Soul" model, paid hosted API.
    higgsfield_api_key_id: str | None = None
    higgsfield_api_key_secret: str | None = None
    higgsfield_model_id: str = "higgsfield-ai/soul/v2/standard"

    # OpenAI (integrations/media/openai.py) — gpt-image-2, paid hosted API. Supports a reference
    # image (e.g. the real brand logo) like Gemini does. gpt-image-1 (the previous default) is
    # being retired by OpenAI on 2026-10-23 — gpt-image-2 is the official replacement, same
    # endpoints, ~20-25% cheaper per token.
    openai_api_key: str | None = None
    openai_image_model_id: str = "gpt-image-2"

    # Which video generator to use: siliconflow, gemini. See integrations/media/registry.py.
    video_generator: str = "siliconflow"

    # SiliconFlow (integrations/media/siliconflow_video.py) — hosts Wan2.2 text-to-video, cheap.
    siliconflow_api_key: str | None = None
    siliconflow_video_model_id: str = "Wan-AI/Wan2.2-T2V-A14B"

    # Google Veo via the Gemini API (integrations/media/gemini_video.py) — reuses GEMINI_API_KEY.
    gemini_video_model_id: str = "veo-3.1-fast-generate-preview"

    # Higgsfield video (integrations/media/higgsfield_video.py) — kept for a possible future DoP
    # (image-to-video, needs a starting image) pipeline. NOT wired into tools/media_tools.py: this
    # account's plan only has Higgsfield's own Soul/DoP/Popcorn models, not the third-party
    # text-to-video ones (Kling/Seedance/Veo/Sora) advertised in their public docs/site.
    higgsfield_video_model_id: str | None = None

    # OpenAI text-to-speech (integrations/media/openai_tts.py) — narration voiceover for video
    # posts, muxed onto the Higgsfield clip.
    openai_tts_model_id: str = "tts-1"
    openai_tts_voice: str = "alloy"

    enabled_platforms_raw: str = Field(default="facebook", validation_alias="ENABLED_PLATFORMS")

    fb_graph_api_version: str = "v21.0"
    fb_page_id: str | None = None
    fb_page_access_token: str | None = None

    mastodon_base_url: str | None = None
    mastodon_access_token: str | None = None

    # Growth mission (run_growth_mission.py) — Mastodon-only, autonomous organic-growth
    # experiment: posts, replies to our own audience, and follows genuinely relevant accounts
    # discovered by hashtag. Caps exist specifically to reduce the risk of the account being
    # flagged as spam/bot — start conservative, raise only if the account stays healthy.
    growth_target_followers: int = 100
    growth_tick_minutes: int = 60
    growth_max_follows_per_tick: int = 5
    growth_max_replies_per_tick: int = 5
    growth_hashtags_raw: str = Field(default="", validation_alias="GROWTH_HASHTAGS")

    supabase_url: str
    supabase_service_role_key: str

    @property
    def enabled_platforms(self) -> list[str]:
        return [p.strip() for p in self.enabled_platforms_raw.split(",") if p.strip()]

    @property
    def growth_hashtags(self) -> list[str]:
        return [h.strip().lstrip("#") for h in self.growth_hashtags_raw.split(",") if h.strip()]

    def _check_has_credentials(self, label: str, value: str, required_fields_by_value: dict[str, list[str]]) -> None:
        required = required_fields_by_value.get(value)
        if required is None:
            raise ValueError(f"Unknown {label} '{value}'. Known: {list(required_fields_by_value)}")
        missing = [field for field in required if not getattr(self, field)]
        if missing:
            raise ValueError(f"{label} '{value}' is set but missing env vars: {missing}")

    @model_validator(mode="after")
    def _check_enabled_platforms_have_credentials(self) -> "Settings":
        for platform in self.enabled_platforms:
            self._check_has_credentials("platform (in ENABLED_PLATFORMS)", platform, _REQUIRED_FIELDS_BY_PLATFORM)
        return self

    @model_validator(mode="after")
    def _check_media_generator_has_credentials(self) -> "Settings":
        self._check_has_credentials("MEDIA_GENERATOR", self.media_generator, _REQUIRED_FIELDS_BY_MEDIA_GENERATOR)
        return self

    @model_validator(mode="after")
    def _check_video_generator_has_credentials(self) -> "Settings":
        self._check_has_credentials("VIDEO_GENERATOR", self.video_generator, _REQUIRED_FIELDS_BY_VIDEO_GENERATOR)
        return self


# Fails fast at import time if a required var is missing, instead of failing deep inside a node.
settings = Settings()
