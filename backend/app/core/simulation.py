from ipaddress import ip_address
from urllib.parse import urlparse

from fastapi import HTTPException, status

from app.core.settings import get_settings


LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def simulation_enabled() -> bool:
    return get_settings().app_env.lower() in {"development", "test", "testing"}


def require_simulation_enabled() -> None:
    if not simulation_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development security simulation is disabled",
        )


def validate_local_target(target: str) -> str:
    parsed = urlparse(target)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or hostname not in LOOPBACK_HOSTS:
        try:
            is_loopback = ip_address(hostname).is_loopback
        except ValueError:
            is_loopback = False
        if not is_loopback:
            raise ValueError("The simulator target must use a loopback hostname or address")
    if parsed.username or parsed.password or not parsed.netloc:
        raise ValueError("The simulator target must not contain credentials")
    return target.rstrip("/")


def bounded_count(value: int, limit: int, name: str) -> int:
    if value < 1 or value > limit:
        raise ValueError(f"{name} must be between 1 and {limit}")
    return value