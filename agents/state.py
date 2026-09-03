from typing import TypedDict


class AgentState(TypedDict, total=False):
    instruction: str
    week_start: str

    page_insights: dict
    recent_posts: list[dict]

    strategy: dict
    strategy_id: int
    planned_posts: list[dict]

    generated_assets: list[dict]
    published_posts: list[dict]

    run_id: int
    errors: list[str]
