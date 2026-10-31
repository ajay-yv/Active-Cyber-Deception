import argparse
import getpass
import sys

from app.core.users import hash_password
from app.repositories.user_repository import user_repository
from app.services.audit import record_audit


def reset_admin_password(username: str, new_password: str) -> None:
    if not 8 <= len(new_password) <= 128:
        raise ValueError("The password must be between 8 and 128 characters.")

    account = user_repository.get_by_username(username)
    if account is None or account.role != "administrator":
        raise ValueError("The specified administrator account was not found.")
    if account.is_blocked:
        raise ValueError("The specified administrator account is blocked.")

    if not user_repository.update_password(username, hash_password(new_password)):
        raise RuntimeError("The administrator password could not be updated.")

    record_audit(
        username,
        "reset_password",
        "administrator password reset via local operator command",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset an administrator password from the backend host."
    )
    parser.add_argument("username", help="username of the administrator account")
    args = parser.parse_args(argv)

    if not sys.stdin.isatty():
        parser.error("an interactive terminal is required")
    if input(f"Type RESET {args.username} to continue: ") != f"RESET {args.username}":
        parser.error("confirmation did not match")

    new_password = getpass.getpass("New password (input hidden): ")
    if new_password != getpass.getpass("Confirm new password: "):
        parser.error("passwords do not match")

    try:
        reset_admin_password(args.username, new_password)
    except ValueError as exc:
        parser.exit(1, f"Error: {exc}\n")

    print("Administrator password reset successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
