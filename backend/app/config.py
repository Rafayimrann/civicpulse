"""
Centralised runtime configuration.

Everything that varies between environments (dev laptop, CI runner, k8s pod)
comes from environment variables, loaded once here. Nothing else in the
codebase should call os.environ directly - that keeps every "what config
value am I reading" question answerable by looking at this one file.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    app_name: str = "CivicPulse"
    environment: Literal["dev", "ci", "prod"] = "dev"
    log_level: str = "INFO"

    # --- Database ---
    # asyncpg driver for the app, plain psycopg2 URL derived for Alembic (see alembic/env.py)
    database_url: str = "postgresql+asyncpg://civicpulse:civicpulse@localhost:5432/civicpulse"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    stats_cache_ttl_seconds: int = 30
    triage_cache_ttl_seconds: int = 60 * 60 * 24  # 24h

    # --- Rate limiting ---
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 20

    # --- Triage provider selection ---
    triage_provider: Literal["llm", "ollama", "rules", "simulated"] = "simulated"

    # --- Groq (LLMTriage) ---
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.1-8b-instant"
    llm_timeout_seconds: float = 10.0

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"

    # --- Simulated (CI) ---
    simulated_force_failure: bool = False

    # --- Misc ---
    cors_allow_origins: str = "*"  # comma-separated in real deployments


@lru_cache
def get_settings() -> Settings:
    return Settings()
