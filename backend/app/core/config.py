from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "A4A Learn"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
