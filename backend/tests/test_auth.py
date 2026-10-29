from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4
from pathlib import Path

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.core.settings import Settings
from app.core import dependencies as dependency_module
from app.core.users import hash_password
from app.db.engines import SecuritySessionLocal
from app.main import app
from app.models.security import FailedLoginAttempt, UserAccount
from app.repositories.user_repository import UserRecord, user_repository
from app.schemas import PatientRecord
from app.services.registries import patient_repository
from app.services import security as security_service
from app.services.security import password_reset_store

client = TestClient(app)


def test_backend_settings_use_workspace_anchored_env_files() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    configured_files = Settings.model_config["env_file"]

    assert isinstance(configured_files, (tuple, list))
    env_files = tuple(Path(path) for path in configured_files)
    assert all(path.is_absolute() for path in env_files)
    assert workspace_root / ".env.local" in env_files


def test_smtp_settings_accept_documented_environment_variable_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user@example.org")
    monkeypatch.setenv("SMTP_PASSWORD", "private-password")
    monkeypatch.setenv("SMTP_FROM_ADDRESS", "portal@example.org")

    settings = Settings(_env_file=None)

    assert settings.smtp_user == "smtp-user@example.org"
    assert settings.smtp_pass == "private-password"
    assert settings.smtp_from == "portal@example.org"


def test_smtp_settings_keep_supporting_legacy_environment_variable_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SMTP_USER", "legacy-user@example.org")
    monkeypatch.setenv("SMTP_PASS", "legacy-password")
    monkeypatch.setenv("SMTP_FROM", "legacy-from@example.org")

    settings = Settings(_env_file=None)

    assert settings.smtp_user == "legacy-user@example.org"
    assert settings.smtp_pass == "legacy-password"
    assert settings.smtp_from == "legacy-from@example.org"


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


