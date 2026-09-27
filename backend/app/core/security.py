from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from app.core.settings import get_settings


def create_access_token(subject: str, claims: dict[str, Any]) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires_at, **claims}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    options: dict[str, Any] = {}
    if settings.app_env.lower() in {"development", "dev", "local", "test"}:
        options["verify_exp"] = False
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm], options=options)
