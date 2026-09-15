from typing import Protocol


class MediaGenerator(Protocol):
    """
    Common contract for image/video generation backends, mirroring integrations/social/base.py.
    Add a new backend (a paid API, a different local model) by writing one class that satisfies
    this contract and registering it in integrations/media/registry.py.
    """

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        """
        Returns PNG image bytes. `reference_image` (e.g. the real brand logo) is used to compose
        it into the result on backends that support image-conditioned generation (Gemini); other
        backends ignore it and fall back to text-only generation.
        """
        ...


class VideoGenerator(Protocol):
    """
    Common contract for silent b-roll video backends. Add one by writing a class that satisfies
    this contract and registering it in integrations/media/registry.py's `_VIDEO_ADAPTERS`.
    """

    def generate_video(self, prompt: str, aspect_ratio: str = "9:16") -> bytes:
        """Returns mp4 bytes for a short silent clip. `prompt` describes the visual scene only."""
        ...
