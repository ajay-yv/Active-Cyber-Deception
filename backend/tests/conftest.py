import os
import tempfile
from pathlib import Path
import pytest

# Direct all automated test database operations to an isolated temporary directory
TEST_DIR = Path(tempfile.gettempdir()) / "ehr_test_databases"
TEST_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DIR / 'test_real.db').as_posix()}"
os.environ["SYNTHETIC_DATABASE_URL"] = f"sqlite:///{(TEST_DIR / 'test_syn.db').as_posix()}"
os.environ["SECURITY_DATABASE_URL"] = f"sqlite:///{(TEST_DIR / 'test_sec.db').as_posix()}"

from app.db.bootstrap import create_all_tables
create_all_tables()

from app.repositories.user_repository import user_repository
from app.services.deception import deception_orchestrator
from app.services.gateway import reset_gateway_state
from app.services.security import reset_security_state


@pytest.fixture(autouse=True)
def reset_backend_test_state() -> None:
    """Reset shared backend state between tests to avoid cross-test session or user blocking."""
    reset_security_state()
    reset_gateway_state()
    deception_orchestrator.reset()
    for username in ["admin", "doctor", "reception", "hacker"]:
        user_repository.set_block(username, False)
    yield
    reset_security_state()
    reset_gateway_state()
    deception_orchestrator.reset()
    for username in ["admin", "doctor", "reception", "hacker"]:
        user_repository.set_block(username, False)
