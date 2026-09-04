import os

# Set required env vars before any test module imports config.settings (which reads them eagerly).
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("LEONARDO_API_KEY", "test-leonardo-key")
os.environ.setdefault("FAL_API_KEY", "test-fal-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("HIGGSFIELD_API_KEY_ID", "test-higgsfield-key-id")
os.environ.setdefault("HIGGSFIELD_API_KEY_SECRET", "test-higgsfield-key-secret")
os.environ.setdefault("ENABLED_PLATFORMS", "facebook")
os.environ.setdefault("FB_PAGE_ID", "123456")
os.environ.setdefault("FB_PAGE_ACCESS_TOKEN", "test-fb-token")
os.environ.setdefault("MASTODON_BASE_URL", "https://instance.example")
os.environ.setdefault("MASTODON_ACCESS_TOKEN", "test-mastodon-token")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
