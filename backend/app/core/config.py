from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --------------------------------------------------
    # Application
    # --------------------------------------------------
    APP_NAME: str = "A4A Learn"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --------------------------------------------------
    # Database
    # --------------------------------------------------
    DATABASE_URL: str

    # --------------------------------------------------
    # Security
    # --------------------------------------------------
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # --------------------------------------------------
    # Ollama / Local LLM
    # --------------------------------------------------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    # --------------------------------------------------
    # RAG Retrieval
    # --------------------------------------------------
    RAG_TOP_K: int = 3
    RAG_MAX_DISTANCE: float = 0.85

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()