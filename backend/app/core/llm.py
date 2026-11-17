from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


@lru_cache
def get_llm() -> ChatOpenAI:
    """Return the sole configured model client shared by every agent."""
    settings = get_settings()
    settings.validate_llm_settings()
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        temperature=0.2,
        timeout=60,
        max_retries=2,
    )
