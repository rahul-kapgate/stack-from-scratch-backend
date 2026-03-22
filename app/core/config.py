from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Stack From Scratch Backend"
    APP_ENV: str = "development"
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()    