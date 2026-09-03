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
