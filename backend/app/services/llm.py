"""LLM client factory for knowledge extraction."""

from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm(temperature: float | None = None, content_type: str | None = None) -> ChatOpenAI:
    """Create an OpenAI-compatible LLM client based on settings.
    
    Args:
        temperature: Temperature for generation (0.0-1.0)
        content_type: Type of content being generated ('ppt', 'video', 'animation', 'podcast', 'mindmap')
                      Used to select the appropriate model from configuration
    """
    # Select model based on content type
    model_map = {
        'ppt': settings.llm_model_ppt,
        'video': settings.llm_model_video,
        'animation': settings.llm_model_animation,
        'podcast': settings.llm_model_podcast,
        'mindmap': settings.llm_model_mindmap,
    }
    
    model = model_map.get(content_type, settings.llm_model) if content_type else settings.llm_model
    
    return ChatOpenAI(
        model=model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        timeout=120,  # 120 seconds timeout for complex generation
        max_retries=3,  # Retry up to 3 times
    )
