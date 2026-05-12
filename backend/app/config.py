from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:123456@localhost:5432/hexamind"

    # Upload
    upload_dir: Path = Path("uploads")
    max_upload_size: int = 50 * 1024 * 1024  # 50MB

    # LLM Configuration
    llm_provider: str = "openai"  # openai-compatible (Qwen, DeepSeek, etc.)
    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    llm_temperature: float = 0.7
    
    # LLM Models for different content types
    llm_model_ppt: str = "qwen-plus"
    llm_model_video: str = "qwen-plus"
    llm_model_animation: str = "qwen-plus"
    llm_model_podcast: str = "qwen-plus"
    llm_model_mindmap: str = "qwen-plus"

    # Extraction
    extraction_cache_dir: Path = Path(".cache/extractions")

    # PPT Generation
    ppt_output_dir: Path = Path("outputs/ppt")

    # Video Generation
    video_output_dir: Path = Path("outputs/video")

    # Animation Generation
    animation_output_dir: Path = Path("outputs/animation")

    # Podcast Generation
    podcast_output_dir: Path = Path("outputs/podcast")

    # Mindmap Generation
    mindmap_output_dir: Path = Path("outputs/mindmap")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.extraction_cache_dir.mkdir(parents=True, exist_ok=True)
settings.ppt_output_dir.mkdir(parents=True, exist_ok=True)
settings.video_output_dir.mkdir(parents=True, exist_ok=True)
settings.animation_output_dir.mkdir(parents=True, exist_ok=True)
settings.podcast_output_dir.mkdir(parents=True, exist_ok=True)
settings.mindmap_output_dir.mkdir(parents=True, exist_ok=True)
