from fastapi.testclient import TestClient

from app.main import app
from app.services.security import password_reset_store

client = TestClient(app)


def test_login_and_me_returns_user_context() -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    assert response.status_code == 200
    token = response.json()["access_token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "administrator"


def test_request_email_verification_and_verify_otp_updates_email() -> None:
    login_response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    new_email = "admin+verify@example.com"
    request_response = client.post(
        "/api/auth/request-email-verification",
        json={"email": new_email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert request_response.status_code == 200
    assert request_response.json()["status"] == "ok"

    otp = password_reset_store.get_otp(new_email, "verify_email")
    assert otp is not None

    verify_response = client.post(
        "/api/auth/verify-email-otp",
        json={"email": new_email, "otp": otp},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["status"] == "ok"

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == new_email


def test_request_password_reset_with_mobile_input_generates_mobile_otp_alias() -> None:
    response = client.post("/api/auth/request-password-reset", json={"email": "9876543210"})
    assert response.status_code == 200
    alias = "9876543210@mobile.health"
    otp = password_reset_store.get_otp(alias, "reset") or password_reset_store.get_otp("9876543210", "reset")
    assert otp is not None