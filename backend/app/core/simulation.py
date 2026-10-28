from ipaddress import ip_address
from urllib.parse import urlparse

from fastapi import HTTPException, status
from starlette.requests import Request

from app.core.settings import get_settings


LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def simulation_enabled(hostname: str | None = None) -> bool:
    settings = get_settings()
    environment = settings.app_env.lower()
    if environment in {"development", "test", "testing"}:
        return True
    if environment != "demo" or not settings.simulation_demo_enabled or not hostname:
        return False

    allowed_hosts = {
        item.strip().lower().rstrip(".")
        for item in settings.simulation_allowed_hosts.split(",")
        if item.strip()
    }
    return hostname.lower().rstrip(".") in allowed_hosts


def require_simulation_enabled(request: Request) -> None:
    settings = get_settings()
    is_demo = settings.app_env.lower() == "demo"
    is_secure_demo_origin = request.url.scheme == "https" and request.url.port in {None, 443}
    if not simulation_enabled(request.url.hostname) or (is_demo and not is_secure_demo_origin):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security simulation is disabled for this environment, host, or transport",
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