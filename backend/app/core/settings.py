from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
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
    frontend_url: str = "https://frontend-eosin-omega-65.vercel.app"
    login_email_otp_enabled: bool = False
    firebase_project_id: str | None = None
    admin_recovery_email: str | None = None
    admin_recovery_phone: str | None = None
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = Field(
        default="",
        validation_alias=AliasChoices("smtp_user", "SMTP_USERNAME", "SMTP_USER"),
    )
    smtp_pass: str = Field(
        default="",
        validation_alias=AliasChoices("smtp_pass", "SMTP_PASSWORD", "SMTP_PASS"),
    )
    smtp_from: str = Field(
        default="stjude.hospital.security@gmail.com",
        validation_alias=AliasChoices(
            "smtp_from",
            "SMTP_FROM_ADDRESS",
            "SMTP_FROM",
        ),
    )
    brevo_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("brevo_api_key", "BREVO_API_KEY"),
    )
    brevo_email_sender: str = Field(
        default="",
        validation_alias=AliasChoices("brevo_email_sender", "BREVO_EMAIL_SENDER"),
    )
    brevo_email_sender_name: str = Field(
        default="Healthcare EHR Portal",
        validation_alias=AliasChoices(
            "brevo_email_sender_name",
            "BREVO_EMAIL_SENDER_NAME",
        ),
    )
    brevo_sms_sender: str = Field(
        default="",
        validation_alias=AliasChoices("brevo_sms_sender", "BREVO_SMS_SENDER"),
    )
    resend_api_key: str = ""
    resend_from_address: str = ""
    otp_sms_provider: Literal["twilio", "msg91", "brevo"] = "brevo"
    msg91_auth_key: str = ""
    msg91_template_id: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_api_key_sid: str = ""
    twilio_api_key_secret: str = ""
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
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
