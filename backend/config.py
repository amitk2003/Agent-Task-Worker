"""
Application configuration management.

All environment variables and tunables are defined here.
Uses pydantic-settings for type-safe loading from .env files.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration for the AI Task Worker.

    Every configurable value lives here. To add a new setting:
    1. Add a field below with a sensible default.
    2. Set the real value in your .env file.
    """

    # ── LLM ──────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # ── Agent Limits ─────────────────────────────────────
    max_steps: int = 15
    max_retries_per_step: int = 2

    # ── Server ───────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — reads .env once."""
    return Settings()