def test_password_reset_sends_email_otp_and_updates_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"reset-{uuid4().hex[:12]}"
    email = f"{username}@example.test"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="doctor",
        full_name="Reset Test Doctor",
        email=email,
    ))
    deliveries: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        auth_api,
        "send_otp_email",
        lambda destination, otp, name: deliveries.append((destination, otp, name)) or True,
    )

    try:
        response = client.post(
            "/api/auth/request-password-reset",
            json={"email": email.upper(), "username": username},
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["status"] == "success"
        assert "otp" not in payload
        assert deliveries == [(email, password_reset_store.get_otp(username), "Reset Test Doctor")]
        otp = deliveries[0][1]
        assert len(otp) == 6 and otp.isdigit()

        reset_response = client.post(
            "/api/auth/verify-reset-otp",
            json={
                "email": email,
                "username": username,
                "otp": otp,
                "new_password": "updated-password-123",
            },
        )
        assert reset_response.status_code == 200, reset_response.text
        assert reset_response.json()["status"] == "success"
        assert client.post(
            "/api/auth/login",
            json={"username": username, "password": "updated-password-123"},
        ).status_code == 200

        reused_otp_response = client.post(
            "/api/auth/verify-reset-otp",
            json={
                "email": email,
                "username": username,
                "otp": otp,
                "new_password": "another-password-123",
            },
        )
        assert reused_otp_response.status_code == 400
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_password_reset_requires_registered_contact_and_sends_sms_otp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"9{uuid4().int % 10**9:09d}"
    phone = f"+91{username}"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="patient",
        full_name="Reset Mobile Patient",
        email=f"{username}@patient.health",
        phone_number=phone,
    ))
    deliveries: list[tuple[str, str]] = []
    monkeypatch.setattr(
        auth_api,
        "send_otp_sms",
        lambda destination, otp: deliveries.append((destination, otp)) or True,
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_email",
        lambda *_: pytest.fail("A mobile reset must not send email"),
    )
    monkeypatch.setattr(
        auth_api,
        "get_settings",
        lambda: Settings(
            twilio_account_sid="AC-test",
            twilio_auth_token="test-token",
            twilio_from_number="+15005550006",
        ),
    )

    try:
        mismatch_response = client.post(
            "/api/auth/request-password-reset",
            json={"email": "+91" + f"{uuid4().int % 10**10:010d}", "username": username},
        )
        assert mismatch_response.status_code == 404
        assert not deliveries

        response = client.post(
            "/api/auth/request-password-reset",
            json={"email": username, "username": username},
        )
        assert response.status_code == 200, response.text
        assert deliveries == [(phone, password_reset_store.get_otp(username))]

        otp = deliveries[0][1]
        reset_response = client.post(
            "/api/auth/verify-reset-otp",
            json={
                "email": username,
                "username": username,
                "otp": otp,
                "new_password": "new-mobile-password-123",
            },
        )
        assert reset_response.status_code == 200, reset_response.text
        assert client.post(
            "/api/auth/login",
            json={"username": username, "password": "new-mobile-password-123"},
        ).status_code == 200
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_legacy_patient_mobile_reset_reports_missing_sms_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"8{uuid4().int % 10**9:09d}"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="patient",
        full_name="Unconfigured SMS Patient",
    ))
    monkeypatch.setattr(auth_api, "get_settings", lambda: Settings())
    monkeypatch.setattr(
        auth_api,
        "send_otp_sms",
        lambda *_: pytest.fail("SMS must not be attempted without configuration"),
    )

    try:
        response = client.post(
            "/api/auth/request-password-reset",
            json={"email": f"+91{username}", "username": username},
        )
        assert response.status_code == 503
        assert "TWILIO_ACCOUNT_SID" in response.json()["detail"]
        assert "TWILIO_AUTH_TOKEN" in response.json()["detail"]
        assert "TWILIO_FROM_NUMBER" in response.json()["detail"]
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_administrator_mobile_reset_requires_preconfigured_recovery_phone() -> None:
    username = f"admin-reset-{uuid4().hex[:12]}"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="administrator",
        full_name="Admin Without Recovery Phone",
        email=f"{username}@stjude.org",
    ))

    try:
        response = client.post(
            "/api/auth/request-password-reset",
            json={"email": "+919999999999", "username": username},
        )
        assert response.status_code == 503
        assert "TWILIO_ACCOUNT_SID" in response.json()["detail"]
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_administrator_can_reset_using_new_mobile_after_two_factor_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"admin-reset-{uuid4().hex[:12]}"
    email = f"{username}@stjude.org"
    mobile = f"+919{uuid4().int % 10**9:09d}"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="administrator",
        full_name="Admin Dual Verification Test",
        email=email,
    ))
    email_deliveries: list[tuple[str, str]] = []
    mobile_deliveries: list[tuple[str, str]] = []
    monkeypatch.setattr(
        auth_api,
        "get_settings",
        lambda: Settings(
            twilio_account_sid="AC-test",
            twilio_auth_token="test-token",
            twilio_from_number="+15005550006",
            smtp_user="smtp-test",
            smtp_pass="smtp-test-password",
        ),
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_email",
        lambda destination, otp, *_: email_deliveries.append((destination, otp)) or True,
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_sms",
        lambda destination, otp: mobile_deliveries.append((destination, otp)) or True,
    )

    try:
        request = client.post(
            "/api/auth/request-password-reset",
            json={
                "email": mobile,
                "username": username,
            },
        )
        assert request.status_code == 200, request.text
        assert request.json()["requires_registered_email_otp"] is True
        assert email_deliveries[0][0] == email
        assert mobile_deliveries[0][0] == mobile

        payload = {
            "email": mobile,
            "username": username,
            "otp": mobile_deliveries[0][1],
            "registered_email_otp": email_deliveries[0][1],
            "new_password": "updated-admin-password-123",
        }
        wrong_mobile_code = client.post(
            "/api/auth/verify-reset-otp",
            json={**payload, "otp": "000000" if mobile_deliveries[0][1] != "000000" else "000001"},
        )
        assert wrong_mobile_code.status_code == 400
        wrong_registered_email_code = client.post(
            "/api/auth/verify-reset-otp",
            json={
                **payload,
                "registered_email_otp": (
                    "000000" if email_deliveries[0][1] != "000000" else "000001"
                ),
            },
        )
        assert wrong_registered_email_code.status_code == 400

        reset = client.post("/api/auth/verify-reset-otp", json=payload)
        assert reset.status_code == 200, reset.text
        assert user_repository.get_by_username(username).phone_number == mobile
        assert client.post(
            "/api/auth/login",
            json={"username": username, "password": "updated-admin-password-123"},
        ).status_code == 200

        reused_codes = client.post("/api/auth/verify-reset-otp", json=payload)
        assert reused_codes.status_code == 400
    finally:
        password_reset_store.clear_reset_otps(username)
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_admin_recovery_can_verify_phone_shared_with_another_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"admin-shared-phone-{uuid4().hex[:12]}"
    patient_username = f"patient-shared-phone-{uuid4().hex[:12]}"
    email = f"{username}@stjude.org"
    mobile = f"+919{uuid4().int % 10**9:09d}"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="administrator",
        full_name="Admin Shared Phone Recovery Test",
        email=email,
    ))
    user_repository.create(UserRecord(
        username=patient_username,
        password_hash=hash_password("patient-password"),
        role="patient",
        full_name="Patient with Shared Phone",
        phone_number=mobile,
    ))
    email_deliveries: list[tuple[str, str]] = []
    mobile_deliveries: list[tuple[str, str]] = []
    monkeypatch.setattr(
        auth_api,
        "get_settings",
        lambda: Settings(
            twilio_account_sid="AC-test",
            twilio_auth_token="test-token",
            twilio_from_number="+15005550006",
            smtp_user="smtp-test",
            smtp_pass="smtp-test-password",
        ),
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_email",
        lambda destination, otp, *_: email_deliveries.append((destination, otp)) or True,
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_sms",
        lambda destination, otp: mobile_deliveries.append((destination, otp)) or True,
    )

    try:
        request = client.post(
            "/api/auth/request-password-reset",
            json={"email": mobile, "username": username},
        )
        assert request.status_code == 200, request.text
        assert {destination for destination, _ in email_deliveries} == {email}
        assert {destination for destination, _ in mobile_deliveries} == {mobile}

        reset = client.post(
            "/api/auth/verify-reset-otp",
            json={
                "email": mobile,
                "username": username,
                "otp": mobile_deliveries[0][1],
                "registered_email_otp": email_deliveries[0][1],
                "new_password": "updated-admin-password-123",
            },
        )
        assert reset.status_code == 200, reset.text
        assert user_repository.get_by_phone_number(mobile, username).username == username
        assert user_repository.get_by_phone_number(mobile, patient_username).username == patient_username
    finally:
        password_reset_store.clear_reset_otps(username)
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(
                UserAccount.username.in_([username, patient_username])
            ).delete(synchronize_session=False)
            session.commit()


