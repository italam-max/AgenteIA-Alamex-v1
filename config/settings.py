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

    enabled_platforms_raw: str = Field(default="facebook", validation_alias="ENABLED_PLATFORMS")

    fb_graph_api_version: str = "v21.0"
    fb_page_id: str | None = None
    fb_page_access_token: str | None = None

    mastodon_base_url: str | None = None
    mastodon_access_token: str | None = None

    supabase_url: str
    supabase_service_role_key: str

    @property
    def enabled_platforms(self) -> list[str]:
        return [p.strip() for p in self.enabled_platforms_raw.split(",") if p.strip()]

    @model_validator(mode="after")
    def _check_enabled_platforms_have_credentials(self) -> "Settings":
        for platform in self.enabled_platforms:
            required = _REQUIRED_FIELDS_BY_PLATFORM.get(platform)
            if required is None:
                raise ValueError(f"Unknown platform '{platform}' in ENABLED_PLATFORMS. Known: {list(_REQUIRED_FIELDS_BY_PLATFORM)}")
            missing = [field for field in required if not getattr(self, field)]
            if missing:
                raise ValueError(f"Platform '{platform}' is enabled but missing env vars: {missing}")
        return self

    @model_validator(mode="after")
    def _check_media_generator_has_credentials(self) -> "Settings":
        required = _REQUIRED_FIELDS_BY_MEDIA_GENERATOR.get(self.media_generator)
        if required is None:
            raise ValueError(f"Unknown MEDIA_GENERATOR '{self.media_generator}'. Known: {list(_REQUIRED_FIELDS_BY_MEDIA_GENERATOR)}")
        missing = [field for field in required if not getattr(self, field)]
        if missing:
            raise ValueError(f"MEDIA_GENERATOR '{self.media_generator}' is set but missing env vars: {missing}")
        return self


# Fails fast at import time if a required var is missing, instead of failing deep inside a node.
settings = Settings()
