import json
from datetime import date, timedelta
from pathlib import Path

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agents.llm import cached_system_message, sonnet
from agents.schemas import WeeklyStrategy
from agents.state import AgentState
from config.settings import settings
from tools import social_tools, supabase_tools

_PROMPT_PATH = Path(__file__).parent / "prompts" / "supervisor_system.md"
SUPERVISOR_MODEL = "claude-sonnet-5"
SOCIAL_MEDIA_MODEL = "claude-sonnet-5"


def _monday_of_this_week() -> str:
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


def _fetch_platform_data(platform: str) -> tuple[list[dict], dict, list[str]]:
    errors = []
    try:
        recent_posts = social_tools.get_recent_posts.invoke({"platform": platform, "limit": 10})
    except Exception as exc:  # noqa: BLE001 - keep going with degraded input, not crash the run
        recent_posts = []
        errors.append(f"[{platform}] get_recent_posts failed: {exc}")

    try:
        engagement_summary = social_tools.get_engagement_summary.invoke({"platform": platform})
    except Exception as exc:  # noqa: BLE001
        engagement_summary = {}
        errors.append(f"[{platform}] get_engagement_summary failed: {exc}")

    return recent_posts, engagement_summary, errors


def supervisor_node(state: AgentState) -> Command:
    errors = list(state.get("errors", []))

    run_id = supabase_tools.create_agent_run.invoke(
        {
            "instruction": state["instruction"],
            "supervisor_model": SUPERVISOR_MODEL,
            "social_media_model": SOCIAL_MEDIA_MODEL,
        }
    )

    recent_posts_by_platform: dict[str, list[dict]] = {}
    engagement_by_platform: dict[str, dict] = {}
    for platform in settings.enabled_platforms:
        recent_posts, engagement_summary, platform_errors = _fetch_platform_data(platform)
        recent_posts_by_platform[platform] = recent_posts
        engagement_by_platform[platform] = engagement_summary
        errors.extend(platform_errors)

    week_start = _monday_of_this_week()

    supabase_tools.append_run_step.invoke(
        {
            "run_id": run_id,
            "node": "supervisor",
            "message": f"Fetched recent performance data from: {', '.join(settings.enabled_platforms)}",
            "payload": {platform: len(posts) for platform, posts in recent_posts_by_platform.items()},
        }
    )

    try:
        llm = sonnet().with_structured_output(WeeklyStrategy)
        system_message = cached_system_message(_PROMPT_PATH)
        user_message = HumanMessage(
            content=(
                f"Instrucción del humano: {state['instruction']}\n"
                f"Semana a planear (lunes): {week_start}\n"
                f"Plataformas habilitadas: {', '.join(settings.enabled_platforms)}\n\n"
                f"Posts recientes por plataforma (con engagement/impresiones si están disponibles):\n"
                f"{json.dumps(recent_posts_by_platform, ensure_ascii=False)}\n\n"
                f"Resumen de engagement/reach por plataforma:\n"
                f"{json.dumps(engagement_by_platform, ensure_ascii=False)}"
            )
        )
        strategy: WeeklyStrategy = llm.invoke([system_message, user_message])

        strategy_id = supabase_tools.save_weekly_strategy.invoke(
            {
                "run_id": run_id,
                "week_start": week_start,
                "themes": strategy.themes,
                "num_posts": strategy.num_posts,
                "content_mix": strategy.content_mix,
                "rationale": strategy.rationale,
                "source_metrics": {"recent_posts": recent_posts_by_platform, "engagement": engagement_by_platform},
            }
        )
    except Exception as exc:
        supabase_tools.update_agent_run.invoke(
            {"run_id": run_id, "status": "failed", "error": f"supervisor: {exc}"}
        )
        raise

    supabase_tools.append_run_step.invoke(
        {
            "run_id": run_id,
            "node": "supervisor",
            "message": "Decided weekly strategy",
            "payload": {"strategy_id": strategy_id, "rationale": strategy.rationale},
        }
    )

    return Command(
        goto="social_media",
        update={
            "run_id": run_id,
            "week_start": week_start,
            "recent_posts": recent_posts_by_platform,
            "page_insights": engagement_by_platform,
            "strategy": strategy.model_dump(),
            "strategy_id": strategy_id,
            "planned_posts": [p.model_dump() for p in strategy.planned_posts],
            "errors": errors,
        },
    )
