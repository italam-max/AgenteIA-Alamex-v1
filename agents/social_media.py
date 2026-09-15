import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.llm import cached_system_message, sonnet
from agents.schemas import PostContent, VideoPostContent
from agents.state import AgentState
from config.settings import settings
from tools import media_tools, product_photos_tools, social_tools, supabase_tools

_PROMPT_PATH = Path(__file__).parent / "prompts" / "social_media_system.md"


def _generate_content(
    system_message, planned_post: dict, reference_photos: list[dict], layouts_used_so_far: list[str]
) -> PostContent | VideoPostContent:
    schema = VideoPostContent if planned_post["type"] == "video" else PostContent
    llm = sonnet().with_structured_output(schema)
    user_message = HumanMessage(
        content=(
            f"Tipo de post: {planned_post['type']}\n"
            f"Content type: {planned_post.get('content_type', 'producto')}\n"
            f"Tema: {planned_post['theme']}\n"
            f"Brief: {planned_post['brief']}\n\n"
            f"Fotos reales disponibles (reference_photo, usa el filename exacto si alguna aplica):\n"
            f"{json.dumps(reference_photos, ensure_ascii=False)}\n\n"
            f"Layouts ya usados en esta corrida (evita repetir salvo que el brief lo pida): "
            f"{layouts_used_so_far or 'ninguno todavía'}"
        )
    )
    return llm.invoke([system_message, user_message])


def social_media_node(state: AgentState) -> dict:
    run_id = state["run_id"]
    strategy_id = state["strategy_id"]
    errors = list(state.get("errors", []))
    generated_assets: list[dict] = []
    published_posts: list[dict] = []

    system_message = cached_system_message(_PROMPT_PATH)
    total = len(state["planned_posts"])
    reference_photos = product_photos_tools.list_reference_photos.invoke({})
    layouts_used: list[str] = []

    for index, planned_post in enumerate(state["planned_posts"], start=1):
        label = f"post {index}/{total} ({planned_post.get('theme')})"
        is_video = planned_post["type"] == "video"
        try:
            supabase_tools.append_run_step.invoke(
                {"run_id": run_id, "node": "social_media", "message": f"Redactando caption y guion — {label}"}
            )
            content = _generate_content(system_message, planned_post, reference_photos, layouts_used)
            if not is_video:
                layouts_used.append(content.layout)

            if is_video:
                supabase_tools.append_run_step.invoke(
                    {"run_id": run_id, "node": "social_media", "message": f"Generando video (Higgsfield + voz OpenAI) — {label}"}
                )
                media_bytes = media_tools.generate_video.invoke(
                    {"prompt": content.video_prompt, "narration": content.narration}
                )
                media_url = supabase_tools.upload_media.invoke({"image_bytes": media_bytes, "content_type": "video/mp4"})
                generation_meta = {
                    "layout": None,
                    "reference_photo": None,
                    "media_generator": settings.video_generator,
                    "generation_prompt": content.video_prompt,
                    "narration": content.narration,
                }
            else:
                supabase_tools.append_run_step.invoke(
                    {
                        "run_id": run_id,
                        "node": "social_media",
                        "message": (
                            f"Generando imagen (layout={content.layout}, foto="
                            f"{content.reference_photo or settings.media_generator}) — {label}"
                        ),
                    }
                )
                media_bytes = media_tools.generate_image.invoke(
                    {
                        "prompt": content.media_prompt,
                        "headline": content.headline,
                        "bullets": content.bullets,
                        "layout": content.layout,
                        "reference_photo": content.reference_photo,
                    }
                )
                media_url = supabase_tools.upload_media.invoke({"image_bytes": media_bytes})
                generation_meta = {
                    "layout": content.layout,
                    "reference_photo": content.reference_photo,
                    "media_generator": settings.media_generator if not content.reference_photo else None,
                    "generation_prompt": content.media_prompt or None,
                    "narration": None,
                }
            generated_assets.append({"post_type": planned_post["type"], "media_url": media_url})
        except Exception as exc:  # noqa: BLE001 - one failed post shouldn't abort the whole run
            errors.append(f"post '{planned_post.get('theme')}' generation failed: {exc}")
            supabase_tools.append_run_step.invoke(
                {"run_id": run_id, "node": "social_media", "message": f"Falló la generación — {label}: {exc}"}
            )
            continue

        for platform in settings.enabled_platforms:
            post_row = {
                "run_id": run_id,
                "weekly_strategy_id": strategy_id,
                "platform": platform,
                "post_type": planned_post["type"],
                "content_type": planned_post.get("content_type"),
                "caption": content.caption,
                "media_url": media_url,
                **generation_meta,
            }
            try:
                supabase_tools.append_run_step.invoke(
                    {"run_id": run_id, "node": "social_media", "message": f"Publicando en {platform} — {label}"}
                )
                if is_video:
                    publish_result = social_tools.publish_video_post.invoke(
                        {"platform": platform, "video_url": media_url, "caption": content.caption}
                    )
                else:
                    publish_result = social_tools.publish_image_post.invoke(
                        {
                            "platform": platform,
                            "image_bytes": media_bytes,
                            "caption": content.caption,
                            "alt_text": content.image_alt_text,
                        }
                    )
                post_row_id = supabase_tools.save_post.invoke(
                    {
                        **post_row,
                        "caption": publish_result.get("caption", content.caption),
                        "external_post_id": publish_result.get("post_id"),
                        "permalink": publish_result.get("permalink"),
                        "status": "published",
                    }
                )
                published_posts.append(
                    {"platform": platform, "post_row_id": post_row_id, "post_id": publish_result.get("post_id")}
                )
                supabase_tools.append_run_step.invoke(
                    {
                        "run_id": run_id,
                        "node": "social_media",
                        "message": f"Publicado en {platform} — {label}",
                        "payload": {"permalink": publish_result.get("permalink")},
                    }
                )
            except Exception as exc:  # noqa: BLE001 - one platform failing shouldn't block the others
                errors.append(f"[{platform}] post '{planned_post.get('theme')}' publish failed: {exc}")
                supabase_tools.append_run_step.invoke(
                    {"run_id": run_id, "node": "social_media", "message": f"Falló en {platform} — {label}: {exc}"}
                )
                supabase_tools.save_post.invoke({**post_row, "status": "failed", "error": str(exc)})

    run_status = "completed" if published_posts else "failed"
    summary = f"{len(published_posts)} publish(es) across {len(settings.enabled_platforms)} platform(s), {len(state['planned_posts'])} posts planned"
    supabase_tools.update_agent_run.invoke(
        {"run_id": run_id, "status": run_status, "summary": summary, "error": "; ".join(errors) or None}
    )
    supabase_tools.append_run_step.invoke(
        {"run_id": run_id, "node": "social_media", "message": summary, "payload": {"errors": errors}}
    )

    return {"generated_assets": generated_assets, "published_posts": published_posts, "errors": errors}
