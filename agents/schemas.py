from typing import Literal

from pydantic import BaseModel, Field

# Shared between PlannedPost (weekly/on-demand posts) and GrowthPlan (growth mission's own extra
# posts) so the two never drift — adding a content type means updating this in one place, plus
# the matching prompts (agents/prompts/*_system.md) and the `posts.content_type` check constraint
# (scripts/setup_supabase_schema.sql).
ContentType = Literal["producto", "educativo", "pregunta_comunidad", "detras_de_camaras", "refacciones"]


class PlannedPost(BaseModel):
    type: Literal["image", "video"] = Field(
        description=(
            "'image': composited graphic (real/generated photo + headline/bullets drawn by code). "
            "'video': short vertical clip (Higgsfield b-roll + OpenAI-narrated voiceover) — slower "
            "and more expensive to generate, use sparingly for content that benefits from motion "
            "(a quick process/demo shot), not as a default replacement for image posts."
        )
    )
    content_type: ContentType = Field(
        description=(
            "What this post is *for* — not every post should sell. 'producto': features/specs of a "
            "model, CTA-friendly. 'educativo': a real technical fact/curiosity (from the guidelines/"
            "catalog) taught for its own sake, no CTA. 'pregunta_comunidad': leads with a genuine "
            "open question to the audience about their own experience/opinion — the post exists to "
            "start a conversation, not to inform or sell. 'detras_de_camaras': process/engineering/"
            "team angle instead of a finished product. 'refacciones': a spare-part angle (experimental "
            "— testing whether this line has its own audience, separate from new-elevator sales) — "
            "leads with a common failure symptom (e.g. a button panel that stopped responding, a "
            "worn cable) and names the likely part category, without inventing a specific part number, "
            "price, or exact-model compatibility not confirmed in the catalog; CTA points them to reach "
            "out (WhatsApp/web) for the exact match instead of promising availability. Mix these across "
            "a run's posts — a batch that is all 'producto' reads as a catalog, not a community."
        )
    )
    theme: str
    brief: str = Field(description="Short creative brief for this post, used to prompt image generation and copy.")


class WeeklyStrategy(BaseModel):
    themes: list[str]
    num_posts: int
    content_mix: dict[str, int] = Field(description='e.g. {"image": 3, "video": 1}.')
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
        default="",
        description=(
            "Prompt for the background photo only (scene, composition, materials, lighting, brand colors), "
            "used only when `reference_photo` is null — leave empty when `reference_photo` is set. Never "
            "describe text, headlines, panels, or data here — that's drawn separately from `headline`/`bullets`."
        ),
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


class VideoPostContent(BaseModel):
    caption: str = Field(description="Ready-to-publish social media caption, on-brand and in the page's language.")
    video_prompt: str = Field(
        description=(
            "Visual description of a single continuous b-roll scene (composition, materials, "
            "lighting, brand colors) for the video clip — no on-screen text, panels, logos, or "
            "screens/signage: unlike image posts, there is no compositing step for video, so "
            "nothing gets drawn on top afterward. Keep it conceptual/abstract, NOT people-centric: "
            "describe the machine, material, mechanism, light, or motion itself (a gearless machine "
            "turning, cables tensioning, a cabin gliding past floor sensors, dust in a light beam) "
            "rather than technicians/workers/hands — AI video models render human figures/faces "
            "poorly, and it reads as more premium/brand-forward without them anyway."
        )
    )
    narration: str = Field(
        description=(
            "Short spoken-voiceover script, ~4-6 seconds out loud (roughly 10-16 words), on-brand "
            "tone. Write it to sound natural when heard, not read — this gets converted to audio via "
            "text-to-speech and played over the clip. Keep it this short on purpose: the underlying "
            "video clip is a fixed ~5s loop, so a longer narration just repeats the same loop more "
            "times and looks visibly repetitive — one tight, punchy line beats a paragraph here."
        )
    )


class GrowthReply(BaseModel):
    status_id: str = Field(description="Exact status_id of the mention being answered, from the notifications list given.")
    text: str = Field(description="Reply text, on-brand and in the page's language.")


class GrowthPlan(BaseModel):
    reasoning: str = Field(
        description="Brief rationale for this tick's plan, referencing the heuristic performance summary given."
    )
    replies: list[GrowthReply] = Field(
        default_factory=list,
        description="Mentions worth answering this tick — only real, relevant ones from the notifications list. Empty if none are worth it.",
    )
    accounts_to_follow: list[str] = Field(
        default_factory=list,
        description=(
            "Exact account_id values (from the candidate accounts list given) genuinely relevant to Alamex's "
            "business to follow this tick. Never pad this list just to hit a number — empty if no good candidates."
        ),
    )
    post_theme: str | None = Field(
        default=None,
        description=(
            "If an extra organic post is worth publishing this tick, a short theme/brief for it — prefer "
            "content designed to spark conversation (a genuine question, a curiosity) over another product "
            "pitch. Null if nothing is worth publishing outside the normal weekly calendar."
        ),
    )
    post_content_type: ContentType | None = Field(
        default=None,
        description="Required alongside `post_theme` when it's set — see `PlannedPost.content_type` for what each value means. Null when `post_theme` is null.",
    )
    post_type: Literal["image", "video"] | None = Field(
        default=None,
        description=(
            "Required alongside `post_theme` when it's set — see `PlannedPost.type`. 'video' is "
            "slower/more expensive to generate, use it sparingly. Null when `post_theme` is null."
        ),
    )
