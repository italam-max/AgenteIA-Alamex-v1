from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.llm import cached_system_message, sonnet
from agents.schemas import PostContent
from agents.state import AgentState
from config.settings import settings
from tools import media_tools, social_tools, supabase_tools

_PROMPT_PATH = Path(__file__).parent / "prompts" / "social_media_system.md"


def _generate_content(system_message, planned_post: dict) -> PostContent:
    llm = sonnet().with_structured_output(PostContent)
    user_message = HumanMessage(
        content=(
            f"Tipo de post: {planned_post['type']}\n"
            f"Tema: {planned_post['theme']}\n"
            f"Brief: {planned_post['brief']}"
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

    for planned_post in state["planned_posts"]:
        try:
            content = _generate_content(system_message, planned_post)
            image_bytes = media_tools.generate_image.invoke({"prompt": content.media_prompt})
            media_url = supabase_tools.upload_media.invoke({"image_bytes": image_bytes})
            generated_assets.append({"post_type": "image", "media_url": media_url})
        except Exception as exc:  # noqa: BLE001 - one failed post shouldn't abort the whole run
            errors.append(f"post '{planned_post.get('theme')}' generation failed: {exc}")
            continue

        for platform in settings.enabled_platforms:
            try:
                publish_result = social_tools.publish_image_post.invoke(
                    {"platform": platform, "image_bytes": image_bytes, "caption": content.caption}
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
            except Exception as exc:  # noqa: BLE001 - one platform failing shouldn't block the others
                errors.append(f"[{platform}] post '{planned_post.get('theme')}' publish failed: {exc}")
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