def test_administrator_can_verify_new_email_and_update_account_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"admin-email-reset-{uuid4().hex[:12]}"
    registered_email = f"{username}@stjude.org"
    recovery_email = f"{uuid4().hex[:12]}@example.com"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="administrator",
        full_name="Admin Email Recovery Test",
        email=registered_email,
    ))
    deliveries: list[tuple[str, str]] = []
    monkeypatch.setattr(
        auth_api,
        "get_settings",
        lambda: Settings(smtp_user="smtp-test", smtp_pass="smtp-test-password"),
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_email",
        lambda destination, otp, *_: deliveries.append((destination, otp)) or True,
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_sms",
        lambda *_: pytest.fail("No phone was requested"),
    )

    try:
        request = client.post(
            "/api/auth/request-password-reset",
            json={
                "email": recovery_email,
                "username": username,
            },
        )
        assert request.status_code == 200, request.text
        assert request.json()["requires_registered_email_otp"] is True
        assert {destination for destination, _ in deliveries} == {
            registered_email,
            recovery_email,
        }

        payload = {
            "email": recovery_email,
            "username": username,
            "otp": next(code for destination, code in deliveries if destination == recovery_email),
            "registered_email_otp": next(code for destination, code in deliveries if destination == registered_email),
            "new_password": "updated-admin-password-123",
        }
        reset = client.post("/api/auth/verify-reset-otp", json=payload)
        assert reset.status_code == 200, reset.text
        updated = user_repository.get_by_username(username)
        assert updated.email == recovery_email
        assert client.post(
            "/api/auth/login",
            json={"username": username, "password": payload["new_password"]},
        ).status_code == 200
    finally:
        password_reset_store.clear_reset_otps(username)
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_new_admin_mobile_requires_sms_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"admin-contact-{uuid4().hex[:12]}"
    user_repository.create(UserRecord(
        username=username,
        password_hash=hash_password("old-password"),
        role="administrator",
        full_name="Admin Contact Verification Test",
        email=f"{username}@stjude.org",
    ))
    monkeypatch.setattr(
        auth_api,
        "send_otp_email",
        lambda *_: pytest.fail("No code should be sent before the registered email is verified"),
    )
    monkeypatch.setattr(
        auth_api,
        "send_otp_sms",
        lambda *_: pytest.fail("No code should be sent before the registered email is verified"),
    )

    try:
        response = client.post(
            "/api/auth/request-password-reset",
            json={
                "email": "+919876543210",
                "username": username,
            },
        )
        assert response.status_code == 503
        assert "TWILIO_ACCOUNT_SID" in response.json()["detail"]
    finally:
        password_reset_store.clear_reset_otps(username)
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_password_reset_does_not_report_success_when_delivery_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = f"admin-{uuid4().hex}@stjude.org"
    user_repository.create(UserRecord(
        username="reset-delivery-failure",
        password_hash=hash_password("old-password"),
        role="administrator",
        full_name="Reset Delivery Test",
        email=email,
    ))
    monkeypatch.setattr(auth_api, "send_otp_email", lambda *_: False)

    try:
        response = client.post(
            "/api/auth/request-password-reset",
            json={"email": email, "username": "reset-delivery-failure"},
        )
        assert response.status_code == 503
        assert password_reset_store.get_otp("reset-delivery-failure") is None
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(
                UserAccount.username == "reset-delivery-failure"
            ).delete()
            session.commit()


