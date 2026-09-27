from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parents[2]
REAL_DB_PATH = (ROOT_DIR / "real_healthcare.db").as_posix()
SYN_DB_PATH = (ROOT_DIR / "synthetic_healthcare.db").as_posix()
SEC_DB_PATH = (ROOT_DIR / "security_events.db").as_posix()


class DatabaseSettings(BaseSettings):
    real_database_url: str = Field(default=f"sqlite:///{REAL_DB_PATH}", env="DATABASE_URL")
    synthetic_database_url: str = Field(default=f"sqlite:///{SYN_DB_PATH}", env="SYNTHETIC_DATABASE_URL")
    security_database_url: str = Field(default=f"sqlite:///{SEC_DB_PATH}", env="SECURITY_DATABASE_URL")

    class Config:
        env_file = ".env"
        validate_assignment = True
        extra = "ignore"


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
