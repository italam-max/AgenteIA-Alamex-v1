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
    media_prompt: str = Field(description="Prompt to send to the image generator, incorporating brand visual guidelines.")