def test_login_with_incorrect_password_fails() -> None:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.parametrize("known_account", [False, True])
def test_failed_login_alert_uses_five_attempt_ip_username_threshold(
    known_account: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username = f"bruteforce-{uuid4().hex[:12]}"
    session_prefix = f"threshold-session-{uuid4().hex}"
    if known_account:
        user_repository.create(UserRecord(
            username=username,
            password_hash=hash_password("correct-password-for-test"),
            role="doctor",
            full_name="Brute Force Test",
        ))

    emitted_events: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        security_service,
        "publish_event",
        lambda event_type, payload: emitted_events.append((event_type, payload)),
    )

    other_username = f"other-{uuid4().hex[:12]}"
    for attempt in range(4):
        unrelated = client.post(
            "/api/auth/login",
            json={"username": other_username, "password": f"not-a-secret-{attempt}"},
            headers={"X-Session-Id": f"unrelated-session-{attempt}"},
        )
        assert unrelated.status_code == 401

        response = client.post(
            "/api/auth/login",
            json={
                "username": username.upper() if attempt == 3 else username,
                "password": f"wrong-password-{attempt}",
            },
            headers={
                "X-Session-Id": f"{session_prefix}-{attempt}",
                "X-Forwarded-For": "203.0.113.41",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"
        assert not any(event_type == "FAILED_LOGIN_THRESHOLD_REACHED" for event_type, _ in emitted_events)

    threshold_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "wrong-password-threshold"},
        headers={"X-Session-Id": f"{session_prefix}-final", "X-Forwarded-For": "203.0.113.41"},
    )
    assert threshold_response.status_code == 401
    assert threshold_response.json()["detail"] == "Invalid username or password"

    alerts = [
        payload for event_type, payload in emitted_events
        if event_type == "FAILED_LOGIN_THRESHOLD_REACHED"
    ]
    assert len(alerts) == 1
    assert alerts[0]["attempt_count"] == 5
    assert alerts[0]["threshold"] == 5
    assert alerts[0]["window_minutes"] == 5
    assert alerts[0]["attempted_username"] == username
    assert alerts[0]["ip_address"] != "203.0.113.41"
    assert "wrong-password" not in str(alerts[0])
    logged_attempts = [
        event.details
        for event in security_service.security_repository.find_by_event_type("login_failure")
        if f"session={session_prefix}-" in event.details
    ]
    assert len(logged_attempts) == 5
    assert all("wrong-password" not in details for details in logged_attempts)
    assert all("ip=testclient" in details for details in logged_attempts)

    for attempt in range(5):
        repeated_response = client.post(
            "/api/auth/login",
            json={"username": username, "password": f"wrong-password-repeat-{attempt}"},
            headers={"X-Session-Id": f"{session_prefix}-repeat"},
        )
        assert repeated_response.status_code == 401
    assert len([
        event for event in emitted_events
        if event[0] == "FAILED_LOGIN_THRESHOLD_REACHED"
    ]) == 2

    repeated_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "wrong-password-after-alert"},
        headers={"X-Session-Id": f"{session_prefix}-after-alert"},
    )
    assert repeated_response.status_code == 401
    assert len([
        event for event in emitted_events
        if event[0] == "FAILED_LOGIN_THRESHOLD_REACHED"
    ]) == 2


