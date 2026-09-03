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


def cached_system_message(agent_prompt_path: Path) -> SystemMessage:
    """
    Builds a SystemMessage with the agent's static instructions + brand guidelines marked as an
    Anthropic ephemeral cache breakpoint. Only the *static* text goes here — any per-run variable
    data (dates, metrics) must be added to the user turn instead, or it will invalidate the cache
    on every run.
    """
    agent_prompt = agent_prompt_path.read_text(encoding="utf-8")
    guidelines = (_BRAND_DIR / "guidelines.md").read_text(encoding="utf-8")
    static_text = f"{agent_prompt}\n\n## Brand guidelines\n{guidelines}"

    catalog_path = _BRAND_DIR / "equipment_catalog.md"
    if catalog_path.exists():
        static_text += f"\n\n## Equipment/product catalog\n{catalog_path.read_text(encoding='utf-8')}"
    return SystemMessage(
        content=[{"type": "text", "text": static_text, "cache_control": {"type": "ephemeral"}}]
    )
