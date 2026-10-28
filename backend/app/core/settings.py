from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SETTINGS_ENV_FILES = (
    WORKSPACE_ROOT / ".env",
    WORKSPACE_ROOT / "backend" / ".env",
    WORKSPACE_ROOT / ".env.local",
)


class Settings(BaseSettings):
    secret_key: str = "dev-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    app_env: str = "development"
    firebase_project_id: str | None = None
    admin_recovery_phone: str | None = None
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "stjude.hospital.security@gmail.com"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_default_country_code: str = "91"
    simulator_max_requests: int = 100
    simulator_max_records: int = 25
    simulator_min_interval_ms: int = 50
    trusted_proxy_cidrs: str = ""
    simulation_demo_enabled: bool = False
    simulation_allowed_hosts: str = ""
    cors_allowed_origins: str = Field(
        default=(
            "http://localhost:3000,http://127.0.0.1:3000,"
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:5174,http://127.0.0.1:5174"
        )
    )

    model_config = SettingsConfigDict(
        env_file=SETTINGS_ENV_FILES,
        env_file_encoding="utf-8",
        validate_assignment=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
