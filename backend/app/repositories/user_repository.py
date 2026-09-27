from dataclasses import dataclass

from app.db.engines import SecuritySessionLocal
from app.models.security import UserAccount


def _normalize_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "none", "null"}
    if isinstance(value, int):
        return value != 0
    return bool(value)


@dataclass
class UserRecord:
    username: str
    password_hash: str
    role: str
    full_name: str
    email: str | None = None
    is_blocked: bool = False


class UserRepository:
    def get_by_username(self, username: str) -> UserRecord | None:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return None
            return UserRecord(
                username=row.username,
                password_hash=row.password_hash,
                role=row.role,
                full_name=row.full_name,
                email=row.email,
                is_blocked=_normalize_bool(getattr(row, "is_blocked", False)),
            )

    def create(self, record: UserRecord) -> UserRecord:
        with SecuritySessionLocal() as session:
            session.merge(UserAccount(username=record.username, password_hash=record.password_hash, role=record.role, full_name=record.full_name, email=record.email, is_blocked=record.is_blocked))
            session.commit()
        return record

    def update_password(self, username: str, new_hashed: str) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.password_hash = new_hashed
            session.add(row)
            session.commit()
        return True

    def update_email(self, username: str, new_email: str) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.email = new_email
            session.add(row)
            session.commit()
        return True

    def get_by_email(self, email: str) -> UserRecord | None:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.email == email).first()
            if row is None:
                return None
            return UserRecord(username=row.username, password_hash=row.password_hash, role=row.role, full_name=row.full_name, email=row.email, is_blocked=bool(getattr(row, 'is_blocked', False)))

    def set_block(self, username: str, blocked: bool) -> bool:
        with SecuritySessionLocal() as session:
            row = session.query(UserAccount).filter(UserAccount.username == username).first()
            if row is None:
                return False
            row.is_blocked = blocked
            session.add(row)
            session.commit()
        return True


user_repository = UserRepository()
