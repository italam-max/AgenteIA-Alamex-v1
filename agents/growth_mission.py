import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.llm import cached_system_message, sonnet
from agents.schemas import GrowthPlan
from agents.social_media import _generate_content
from agents.social_media import _PROMPT_PATH as _SOCIAL_MEDIA_PROMPT_PATH
from config.settings import settings
from integrations.social.registry import get_publisher
from tools import media_tools, product_photos_tools, social_tools, supabase_tools

_PROMPT_PATH = Path(__file__).parent / "prompts" / "growth_mission_system.md"
_PLATFORM = "mastodon"  # growth mission is Mastodon-only — see README.md.


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _build_heuristic_summary(snapshots: list[dict], actions: list[dict]) -> str:
    """
    Plain-arithmetic feedback loop (not a trained model — there isn't enough history for that
    yet): for each interval between two consecutive snapshots, how many followers were gained and
    which action types happened in that window, so the LLM can lean toward what's worked so far.
    """
    if len(snapshots) < 2:
        return "Aún no hay suficiente historial para sacar conclusiones — este es de los primeros ciclos."

    intervals = []
    for prev, curr in zip(snapshots, snapshots[1:]):
        prev_ts, curr_ts = _parse_ts(prev["recorded_at"]), _parse_ts(curr["recorded_at"])
        delta = curr["followers_count"] - prev["followers_count"]
        counts = Counter(
            a["action_type"] for a in actions if prev_ts <= _parse_ts(a["created_at"]) < curr_ts
        )
        intervals.append({"delta": delta, "counts": counts})

    total_delta = sum(i["delta"] for i in intervals)
    lines = [f"Cambio neto de seguidores en los últimos {len(intervals)} ciclos: {total_delta:+d}."]
    for action_type in ("follow", "reply", "post"):
        deltas_with_action = [i["delta"] for i in intervals if i["counts"].get(action_type)]
        if deltas_with_action:
            avg = sum(deltas_with_action) / len(deltas_with_action)
            lines.append(
                f"Ciclos con al menos un '{action_type}': {len(deltas_with_action)}, "
                f"cambio promedio de seguidores {avg:+.1f}."
            )
    return " ".join(lines)


def _publish_extra_post(theme: str, content_type: str, post_type: str = "image") -> None:
    run_id = supabase_tools.create_agent_run.invoke(
        {"instruction": f"growth mission: {theme}", "supervisor_model": "growth_mission", "social_media_model": "growth_mission"}
    )
    is_video = post_type == "video"
    try:
        reference_photos = product_photos_tools.list_reference_photos.invoke({})
        system_message = cached_system_message(_SOCIAL_MEDIA_PROMPT_PATH, ttl="1h")
        planned_post = {"type": post_type, "content_type": content_type, "theme": theme, "brief": theme}
        content = _generate_content(system_message, planned_post, reference_photos, [])

        if is_video:
            media_bytes = media_tools.generate_video.invoke(
                {"prompt": content.video_prompt, "narration": content.narration}
            )
            media_url = supabase_tools.upload_media.invoke({"image_bytes": media_bytes, "content_type": "video/mp4"})
            publish_result = social_tools.publish_video_post.invoke(
                {"platform": _PLATFORM, "video_url": media_url, "caption": content.caption}
            )
            generation_meta = {
                "layout": None,
                "reference_photo": None,
                "media_generator": settings.video_generator,
                "generation_prompt": content.video_prompt,
                "narration": content.narration,
            }
        else:
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
            publish_result = social_tools.publish_image_post.invoke(
                {
                    "platform": _PLATFORM,
                    "image_bytes": media_bytes,
                    "caption": content.caption,
                    "alt_text": content.image_alt_text,
                }
            )
            generation_meta = {
                "layout": content.layout,
                "reference_photo": content.reference_photo,
                "media_generator": settings.media_generator if not content.reference_photo else None,
                "generation_prompt": content.media_prompt or None,
                "narration": None,
            }
        supabase_tools.save_post.invoke(
            {
                "run_id": run_id,
                "weekly_strategy_id": None,
                "platform": _PLATFORM,
                "post_type": post_type,
                "content_type": content_type,
                "caption": publish_result.get("caption", content.caption),
                "media_url": media_url,
                "external_post_id": publish_result.get("post_id"),
                "permalink": publish_result.get("permalink"),
                "status": "published",
                **generation_meta,
            }
        )
        supabase_tools.save_growth_action.invoke(
            {"platform": _PLATFORM, "action_type": "post", "rationale": theme, "result": "ok"}
        )
        supabase_tools.update_agent_run.invoke(
            {"run_id": run_id, "status": "completed", "summary": f"Growth mission post: {theme}"}
        )
    except Exception as exc:  # noqa: BLE001 - one failed extra post shouldn't abort the tick
        supabase_tools.save_growth_action.invoke(
            {"platform": _PLATFORM, "action_type": "post", "rationale": theme, "result": "failed", "error": str(exc)}
        )
        supabase_tools.update_agent_run.invoke({"run_id": run_id, "status": "failed", "error": str(exc)})