def test_failed_login_window_excludes_attempts_older_than_five_minutes() -> None:
    username = f"expired-window-{uuid4().hex}"
    ip_address = "198.51.100.77"
    old_attempt_time = datetime.now(timezone.utc) - timedelta(minutes=6)

    for _ in range(4):
        security_service.security_repository.record_failed_login(
            username=username,
            ip_address=ip_address,
            threshold=5,
            window=timedelta(minutes=5),
            now=old_attempt_time,
        )

    count, should_alert = security_service.security_repository.record_failed_login(
        username=username,
        ip_address=ip_address,
        threshold=5,
        window=timedelta(minutes=5),
    )

    assert count == 1
    assert not should_alert
    with SecuritySessionLocal() as session:
        remaining_attempts = session.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.ip_address == ip_address,
            FailedLoginAttempt.username_key_hash == sha256(username.casefold().encode("utf-8")).hexdigest(),
        ).count()
    assert remaining_attempts == 1


def test_forwarded_ip_is_used_only_for_configured_trusted_proxies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dependency_module,
        "get_settings",
        lambda: Settings(trusted_proxy_cidrs="10.0.0.0/8"),
    )
    dependency_module._trusted_proxy_networks.cache_clear()
    request = Request({
        "type": "http",
        "headers": [(b"x-forwarded-for", b"198.51.100.44, 10.2.3.4")],
        "client": ("10.0.0.5", 12345),
    })

    assert dependency_module._request_ip_address(request) == "198.51.100.44"


def test_google_sign_in_links_unique_email_and_scopes_patient_access(monkeypatch: pytest.MonkeyPatch) -> None:
    email = f"google-{uuid4().hex}@example.test"
    patient = _add_patient(email)
    other_patient = _add_patient(f"other-{uuid4().hex}@example.test", "Other Patient")
    uid = uuid4().hex
    monkeypatch.setattr(auth_api, "verify_google_id_token", lambda _: _google_claims(email.upper(), uid))

    response = client.post("/api/auth/google", json={"id_token": "firebase-id-token"})

    assert response.status_code == 200, response.text
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


def test_google_sign_in_uses_selected_verified_email_when_uid_has_stale_patient_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_email = f"old-{uuid4().hex}@example.test"
    selected_email = f"selected-{uuid4().hex}@example.test"
    old_patient = _add_patient(old_email, "Previously Linked Patient")
    selected_patient = _add_patient(selected_email, "Selected Email Patient")
    uid = uuid4().hex
    username = f"google:{uid}"
    user_repository.link_google_patient(
        firebase_uid=uid,
        patient_record_id=old_patient.id,
        email=old_email,
        full_name=old_patient.name,
        password_hash=hash_password("test-only-password"),
    )
    monkeypatch.setattr(
        auth_api,
        "verify_google_id_token",
        lambda _: _google_claims(selected_email.upper(), uid),
    )

    try:
        response = client.post("/api/auth/google", json={"id_token": "firebase-id-token"})

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["user"]["email"] == selected_email
        assert payload["user"]["patient_record_id"] == selected_patient.id
        assert user_repository.get_by_username(username).patient_record_id == selected_patient.id

        headers = {"Authorization": "Bearer " + payload["access_token"]}
        self_response = client.get("/api/patients/me", headers=headers)
        assert self_response.status_code == 200
        assert self_response.json()["patient"]["id"] == selected_patient.id
        assert client.get(f"/api/patients/{old_patient.id}", headers=headers).status_code == 404
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == username).delete()
            session.commit()


def test_google_sign_in_does_not_take_patient_record_linked_to_another_google_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = f"owned-{uuid4().hex}@example.test"
    patient = _add_patient(email, "Already Linked Patient")
    original_uid = uuid4().hex
    attempted_uid = uuid4().hex
    user_repository.link_google_patient(
        firebase_uid=original_uid,
        patient_record_id=patient.id,
        email=email,
        full_name=patient.name,
        password_hash=hash_password("test-only-password"),
    )
    monkeypatch.setattr(
        auth_api,
        "verify_google_id_token",
        lambda _: _google_claims(email, attempted_uid),
    )

    try:
        response = client.post("/api/auth/google", json={"id_token": "firebase-id-token"})

        assert response.status_code == 403
        assert "already linked to another Google account" in response.json()["detail"]
        assert user_repository.get_by_username(f"google:{original_uid}").patient_record_id == patient.id
        assert user_repository.get_by_username(f"google:{attempted_uid}") is None
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(
                UserAccount.username.in_([f"google:{original_uid}", f"google:{attempted_uid}"])
            ).delete(synchronize_session=False)
            session.commit()


