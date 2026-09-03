import io

import torch
from diffusers import StableDiffusionPipeline

from config.settings import settings

# width, height — kept at 512-ish and multiples of 8 to stay comfortable on a 4GB GPU.
_ASPECT_RATIO_DIMENSIONS = {
    "1:1": (512, 512),
    "4:5": (512, 640),
    "9:16": (512, 896),
    "16:9": (896, 512),
}


class LocalDiffusersGenerator:
    """Runs Stable Diffusion locally via the `diffusers` library. No external API/credits involved."""

    def __init__(self) -> None:
        self._pipe = None

    def _load_pipeline(self) -> StableDiffusionPipeline:
        if self._pipe is not None:
            return self._pipe

        pipe = StableDiffusionPipeline.from_pretrained(
            settings.local_image_model_id,
            dtype=torch.float16 if settings.media_device == "cuda" else torch.float32,
            safety_checker=None,
            token=settings.huggingface_token or None,
        )
        pipe = pipe.to(settings.media_device)
        pipe.enable_attention_slicing()
        pipe.vae.enable_slicing()
        self._pipe = pipe
        return pipe

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1", reference_image: bytes | None = None) -> bytes:
        # SD1.5 is text-to-image only — no image-conditioned generation, so reference_image is ignored.
        width, height = _ASPECT_RATIO_DIMENSIONS.get(aspect_ratio, _ASPECT_RATIO_DIMENSIONS["1:1"])
        pipe = self._load_pipeline()
        image = pipe(prompt=prompt, width=width, height=height, num_inference_steps=25).images[0]

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
