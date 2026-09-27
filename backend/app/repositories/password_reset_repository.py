from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.db.engines import SecuritySessionLocal
from app.models.security import PasswordResetToken


@dataclass(frozen=True)
class PasswordResetTokenRecord:
    id: str
    username: str
    email: str
    token_hash: str
    expires_at: str
    used: bool
    created_at: str


class PasswordResetRepository:
    def __init__(self) -> None:
        self._session_factory = SecuritySessionLocal

    def create_token(self, username: str, email: str, token_hash: str, expires_at: datetime) -> PasswordResetTokenRecord:
        record = PasswordResetToken(
            id=str(uuid4()),
            username=username,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False,
        )
        with self._session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
        return PasswordResetTokenRecord(
            id=record.id,
            username=record.username,
            email=record.email,
            token_hash=record.token_hash,
            expires_at=record.expires_at,
            used=bool(record.used),
            created_at=record.created_at,
        )

    def verify_token(self, token_hash: str) -> PasswordResetTokenRecord | None:
        now = datetime.now(timezone.utc)
        with self._session_factory() as session:
            row = (
                session.query(PasswordResetToken)
                .filter(PasswordResetToken.token_hash == token_hash)
                .filter(PasswordResetToken.used == False)
                .first()
            )
            if row is None:
                return None
            expires_at = row.expires_at if isinstance(row.expires_at, datetime) else datetime.fromisoformat(str(row.expires_at))
            if expires_at < now:
                return None
            return PasswordResetTokenRecord(
                id=row.id,
                username=row.username,
                email=row.email,
                token_hash=row.token_hash,
                expires_at=expires_at.isoformat(),
                used=bool(row.used),
                created_at=row.created_at.isoformat() if isinstance(row.created_at, datetime) else str(row.created_at),
            )

    def mark_used(self, token_id: str) -> bool:
        with self._session_factory() as session:
            row = session.query(PasswordResetToken).filter(PasswordResetToken.id == token_id).first()
            if row is None or row.used:
                return False
            row.used = True
            session.add(row)
            session.commit()
        return True


password_reset_repository = PasswordResetRepository()
