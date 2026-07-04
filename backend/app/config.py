import json
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings configuration using Pydantic Settings.
    Loads variables from Environment or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Core Configurations
    PROJECT_NAME: str = "Prompt Guesser"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parses CORS origins from a comma-separated string or a JSON array.
        """
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    return json.loads(v_trimmed)
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v_trimmed.split(",") if i.strip()]
        return v

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./prompt_guesser.db"

    # AI Integration Configuration
    AI_API_KEY: str = "your-ai-api-key-here"
    AI_IMAGE_MODEL: str = "imagen-4.0-generate-001"
    AI_EMBEDDING_MODEL: str = "gemini-embedding-2"
    AI_EMBEDDING_DIMENSION: int = 768
    AI_TEXT_MODEL: str = "gemini-2.5-flash"
    AI_RETRY_COUNT: int = 3
    AI_TIMEOUT_SECONDS: int = 30

    # Storage Configuration
    STORAGE_LOCAL_DIR: str = "./storage/images"

    # Scheduler Configuration
    SCHEDULER_BUFFER_SIZE: int = 14
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "UTC"
    SCHEDULER_MAX_RETRIES: int = 3
    SCHEDULER_RETRY_DELAY_SECONDS: int = 5


settings = Settings()
