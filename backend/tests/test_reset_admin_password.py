import pytest

from app.core.users import verify_password
from app.repositories.user_repository import UserRecord
from app import reset_admin_password as reset_command


def test_reset_admin_password_updates_hash_and_audits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    account = UserRecord(
        username="admin",
        password_hash="old-hash",
        role="administrator",
        full_name="System Administrator",
    )
    updated: list[tuple[str, str]] = []
    audits: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        reset_command.user_repository,
        "get_by_username",
        lambda username: account if username == "admin" else None,
    )
    monkeypatch.setattr(
        reset_command.user_repository,
        "update_password",
        lambda username, password_hash: updated.append((username, password_hash)) or True,
    )
    monkeypatch.setattr(
        reset_command,
        "record_audit",
        lambda *entry: audits.append(entry),
    )

    reset_command.reset_admin_password("admin", "new-secure-password")

    assert updated[0][0] == "admin"
    assert verify_password("new-secure-password", updated[0][1])
    assert audits == [
        (
            "admin",
            "reset_password",
            "administrator password reset via local operator command",
        )
    ]


@pytest.mark.parametrize(
    ("account", "password", "error"),
    [
        (None, "new-secure-password", "not found"),
        (
            UserRecord(
                username="patient",
                password_hash="old-hash",
                role="patient",
                full_name="Patient",
            ),
            "new-secure-password",
            "not found",
        ),
        (
            UserRecord(
                username="admin",
                password_hash="old-hash",
                role="administrator",
                full_name="Blocked Administrator",
                is_blocked=True,
            ),
            "new-secure-password",
            "blocked",
        ),
        (
            UserRecord(
                username="admin",
                password_hash="old-hash",
                role="administrator",
                full_name="System Administrator",
            ),
            "short",
            "between 8 and 128",
        ),
    ],
)
def test_reset_admin_password_rejects_invalid_request(
    monkeypatch: pytest.MonkeyPatch,
    account: UserRecord | None,
    password: str,
    error: str,
) -> None:
    monkeypatch.setattr(
        reset_command.user_repository,
        "get_by_username",
        lambda _username: account,
    )
    monkeypatch.setattr(
        reset_command.user_repository,
        "update_password",
        lambda *_: pytest.fail("invalid reset must not update the password"),
    )

    with pytest.raises(ValueError, match=error):
        reset_command.reset_admin_password("admin", password)
