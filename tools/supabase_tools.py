from datetime import datetime, timezone

from langchain_core.tools import tool

from integrations.supabase_client import get_client, upload_public_image


@tool
def upload_media(image_bytes: bytes, content_type: str = "image/png") -> str:
    """Upload generated image bytes to public storage so it can be shown in the dashboard. Returns a public URL."""
    return upload_public_image(image_bytes, content_type)


@tool
def create_agent_run(instruction: str, supervisor_model: str, social_media_model: str) -> int:
    """Create a new agent_runs row at the start of a run. Returns the run id."""
    row = {
        "instruction": instruction,
        "status": "running",
        "supervisor_model": supervisor_model,
        "social_media_model": social_media_model,
    }
    result = get_client().table("agent_runs").insert(row).execute()
    return result.data[0]["id"]


@tool
def update_agent_run(run_id: int, status: str, summary: str | None = None, error: str | None = None) -> None:
    """Update an agent_runs row's status (running/completed/failed), optional summary and error."""
    update = {"status": status}
    if status in ("completed", "failed"):
        update["finished_at"] = datetime.now(timezone.utc).isoformat()
    if summary is not None:
        update["summary"] = summary
    if error is not None:
        update["error"] = error
    get_client().table("agent_runs").update(update).eq("id", run_id).execute()


@tool
def append_run_step(run_id: int, node: str, message: str, payload: dict | None = None) -> None:
    """Append one step to the agent_runs.steps log for auditing what each node did."""
    client = get_client()
    current = client.table("agent_runs").select("steps").eq("id", run_id).single().execute()
    steps = (current.data or {}).get("steps") or []
    steps.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "node": node,
            "message": message,
            "payload": payload,
        }
    )
    client.table("agent_runs").update({"steps": steps}).eq("id", run_id).execute()


@tool
def save_weekly_strategy(
    run_id: int,
    week_start: str,
    themes: list[str],
    num_posts: int,
    content_mix: dict,
    rationale: str,
    source_metrics: dict | None = None,
) -> int:
    """Persist the supervisor's weekly content strategy decision. Returns the weekly_strategy id."""
    row = {
        "agent_run_id": run_id,
        "week_start": week_start,
        "themes": themes,
        "num_posts": num_posts,
        "content_mix": content_mix,
        "rationale": rationale,
        "source_metrics": source_metrics,
    }
    result = get_client().table("weekly_strategy").insert(row).execute()
    return result.data[0]["id"]


@tool
def save_post(
    run_id: int,
    weekly_strategy_id: int,
    platform: str,
    post_type: str,
    caption: str,
    media_url: str | None = None,
    external_post_id: str | None = None,
    permalink: str | None = None,
    status: str = "draft",
    error: str | None = None,
) -> int:
    """Persist one generated/published post record for a given platform. Returns the posts row id."""
    row = {
        "agent_run_id": run_id,
        "weekly_strategy_id": weekly_strategy_id,
        "platform": platform,
        "post_type": post_type,
        "caption": caption,
        "media_url": media_url,
        "external_post_id": external_post_id,
        "permalink": permalink,
        "status": status,
        "error": error,
    }
    if status == "published":
        row["published_at"] = datetime.now(timezone.utc).isoformat()
    result = get_client().table("posts").insert(row).execute()
    return result.data[0]["id"]


@tool
def get_recent_strategies(limit: int = 4) -> list[dict]:
    """Fetch the most recent weekly_strategy rows for the supervisor's own historical context."""
    result = (
        get_client()
        .table("weekly_strategy")
        .select("*")
        .order("week_start", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
