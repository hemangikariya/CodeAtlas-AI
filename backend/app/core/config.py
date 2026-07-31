import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeAtlas AI"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "replace-with-a-cryptographically-secure-key-minimum-32-characters"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/codeatlas"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codeatlas"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Caching / Tasks broker
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    STORAGE_DIR: str = "./data/storage"
    MAX_UPLOAD_SIZE_BYTES: int = 104857600  # 100 MB
    
    # AI Gateway / LLM Keys
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OLLAMA_HOST: str = "http://localhost:11434"
    
    # Prompt Registry
    PROMPT_CACHE_TTL_SECONDS: int = 3600
    
    # Feature Flags
    FEATURE_FLAG_OVERRIDES: str = "{}"
    
    # Telemetry / Observability
    ENABLE_EVALUATION_LOGS: bool = True
    TELEMETRY_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"]

    @field_validator("ASYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: str, info) -> str:
        db_url = info.data.get("DATABASE_URL")
        if db_url and db_url.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return db_url.replace("postgresql://", "postgresql+asyncpg://")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
