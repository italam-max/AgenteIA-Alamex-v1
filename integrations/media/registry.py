from functools import lru_cache

from integrations.media.base import MediaGenerator
from integrations.media.fal import FalGenerator
from integrations.media.gemini import GeminiGenerator
from integrations.media.higgsfield import HiggsfieldGenerator
from integrations.media.leonardo import LeonardoGenerator
from integrations.media.local_diffusers import LocalDiffusersGenerator

_ADAPTERS: dict[str, type] = {
    "local": LocalDiffusersGenerator,
    "leonardo": LeonardoGenerator,
    "fal": FalGenerator,
    "gemini": GeminiGenerator,
    "higgsfield": HiggsfieldGenerator,
}


@lru_cache(maxsize=None)
def get_generator(name: str) -> MediaGenerator:
    if name not in _ADAPTERS:
        raise ValueError(f"Unknown media generator '{name}'. Available: {list(_ADAPTERS)}")
    return _ADAPTERS[name]()
