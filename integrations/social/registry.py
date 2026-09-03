from functools import lru_cache

from integrations.social.base import SocialPublisher
from integrations.social.facebook import FacebookPublisher
from integrations.social.mastodon import MastodonPublisher

_ADAPTERS: dict[str, type] = {
    "facebook": FacebookPublisher,
    "mastodon": MastodonPublisher,
}


@lru_cache(maxsize=None)
def get_publisher(platform: str) -> SocialPublisher:
    if platform not in _ADAPTERS:
        raise ValueError(f"Unknown platform '{platform}'. Available: {list(_ADAPTERS)}")
    return _ADAPTERS[platform]()
