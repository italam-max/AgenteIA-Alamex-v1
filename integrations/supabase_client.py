import uuid
from functools import lru_cache

from supabase import Client, create_client

from config.settings import settings

_MEDIA_BUCKET = "post-media"


@lru_cache(maxsize=1)
def get_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def upload_public_image(image_bytes: bytes, content_type: str = "image/png") -> str:
    """Uploads to the public post-media bucket and returns the public URL — lets the dashboard show a thumbnail."""
    extension = content_type.split("/")[-1]
    path = f"{uuid.uuid4()}.{extension}"
    get_client().storage.from_(_MEDIA_BUCKET).upload(path, image_bytes, {"content-type": content_type})
    return get_client().storage.from_(_MEDIA_BUCKET).get_public_url(path)
