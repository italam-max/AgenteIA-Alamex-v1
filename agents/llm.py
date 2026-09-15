from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from config.settings import settings

_BRAND_DIR = Path(__file__).resolve().parent.parent / "brand"


def sonnet() -> ChatAnthropic:
    """Strategic reasoning and creative copy — higher quality, higher cost.
    Claude Sonnet 5 rejects `temperature`/`top_p`/`top_k` with a 400; do not set them here."""
    return ChatAnthropic(model="claude-sonnet-5", api_key=settings.anthropic_api_key)


def haiku() -> ChatAnthropic:
    """Mechanical/formatting steps — cheap and fast."""
    return ChatAnthropic(model="claude-haiku-4-5", api_key=settings.anthropic_api_key, temperature=0)


def cached_system_message(agent_prompt_path: Path, ttl: str | None = None) -> SystemMessage:
    """
    Builds a SystemMessage with the agent's static instructions + brand guidelines marked as an
    Anthropic ephemeral cache breakpoint. Only the *static* text goes here — any per-run variable
    data (dates, metrics) must be added to the user turn instead, or it will invalidate the cache
    on every run.

    `ttl`: pass "1h" for callers spaced further apart than the default 5-minute TTL (e.g. the
    growth mission's hourly ticks) — otherwise every call is a guaranteed cache miss, paying the
    write premium (1.25x base input) for a cache entry that always expires unread. The 1h TTL
    writes at 2x instead, but only once per hour instead of never being read at all.
    """
    agent_prompt = agent_prompt_path.read_text(encoding="utf-8")
    guidelines = (_BRAND_DIR / "guidelines.md").read_text(encoding="utf-8")
    static_text = f"{agent_prompt}\n\n## Brand guidelines\n{guidelines}"

    catalog_path = _BRAND_DIR / "equipment_catalog.md"
    if catalog_path.exists():
        static_text += f"\n\n## Equipment/product catalog\n{catalog_path.read_text(encoding='utf-8')}"

    cache_control = {"type": "ephemeral"} if ttl is None else {"type": "ephemeral", "ttl": ttl}
    return SystemMessage(content=[{"type": "text", "text": static_text, "cache_control": cache_control}])
