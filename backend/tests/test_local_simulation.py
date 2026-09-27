import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.simulation import validate_local_target
from app.main import app


client = TestClient(app)


def login(username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_simulator_target_rejects_external_hosts() -> None:
    with pytest.raises(ValueError):
        validate_local_target("https://example.com")


def test_security_marker_is_detected_without_executing_input() -> None:
    token = login("hacker", "hacker123")
    response = client.post(
        "/api/security/simulation/marker",
        json={"marker": "TEST_SQL_INJECTION"},
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": "marker-test-session"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "detected"
    assert payload["marker"] == "TEST_SQL_INJECTION"
    assert "sql_injection_pattern" in payload["decision"]["reason"]
    assert payload["event"]["session_id"] == "marker-test-session"


def test_repeated_dummy_login_failures_are_recorded_and_blocked() -> None:
    session_id = "brute-force-test-session"
    for _ in range(25):
        response = client.post(
            "/api/auth/login",
            json={"username": "hacker", "password": "dummy-invalid-password"},
            headers={"X-Session-Id": session_id},
        )
        assert response.status_code == 401

    response = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {login('hacker', 'hacker123')}", "X-Session-Id": session_id},
    )
    assert response.status_code == 403


def test_realtime_socket_requires_a_defender_token() -> None:
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/realtime/ws"):
            pass


def test_realtime_socket_accepts_administrator_and_sends_snapshot() -> None:
    token = login("admin", "admin123")
    with client.websocket_connect(f"/api/realtime/ws?token={token}") as websocket:
        message = websocket.receive_json()

    assert message["type"] == "snapshot"
    assert isinstance(message["payload"]["events"], list)