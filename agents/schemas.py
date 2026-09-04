from typing import Literal

from pydantic import BaseModel, Field


class PlannedPost(BaseModel):
    type: Literal["image"] = Field(description="Only 'image' is supported for now — video generation is not wired up yet.")
    theme: str
    brief: str = Field(description="Short creative brief for this post, used to prompt image generation and copy.")


class WeeklyStrategy(BaseModel):
    themes: list[str]
    num_posts: int
    content_mix: dict[str, int] = Field(description='e.g. {"image": 4} — image only for now.')
    rationale: str = Field(description="Concise explanation of why this direction was chosen, referencing the input metrics.")
    planned_posts: list[PlannedPost]


class PostContent(BaseModel):
    caption: str = Field(description="Ready-to-publish social media caption, on-brand and in the page's language.")
    layout: Literal["infografia", "premium", "hero"] = Field(
        default="infografia",
        description=(
            "Visual style of the graphic. 'infografia': white panel with headline + bullets next to the "
            "photo — dense in data, the default. 'premium': dark navy/gold background, one bold headline, "
            "no bullets, photo fills most of the frame — for a single striking idea (a component, a "
            "flagship feature). 'hero': full-bleed photo with the headline overlaid at the bottom, no "
            "panel — for short punchy statements. Vary this across posts in the same run instead of "
            "always picking the same one — repeating the identical layout every week is what makes "
            "content feel templated and kills engagement."
        ),
    )
    reference_photo: str | None = Field(
        default=None,
        description=(
            "Exact filename from the real product photos list (if one clearly matches this post's theme) "
            "to use as the actual photo instead of generating one with AI — more authentic, and it's a "
            "real photo of a real product. Null if none of the available photos fit; a generated photo "
            "will be used instead via `media_prompt`."
        ),
    )
    media_prompt: str = Field(
        description=(
            "Prompt for the background photo only (scene, composition, materials, lighting, brand colors), "
            "used only when `reference_photo` is null. Never describe text, headlines, panels, or data "
            "here — that's drawn separately from `headline`/`bullets`."
        )
    )
    headline: str = Field(
        description=(
            "Short bold title (ideally under 45 characters) drawn as real text on the graphic — written "
            "exactly as it should appear (capitalization as you intend, it will be uppercased automatically)."
        )
    )
    bullets: list[str] = Field(
        default_factory=list,
        description=(
            "0-4 short factual data points drawn as a bulleted list next to the photo (e.g. real specs from "
            "the equipment catalog). Each under ~40 characters. Omit for posts that don't need a data list."
        ),
    )
    image_alt_text: str = Field(
        description=(
            "Short, literal accessibility description of what the generated image will show "
            "(objects, setting, composition) — for screen readers, not marketing copy."
        )
    )
