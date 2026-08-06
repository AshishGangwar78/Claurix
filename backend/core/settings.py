"""
Application settings.

Uses pydantic-settings when installed; otherwise falls back to environment
variables with safe defaults so the existing filesystem pipeline keeps working.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Insurance Gap Analysis"
    log_level: str = "INFO"

    storage_dir: str = "backend/storage"

    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"

    database_url: Optional[str] = None

    copilot_max_sql_retries: int = 3
    copilot_memory_turns: int = 6
    copilot_mastersheet_table: str = "mastersheet"
    copilot_case_filter_column: str = "case_id"
    copilot_debug_default: bool = False

    auth_enabled: bool = False
    auth_optional_bearer_prefix: str = "Bearer "


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Insurance Gap Analysis"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        storage_dir=os.getenv("STORAGE_DIR", "backend/storage"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        database_url=os.getenv("DATABASE_URL") or None,
        copilot_max_sql_retries=int(os.getenv("COPILOT_MAX_SQL_RETRIES", "3")),
        copilot_memory_turns=int(os.getenv("COPILOT_MEMORY_TURNS", "6")),
        copilot_mastersheet_table=os.getenv("COPILOT_MASTERSHEET_TABLE", "mastersheet"),
        copilot_case_filter_column=os.getenv("COPILOT_CASE_FILTER_COLUMN", "case_id"),
        copilot_debug_default=_env_bool("COPILOT_DEBUG_DEFAULT", False),
        auth_enabled=_env_bool("AUTH_ENABLED", False),
        auth_optional_bearer_prefix=os.getenv("AUTH_BEARER_PREFIX", "Bearer "),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return _load_settings()
