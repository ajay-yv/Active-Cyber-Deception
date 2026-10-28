from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
REAL_DB_PATH = (ROOT_DIR / "real_healthcare.db").as_posix()
SYN_DB_PATH = (ROOT_DIR / "synthetic_healthcare.db").as_posix()
SEC_DB_PATH = (ROOT_DIR / "security_events.db").as_posix()


class DatabaseSettings(BaseSettings):
    real_database_url: str = Field(default=f"sqlite:///{REAL_DB_PATH}", validation_alias="DATABASE_URL")
    synthetic_database_url: str = Field(
        default=f"sqlite:///{SYN_DB_PATH}",
        validation_alias="SYNTHETIC_DATABASE_URL",
    )
    security_database_url: str = Field(
        default=f"sqlite:///{SEC_DB_PATH}",
        validation_alias="SECURITY_DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        validate_assignment=True,
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
