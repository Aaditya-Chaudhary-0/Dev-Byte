from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file() -> str | None:
    backend_root = Path(__file__).resolve().parents[2]
    candidates = [backend_root.parent / ".env", backend_root / ".env"]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


class Settings(BaseSettings):
    app_name: str = "DEV BYTE"
    api_prefix: Literal["/api"] = "/api"
    database_url: str = Field(min_length=1)
    jwt_secret: str = Field(min_length=32)
    gemini_api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
