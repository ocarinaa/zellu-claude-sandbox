from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")
    APP_NAME: str = "ZELLU Chat API"
    APP_VERSION: str = "0.1.0"
    ENV: str = "local"
    X_API_KEY: str = "changeme"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

@lru_cache
def get_settings() -> Settings:
    return Settings()