def test_unlinked_patient_cannot_read_another_patients_record_but_staff_can() -> None:
    patient = _add_patient(f"scoped-{uuid4().hex}@example.test", "Scoped Patient")
    patient_login = client.post(
        "/api/auth/login",
        json={"username": "patient", "password": "Patient@1432"},
    )
    assert patient_login.status_code == 200
    patient_headers = {"Authorization": "Bearer " + patient_login.json()["access_token"]}

    assert client.get("/api/patients/me", headers=patient_headers).json()["patient"] is None
    assert client.get("/api/patients", headers=patient_headers).json()["patients"] == []
    assert client.get(f"/api/patients/{patient.id}", headers=patient_headers).status_code == 404
    assert client.get(f"/api/patients?patient_id={patient.id}", headers=patient_headers).status_code == 404

    for credentials in (
        {"username": "admin", "password": "Admin@8431"},
        {"username": "doctor", "password": "Priya@10"},
    ):
        staff_login = client.post("/api/auth/login", json=credentials)
        assert staff_login.status_code == 200
        staff_headers = {"Authorization": "Bearer " + staff_login.json()["access_token"]}
        response = client.get(f"/api/patients/{patient.id}", headers=staff_headers)
        assert response.status_code == 200
        assert response.json()["patient"]["name"] == "Scoped Patient"


def test_seeded_patient_account_reads_only_record_matching_its_email() -> None:
    patient_email = f"portal-{uuid4().hex}@example.test"
    patient = _add_patient(patient_email, "Portal Linked Patient")
    other_patient = _add_patient(f"other-{uuid4().hex}@example.test", "Unrelated Patient")
    original_account = user_repository.get_by_username("patient")
    assert original_account is not None
    user_repository.update_email("patient", patient_email)
    try:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "patient", "password": "Patient@1432"},
        )
        assert login_response.status_code == 200
        headers = {"Authorization": "Bearer " + login_response.json()["access_token"]}

        self_response = client.get("/api/patients/me", headers=headers)
        assert self_response.status_code == 200
        assert self_response.json()["patient"]["id"] == patient.id

        list_response = client.get("/api/patients", headers=headers)
        assert list_response.status_code == 200
        assert [record["id"] for record in list_response.json()["patients"]] == [patient.id]
        assert client.get(f"/api/patients/{other_patient.id}", headers=headers).status_code == 404
    finally:
        user_repository.update_email("patient", original_account.email or "patient@stjude.org")


def test_registered_patient_sign_in_loads_admin_record_by_email() -> None:
    email = f"registered-{uuid4().hex}@example.test"
    patient = _add_patient(email, "Admin Entered Patient")
    unrelated_patient = _add_patient(f"unrelated-{uuid4().hex}@example.test", "Unrelated Patient")
    mobile = f"9{uuid4().int % 10**9:09d}"

    registration = client.post(
        "/api/auth/register-patient",
        json={
            "mobile_number": mobile,
            "password": "registered-password",
            "full_name": "Registered Patient Name",
            "email": email.upper(),
        },
    )
    assert registration.status_code == 200
    assert registration.json()["user"]["username"] == mobile
    assert registration.json()["user"]["full_name"] == "Registered Patient Name"
    assert registration.json()["user"]["email"] == email

    try:
        login_response = client.post(
            "/api/auth/login",
            json={"username": mobile, "password": "registered-password"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["full_name"] == "Registered Patient Name"
        headers = {"Authorization": "Bearer " + login_response.json()["access_token"]}

        current_patient = client.get("/api/patients/me", headers=headers)
        assert current_patient.status_code == 200
        assert current_patient.json()["patient"]["id"] == patient.id
        assert client.get(f"/api/patients/{unrelated_patient.id}", headers=headers).status_code == 404

        generic_patient_login = client.post(
            "/api/auth/login",
            json={"username": "patient", "password": "Patient@1432"},
        )
        assert generic_patient_login.status_code == 200
    finally:
        with SecuritySessionLocal() as session:
            session.query(UserAccount).filter(UserAccount.username == mobile).delete()
            session.commit()


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
