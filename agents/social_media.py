import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.llm import cached_system_message, sonnet
from agents.schemas import PostContent
from agents.state import AgentState
from config.settings import settings
from tools import media_tools, product_photos_tools, social_tools, supabase_tools

_PROMPT_PATH = Path(__file__).parent / "prompts" / "social_media_system.md"


def _generate_content(
    system_message, planned_post: dict, reference_photos: list[dict], layouts_used_so_far: list[str]
) -> PostContent:
    llm = sonnet().with_structured_output(PostContent)
    user_message = HumanMessage(
        content=(
            f"Tipo de post: {planned_post['type']}\n"
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
        try:
            supabase_tools.append_run_step.invoke(
                {"run_id": run_id, "node": "social_media", "message": f"Redactando caption y prompt de imagen — {label}"}
            )
            content = _generate_content(system_message, planned_post, reference_photos, layouts_used)
            layouts_used.append(content.layout)

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
            image_bytes = media_tools.generate_image.invoke(
                {
                    "prompt": content.media_prompt,
                    "headline": content.headline,
                    "bullets": content.bullets,
                    "layout": content.layout,
                    "reference_photo": content.reference_photo,
                }
            )
            media_url = supabase_tools.upload_media.invoke({"image_bytes": image_bytes})
            generated_assets.append({"post_type": "image", "media_url": media_url})
        except Exception as exc:  # noqa: BLE001 - one failed post shouldn't abort the whole run
            errors.append(f"post '{planned_post.get('theme')}' generation failed: {exc}")
            supabase_tools.append_run_step.invoke(
                {"run_id": run_id, "node": "social_media", "message": f"Falló la generación — {label}: {exc}"}
            )
            continue

        for platform in settings.enabled_platforms:
            try:
                supabase_tools.append_run_step.invoke(
                    {"run_id": run_id, "node": "social_media", "message": f"Publicando en {platform} — {label}"}
                )
                publish_result = social_tools.publish_image_post.invoke(
                    {
                        "platform": platform,
                        "image_bytes": image_bytes,
                        "caption": content.caption,
                        "alt_text": content.image_alt_text,
                    }
                )
                post_row_id = supabase_tools.save_post.invoke(
                    {
                        "run_id": run_id,
                        "weekly_strategy_id": strategy_id,
                        "platform": platform,
                        "post_type": "image",
                        "caption": publish_result.get("caption", content.caption),
                        "media_url": media_url,
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
                supabase_tools.save_post.invoke(
                    {
                        "run_id": run_id,
                        "weekly_strategy_id": strategy_id,
                        "platform": platform,
                        "post_type": "image",
                        "caption": content.caption,
                        "media_url": media_url,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

    run_status = "completed" if published_posts else "failed"
    summary = f"{len(published_posts)} publish(es) across {len(settings.enabled_platforms)} platform(s), {len(state['planned_posts'])} posts planned"
    supabase_tools.update_agent_run.invoke(
        {"run_id": run_id, "status": run_status, "summary": summary, "error": "; ".join(errors) or None}
    )
    supabase_tools.append_run_step.invoke(
        {"run_id": run_id, "node": "social_media", "message": summary, "payload": {"errors": errors}}
    )

    return {"generated_assets": generated_assets, "published_posts": published_posts, "errors": errors}
