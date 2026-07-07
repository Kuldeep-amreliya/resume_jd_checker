"""
Central app configuration.

Reads from environment variables / a .env file. Never hardcode secrets here.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM (Groq) ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_retries: int = 2
    groq_timeout_seconds: int = 60

    # --- Database ---
    database_url: str = "sqlite:///./resume_jd.db"

    # --- Ingestion ---
    max_upload_size_mb: int = 10
    low_text_confidence_char_threshold: int = 50  # below this many chars extracted from a PDF, flag it

    # --- Scoring ---
    neutral_unknown_score: float = 0.6  # score given to a category when info is UNKNOWN (not 0, not 1)

    # --- App ---
    app_name: str = "Resume-JD Matching Tool"
    debug: bool = False

    @property
    def llm_configured(self) -> bool:
        return bool(self.groq_api_key)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — import and call this, don't instantiate Settings() directly elsewhere."""
    return Settings()