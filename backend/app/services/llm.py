"""LLM client factory for knowledge extraction."""

from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm(temperature: float | None = None) -> ChatOpenAI:
    """Create an OpenAI-compatible LLM client based on settings."""
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        timeout=60,  # 60 seconds timeout
        max_retries=2,  # Retry up to 2 times
    )
