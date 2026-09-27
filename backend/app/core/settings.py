from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    secret_key: str = Field(default="dev-secret-key-change-me", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    app_env: str = Field(default="development", env="APP_ENV")
    simulator_max_requests: int = Field(default=100, env="SIMULATOR_MAX_REQUESTS")
    simulator_max_records: int = Field(default=25, env="SIMULATOR_MAX_RECORDS")
    simulator_min_interval_ms: int = Field(default=50, env="SIMULATOR_MIN_INTERVAL_MS")

    class Config:
        env_file = ".env"
        validate_assignment = True
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
