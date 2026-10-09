from uuid import uuid4
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.core.settings import Settings
from app.main import app
from app.schemas import PatientRecord
from app.services.registries import patient_repository
from app.services.security import password_reset_store

client = TestClient(app)


def test_backend_settings_use_workspace_anchored_env_files() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    configured_files = Settings.Config.env_file

    assert isinstance(configured_files, (tuple, list))
    env_files = tuple(Path(path) for path in configured_files)
    assert all(path.is_absolute() for path in env_files)
    assert workspace_root / ".env.local" in env_files


def test_google_token_verification_uses_configured_project_without_revocation_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(firebase_project_id="patient-1d860")
    monkeypatch.setattr(auth_api, "get_settings", lambda: settings)
    received = {}

    def verify_firebase_token(token, project_id):
        received.update(token=token, project_id=project_id)
        return {"uid": "verified-user"}

    monkeypatch.setattr(auth_api, "_verify_firebase_token", verify_firebase_token)

    claims = auth_api.verify_google_id_token("firebase-id-token")

    assert claims["uid"] == "verified-user"
    assert received == {"token": "firebase-id-token", "project_id": "patient-1d860"}


def test_google_token_verification_distinguishes_invalid_tokens_from_backend_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(firebase_project_id="patient-1d860")
    monkeypatch.setattr(auth_api, "get_settings", lambda: settings)

    def invalid_token(*_, **__):
        raise ValueError("bad token")

    monkeypatch.setattr(auth_api, "_verify_firebase_token", invalid_token)
    with pytest.raises(HTTPException) as invalid_error:
        auth_api.verify_google_id_token("invalid")
    assert invalid_error.value.status_code == 401

    def unavailable_verifier(*_, **__):
        raise RuntimeError("credential details must not reach the client")

    monkeypatch.setattr(auth_api, "_verify_firebase_token", unavailable_verifier)
    with pytest.raises(HTTPException) as unavailable_error:
        auth_api.verify_google_id_token("token")
    assert unavailable_error.value.status_code == 503
    assert "credential details" not in unavailable_error.value.detail


def _add_patient(email: str, name: str = "Google Test Patient") -> PatientRecord:
    return patient_repository.add(
        PatientRecord(
            id=str(uuid4()),
            name=name,
            age=35,
            disease="Test condition",
            diagnosis="Google sign-in test record",
            email=email,
        )
    )


def _google_claims(email: str, uid: str) -> dict:
    return {
        "uid": uid,
        "sub": uid,
        "email": email,
        "email_verified": True,
        "name": "Verified Google Patient",
        "firebase": {"sign_in_provider": "google.com"},
    }


def test_login_and_me_returns_user_context() -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "Admin@8431"})

    assert response.status_code == 200
    token = response.json()["access_token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "administrator"


def test_request_email_verification_and_verify_otp_updates_email() -> None:
    login_response = client.post("/api/auth/login", json={"username": "admin", "password": "Admin@8431"})
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


def test_login_with_incorrect_password_fails() -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_google_sign_in_links_unique_email_and_scopes_patient_access(monkeypatch: pytest.MonkeyPatch) -> None:
    email = f"google-{uuid4().hex}@example.test"
    patient = _add_patient(email)
    other_patient = _add_patient(f"other-{uuid4().hex}@example.test", "Other Patient")
    uid = uuid4().hex
    monkeypatch.setattr(auth_api, "verify_google_id_token", lambda _: _google_claims(email.upper(), uid))

    response = client.post("/api/auth/google", json={"id_token": "firebase-id-token"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == email
    assert payload["user"]["patient_record_id"] == patient.id
    assert payload["user"]["auth_provider"] == "google"
    token = payload["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    self_response = client.get("/api/patients/me", headers=headers)
    assert self_response.status_code == 200
    assert self_response.json()["patient"]["id"] == patient.id
    list_response = client.get("/api/patients", headers=headers)
    assert list_response.status_code == 200
    assert [record["id"] for record in list_response.json()["patients"]] == [patient.id]
    assert client.get(f"/api/patients/{other_patient.id}", headers=headers).status_code == 404
    assert client.get(f"/api/patients?patient_id={other_patient.id}", headers=headers).status_code == 404
    assert client.get(f"/api/integration/lab-results/{patient.id}", headers=headers).status_code == 200
    assert client.get(f"/api/integration/lab-results/{other_patient.id}", headers=headers).status_code == 404

    repeat_response = client.post("/api/auth/google", json={"id_token": "firebase-id-token"})
    assert repeat_response.status_code == 200
    assert repeat_response.json()["user"]["username"] == payload["user"]["username"]
    assert repeat_response.json()["user"]["patient_record_id"] == patient.id


def test_google_sign_in_rejects_missing_or_ambiguous_patient_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    duplicate_email = f"duplicate-{uuid4().hex}@example.test"
    _add_patient(duplicate_email, "Duplicate Patient One")
    _add_patient(duplicate_email, "Duplicate Patient Two")
    unmatched_email = f"unmatched-{uuid4().hex}@example.test"

    for email in (unmatched_email, duplicate_email):
        uid = uuid4().hex
        monkeypatch.setattr(auth_api, "verify_google_id_token", lambda _, email=email, uid=uid: _google_claims(email, uid))
        response = client.post("/api/auth/google", json={"id_token": "firebase-id-token"})
        assert response.status_code == 403


@pytest.mark.parametrize(
    "claims",
    [
        {"uid": "unverified", "email": "patient@example.test", "email_verified": False, "firebase": {"sign_in_provider": "google.com"}},
        {"uid": "password-provider", "email": "patient@example.test", "email_verified": True, "firebase": {"sign_in_provider": "password"}},
    ],
)
def test_google_sign_in_rejects_unverified_or_non_google_identity(
    monkeypatch: pytest.MonkeyPatch,
    claims: dict,
) -> None:
    monkeypatch.setattr(auth_api, "verify_google_id_token", lambda _: claims)

    response = client.post("/api/auth/google", json={"id_token": "firebase-id-token"})

    assert response.status_code == 403
