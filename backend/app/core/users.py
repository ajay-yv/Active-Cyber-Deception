from dataclasses import dataclass

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


@dataclass(frozen=True)
class User:
    username: str
    password: str
    role: str
    full_name: str
    email: str | None = None


# NOTE: User persistence is now handled via `user_repository` backed by the security database.
# The old in-memory USERS mapping is retained for compatibility only if needed.
USERS: dict[str, User] = {}
