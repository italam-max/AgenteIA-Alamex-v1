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
    step = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "node": node,
        "message": message,
        "payload": payload,
    }
    # A single atomic `steps || jsonb_build_array(...)` UPDATE (see append_run_step in
    # scripts/setup_supabase_schema.sql) — a Python-side read-modify-write here would lose steps
    # under concurrent writers on the same run_id (e.g. the growth mission tick loop).
    get_client().rpc("append_run_step", {"p_run_id": run_id, "p_step": step}).execute()


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
    weekly_strategy_id: int | None,
    platform: str,
    post_type: str,
    caption: str,
    content_type: str | None = None,
    media_url: str | None = None,
    external_post_id: str | None = None,
    permalink: str | None = None,
    status: str = "draft",
    error: str | None = None,
    layout: str | None = None,
    reference_photo: str | None = None,
    media_generator: str | None = None,
    generation_prompt: str | None = None,
    narration: str | None = None,
) -> int:
    """
    Persist one generated/published post record for a given platform. Returns the posts row id.
    `layout`/`reference_photo`/`media_generator`/`generation_prompt`/`narration` record *how* the
    media was made (not just what it says) so engagement can eventually be correlated back to
    those choices — see post_engagement_snapshots.
    """
    row = {
        "agent_run_id": run_id,
        "weekly_strategy_id": weekly_strategy_id,
        "platform": platform,
        "post_type": post_type,
        "content_type": content_type,
        "caption": caption,
        "media_url": media_url,
        "external_post_id": external_post_id,
        "permalink": permalink,
        "status": status,
        "error": error,
        "layout": layout,
        "reference_photo": reference_photo,
        "media_generator": media_generator,
        "generation_prompt": generation_prompt,
        "narration": narration,
    }
    if status == "published":
        row["published_at"] = datetime.now(timezone.utc).isoformat()
    result = get_client().table("posts").insert(row).execute()
    return result.data[0]["id"]


@tool
def save_post_engagement_snapshot(
    platform: str,
    external_post_id: str,
    likes: int,
    comments: int,
    shares: int,
    impressions: int | None = None,
) -> int:
    """
    Persist one post_engagement_snapshots row — engagement (likes/comments/shares) for a single
    published post at a point in time. Recorded repeatedly over a post's life (not just once) so
    engagement *over time* is available, not just a final count — the signal an eventual ML model
    needs to learn what content/content_type actually drives engagement. Returns the row id.
    """
    row = {
        "platform": platform,
        "external_post_id": external_post_id,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "impressions": impressions,
    }
    result = get_client().table("post_engagement_snapshots").insert(row).execute()
    return result.data[0]["id"]


@tool
def get_post_engagement_history(platform: str, external_post_id: str) -> list[dict]:
    """Fetch all post_engagement_snapshots rows for one post, oldest first — its engagement over time."""
    result = (
        get_client()
        .table("post_engagement_snapshots")
        .select("*")
        .eq("platform", platform)
        .eq("external_post_id", external_post_id)
        .order("recorded_at", desc=False)
        .execute()
    )
    return result.data


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


@tool
def save_growth_snapshot(platform: str, followers_count: int, following_count: int, statuses_count: int) -> int:
    """Persist one growth_snapshots row (account stats at a point in time). Returns the row id."""
    row = {
        "platform": platform,
        "followers_count": followers_count,
        "following_count": following_count,
        "statuses_count": statuses_count,
    }
    result = get_client().table("growth_snapshots").insert(row).execute()
    return result.data[0]["id"]


@tool
def save_growth_action(
    platform: str,
    action_type: str,
    target_account_id: str | None = None,
    target_status_id: str | None = None,
    rationale: str | None = None,
    result: str = "ok",
    error: str | None = None,
) -> int:
    """Persist one growth_actions row (a follow/reply/post the growth mission took). Returns the row id."""
    row = {
        "platform": platform,
        "action_type": action_type,
        "target_account_id": target_account_id,
        "target_status_id": target_status_id,
        "rationale": rationale,
        "result": result,
        "error": error,
    }
    inserted = get_client().table("growth_actions").insert(row).execute()
    return inserted.data[0]["id"]


@tool
def get_recent_growth_snapshots(platform: str, limit: int = 30) -> list[dict]:
    """Fetch the most recent growth_snapshots rows for a platform, oldest first."""
    result = (
        get_client()
        .table("growth_snapshots")
        .select("*")
        .eq("platform", platform)
        .order("recorded_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data))


@tool
def get_recent_growth_actions(platform: str, limit: int = 50) -> list[dict]:
    """Fetch the most recent growth_actions rows for a platform, oldest first."""
    result = (
        get_client()
        .table("growth_actions")
        .select("*")
        .eq("platform", platform)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data))


@tool
def get_followed_account_ids(platform: str) -> list[str]:
    """
    All distinct account_ids ever successfully followed on this platform (full history, not just
    the recent-actions window) — used to exclude them from future follow candidates so the same
    small pool of accounts doesn't get re-"followed" (a no-op on an already-followed account) tick
    after tick instead of discovering new ones.
    """
    result = (
        get_client()
        .table("growth_actions")
        .select("target_account_id")
        .eq("platform", platform)
        .eq("action_type", "follow")
        .eq("result", "ok")
        .execute()
    )
    return sorted({row["target_account_id"] for row in result.data if row.get("target_account_id")})


@tool
def get_replied_status_ids(platform: str) -> list[str]:
    """
    All distinct target_status_ids ever successfully replied to on this platform (full history) —
    used to exclude them from the notifications shown to the planner so the same mention isn't
    answered again in a later tick just because Mastodon still lists it as a recent notification.
    """
    result = (
        get_client()
        .table("growth_actions")
        .select("target_status_id")
        .eq("platform", platform)
        .eq("action_type", "reply")
        .eq("result", "ok")
        .execute()
    )
    return sorted({row["target_status_id"] for row in result.data if row.get("target_status_id")})
