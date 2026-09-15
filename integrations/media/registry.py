from functools import lru_cache

from integrations.media.base import MediaGenerator, VideoGenerator
from integrations.media.fal import FalGenerator
from integrations.media.gemini import GeminiGenerator
from integrations.media.gemini_video import GeminiVideoGenerator
from integrations.media.higgsfield import HiggsfieldGenerator
from integrations.media.leonardo import LeonardoGenerator
from integrations.media.local_diffusers import LocalDiffusersGenerator
from integrations.media.openai import OpenAIGenerator
from integrations.media.siliconflow_video import SiliconFlowVideoGenerator

_ADAPTERS: dict[str, type] = {
    "local": LocalDiffusersGenerator,
    "leonardo": LeonardoGenerator,
    "fal": FalGenerator,
    "gemini": GeminiGenerator,
    "higgsfield": HiggsfieldGenerator,
    "openai": OpenAIGenerator,
}

_VIDEO_ADAPTERS: dict[str, type] = {
    "siliconflow": SiliconFlowVideoGenerator,
    "gemini": GeminiVideoGenerator,
}


@lru_cache(maxsize=None)
def get_generator(name: str) -> MediaGenerator:
    if name not in _ADAPTERS:
        raise ValueError(f"Unknown media generator '{name}'. Available: {list(_ADAPTERS)}")
    return _ADAPTERS[name]()


@lru_cache(maxsize=None)
def get_video_generator(name: str) -> VideoGenerator:
    if name not in _VIDEO_ADAPTERS:
        raise ValueError(f"Unknown video generator '{name}'. Available: {list(_VIDEO_ADAPTERS)}")
    return _VIDEO_ADAPTERS[name]()
