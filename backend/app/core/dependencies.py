from collections.abc import Callable
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.core.users import User, verify_password, hash_password
from app.repositories.user_repository import user_repository
from app.services.security import is_session_blocked, record_forensic_attack

bearer_scheme = HTTPBearer(auto_error=False)


def authenticate_user(username: str, password: str) -> User | None:
    record = user_repository.get_by_username(username)
    if record is None and "@" in username:
        record = user_repository.get_by_email(username)
    if record is None:
        return None
    if getattr(record, "is_blocked", False):
        return None
    if record and verify_password(password, record.password_hash):
        return User(username=record.username, password=record.password_hash, role=record.role, full_name=record.full_name, email=record.email)
    return None


def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")

    session_id = request.headers.get("x-session-id") or "unknown-session"
    ip_address = request.headers.get("x-forwarded-for", request.client.host if request.client else "127.0.0.1")
    user_agent = request.headers.get("user-agent", "")

    try:
        payload = decode_token(credentials.credentials)
        username = str(payload.get("sub", ""))
    except Exception as exc:
        record_forensic_attack(
            attack_type="SESSION_ABUSE",
            session_id=session_id,
            risk_score=90.0,
            gateway_decision="BLOCK",
            ip_address=ip_address,
            user_agent=user_agent,
            blocked_status=False,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token") from exc

    record = user_repository.get_by_username(username)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    if getattr(record, "is_blocked", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked")
    return User(username=record.username, password=record.password_hash, role=record.role, full_name=record.full_name, email=record.email)


def require_roles(*allowed_roles: str) -> Callable:
    def dependency(
        user: User = Depends(get_current_user),
        context: dict[str, str] = Depends(request_context_headers),
    ) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions")
        if is_session_blocked(context["session_id"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked session detected")
        return user

    return dependency


def require_roles_or_deceive(*allowed_roles: str) -> Callable:
    def dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        context: dict[str, str] = Depends(request_context_headers),
    ) -> User:
        if credentials is None:
            return User(
                username="unauthorized_guest",
                password="",
                role="guest",
                full_name="External Visitor / Attacker",
                email=None,
            )
        user = get_current_user(request, credentials)
        if user.role not in allowed_roles:
            return User(
                username=user.username,
                password="",
                role="guest",
                full_name=user.full_name,
                email=user.email,
            )
        if is_session_blocked(context["session_id"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked session detected")
        return user

    return dependency


def request_context_headers(
    session_id: str | None = Header(default=None, alias="X-Session-Id"),
    device: str = Header(default="trusted", alias="X-Device"),
    browser: str = Header(default="chrome", alias="X-Browser"),
    operating_system: str = Header(default="windows", alias="X-OS"),
    ip_address: str = Header(default="0.0.0.0", alias="X-Forwarded-For"),
    country: str = Header(default="unknown", alias="X-Country"),
) -> dict[str, str]:
    if not session_id:
        session_id = f"anonymous-{uuid4().hex[:8]}"

    return {
        "session_id": session_id,
        "device": device,
        "browser": browser,
        "operating_system": operating_system,
        "ip_address": ip_address,
        "country": country,
    }
