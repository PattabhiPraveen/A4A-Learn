from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


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
    # CORS
    # --------------------------------------------------

    CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    CORS_ALLOW_CREDENTIALS: bool = True

    CORS_ALLOW_METHODS: str = (
        "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )

    CORS_ALLOW_HEADERS: str = "*"

    # --------------------------------------------------
    # Ollama / Local LLM
    # --------------------------------------------------

    OLLAMA_BASE_URL: str = (
        "http://localhost:11434"
    )

    OLLAMA_MODEL: str = "qwen2.5:3b"

    # --------------------------------------------------
    # RAG Retrieval
    # --------------------------------------------------

    RAG_TOP_K: int = 3

    RAG_MAX_DISTANCE: float = 0.85

    # --------------------------------------------------
    # Governed Web Retrieval
    # --------------------------------------------------

    # Web retrieval remains disabled by default.
    # This preserves A4A Learn's local/offline mode.

    A4A_WEB_SEARCH_ENABLED: bool = False

    # External retrieval is intended only as a fallback
    # when approved local learning evidence is insufficient.

    A4A_WEB_FALLBACK_ONLY: bool = True

    # Maximum number of approved external sources that
    # may be returned to the downstream evidence pipeline.

    A4A_WEB_MAX_RESULTS: int = 3

    # Maximum time allowed for an external search or
    # evidence-fetch request.

    A4A_WEB_TIMEOUT_SECONDS: int = 8

    # Maximum HTML response size accepted from an
    # approved external source.
    #
    # This prevents unexpectedly large responses from
    # consuming excessive memory.

    A4A_WEB_MAX_CONTENT_BYTES: int = 1_000_000

    # Maximum number of redirects followed while
    # acquiring approved external evidence.

    A4A_WEB_MAX_REDIRECTS: int = 3

    # Only these domains may cross the trusted-source
    # boundary.
    #
    # Search engines may return results from other domains,
    # but WebSourcePolicy will reject them.

    A4A_WEB_ALLOWED_DOMAINS: str = (
        "docs.python.org,"
        "scikit-learn.org,"
        "pytorch.org,"
        "tensorflow.org"
    )

    # Local SearXNG instance used only for discovering
    # candidate external sources.
    #
    # SearXNG results remain untrusted until they pass
    # through WebSourcePolicy.

    A4A_SEARXNG_BASE_URL: str = (
        "http://127.0.0.1:8088"
    )

    # --------------------------------------------------
    # Pydantic Settings Configuration
    # --------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()