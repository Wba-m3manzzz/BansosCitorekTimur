from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "backend"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    MODEL_PATH: str = "models/model_knn_bansos.joblib"
    MODEL_METADATA_PATH: str = "models/model_metadata.json"
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175",
        description="Comma-separated list of allowed frontend origins",
    )
    LOG_LEVEL: str = "INFO"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemma-4-26b-a4b-it"
    GEMINI_TIMEOUT_MS: int = 15000
    CHAT_MEMORY_MESSAGE_LIMIT: int = 12
    CHAT_MEMORY_CONVERSATION_LIMIT: int = 200
    CHAT_MEMORY_TTL_SECONDS: int = 1800

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"prod", "production"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