def run_growth_tick(target_followers: int) -> dict:
    publisher = get_publisher(_PLATFORM)

    stats = publisher.get_account_stats()
    supabase_tools.save_growth_snapshot.invoke({"platform": _PLATFORM, **stats})

    if stats["followers_count"] >= target_followers:
        return {"done": True, **stats}

    snapshots = supabase_tools.get_recent_growth_snapshots.invoke({"platform": _PLATFORM})
    actions = supabase_tools.get_recent_growth_actions.invoke({"platform": _PLATFORM})
    heuristic_summary = _build_heuristic_summary(snapshots, actions)

    already_replied = set(supabase_tools.get_replied_status_ids.invoke({"platform": _PLATFORM}))
    notifications = [
        n for n in publisher.get_notifications(limit=20) if n["status_id"] not in already_replied
    ]
    recent_posts = social_tools.get_recent_posts.invoke({"platform": _PLATFORM, "limit": 8})
    recent_captions = [p.get("message", "") for p in recent_posts]

    # Piggybacks on the recent_posts fetch above — records engagement *over time* per post (not
    # just a final count), the signal an eventual ML model needs to learn what content actually
    # drives engagement, since growth_snapshots only tracks the account-level follower count.
    for post in recent_posts:
        engagement = post.get("engagement") or {}
        supabase_tools.save_post_engagement_snapshot.invoke(
            {
                "platform": _PLATFORM,
                "external_post_id": post["id"],
                "likes": engagement.get("likes") or 0,
                "comments": engagement.get("comments") or 0,
                "shares": engagement.get("shares") or 0,
                "impressions": post.get("impressions"),
            }
        )

    already_followed = set(supabase_tools.get_followed_account_ids.invoke({"platform": _PLATFORM}))
    candidate_accounts_by_id: dict[str, dict] = {}
    for hashtag in settings.growth_hashtags:
        for account in publisher.search_accounts_by_hashtag(hashtag, limit=10):
            if account["account_id"] not in already_followed:
                candidate_accounts_by_id.setdefault(account["account_id"], account)
    candidate_accounts = list(candidate_accounts_by_id.values())

    system_message = cached_system_message(_PROMPT_PATH, ttl="1h")
    user_message = HumanMessage(
        content=(
            f"Objetivo de seguidores: {target_followers}\n"
            f"Estadísticas actuales: {json.dumps(stats, ensure_ascii=False)}\n"
            f"Resumen heurístico de ciclos anteriores: {heuristic_summary}\n\n"
            f"Cupo este ciclo: máximo {settings.growth_max_replies_per_tick} respuestas, "
            f"máximo {settings.growth_max_follows_per_tick} follows.\n\n"
            f"Menciones/comentarios candidatos a responder (en nuestras propias publicaciones):\n"
            f"{json.dumps(notifications, ensure_ascii=False)}\n\n"
            f"Cuentas candidatas a seguir (descubiertas por hashtag):\n"
            f"{json.dumps(candidate_accounts, ensure_ascii=False)}\n\n"
            f"Últimos posts publicados (para NO repetir el mismo tema/ángulo si decides publicar uno extra):\n"
            f"{json.dumps(recent_captions, ensure_ascii=False)}"
        )
    )
    plan: GrowthPlan = sonnet().with_structured_output(GrowthPlan).invoke([system_message, user_message])

    # Logged unconditionally (even if the plan takes no concrete action this tick) so the
    # dashboard's bitácora always shows what the agent is thinking, not only when it acts.
    supabase_tools.save_growth_action.invoke(
        {"platform": _PLATFORM, "action_type": "tick", "rationale": plan.reasoning, "result": "ok"}
    )

    replies = plan.replies[: settings.growth_max_replies_per_tick]
    for reply in replies:
        try:
            publisher.reply_to_status(reply.status_id, reply.text)
            supabase_tools.save_growth_action.invoke(
                {
                    "platform": _PLATFORM,
                    "action_type": "reply",
                    "target_status_id": reply.status_id,
                    "rationale": plan.reasoning,
                    "result": "ok",
                }
            )
        except Exception as exc:  # noqa: BLE001 - one failed reply shouldn't block the rest
            supabase_tools.save_growth_action.invoke(
                {
                    "platform": _PLATFORM,
                    "action_type": "reply",
                    "target_status_id": reply.status_id,
                    "rationale": plan.reasoning,
                    "result": "failed",
                    "error": str(exc),
                }
            )

    accounts_to_follow = plan.accounts_to_follow[: settings.growth_max_follows_per_tick]
    for account_id in accounts_to_follow:
        try:
            publisher.follow_account(account_id)
            supabase_tools.save_growth_action.invoke(
                {
                    "platform": _PLATFORM,
                    "action_type": "follow",
                    "target_account_id": account_id,
                    "rationale": plan.reasoning,
                    "result": "ok",
                }
            )
        except Exception as exc:  # noqa: BLE001 - one failed follow shouldn't block the rest
            supabase_tools.save_growth_action.invoke(
                {
                    "platform": _PLATFORM,
                    "action_type": "follow",
                    "target_account_id": account_id,
                    "rationale": plan.reasoning,
                    "result": "failed",
                    "error": str(exc),
                }
            )

    if plan.post_theme:
        _publish_extra_post(plan.post_theme, plan.post_content_type or "educativo", plan.post_type or "image")

    return {
        "done": False,
        **stats,
        "replies": len(replies),
        "follows": len(accounts_to_follow),
        "posted": bool(plan.post_theme),
    }
