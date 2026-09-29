"""Comprehensive integration test suite verifying all 15 cyber-range attack simulation requirements."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.security_extra import security_test_marker
from app.main import app
from app.services.registries import patient_repository, synthetic_repository
from app.services.security import reset_security_state, security_repository
from app.services.gateway import reset_gateway_state
from app.schemas import TwinRecord


client = TestClient(app)


def login(username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, f"Login failed for {username}: {response.text}"
    return response.json()["access_token"]


# Test 1: Brute-force simulation is detected
def test_01_brute_force_detected() -> None:
    session_id = "test-brute-force-session"
    for i in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"username": "hacker", "password": f"wrong-pass-{i}"},
            headers={"X-Session-Id": session_id},
        )
        assert resp.status_code == 401

    # Check forensic records for BRUTE_FORCE
    records = security_repository.list_forensic_records(limit=10)
    bf_records = [r for r in records if r["attack_type"] == "BRUTE_FORCE" and r["session_id"] == session_id]
    assert len(bf_records) >= 1
    assert max(r["risk_score"] for r in bf_records) >= 80


# Test 2: Enumeration is detected
def test_02_enumeration_detected() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-enum-session"

    # Query multiple patient IDs sequentially
    responses = []
    for i in range(1, 6):
        resp = client.get(
            f"/api/patients?patient_id=P-{i:02d}",
            headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
        )
        assert resp.status_code == 200
        responses.append(resp.json())

    # Verify forensic records log PATIENT_ENUMERATION
    records = security_repository.list_forensic_records(limit=20)
    enum_records = [r for r in records if r["attack_type"] == "PATIENT_ENUMERATION" and r["session_id"] == session_id]
    assert len(enum_records) >= 1
    assert enum_records[-1]["risk_score"] >= 65


# Test 3: API abuse is detected
def test_03_api_abuse_detected() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-api-abuse-session"

    for _ in range(12):
        resp = client.get(
            "/api/dashboard",
            headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
        )
        assert resp.status_code == 200

    records = security_repository.list_forensic_records(limit=20)
    abuse_records = [r for r in records if r["attack_type"] == "API_ABUSE" and r["session_id"] == session_id]
    assert len(abuse_records) >= 1


# Test 4: SQL-injection test marker is detected
def test_04_sql_injection_marker_detected() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-sqli-session"

    resp = client.post(
        "/api/security/simulation/marker",
        json={"marker": "TEST_SQL_INJECTION"},
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "detected"
    assert data["marker"] == "TEST_SQL_INJECTION"
    assert data["event"]["attack_type"] == "SQL_INJECTION"
    assert data["event"]["risk_score"] >= 90


# Test 5: Traversal test marker is detected
def test_05_traversal_marker_detected() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-traversal-session"

    resp = client.post(
        "/api/security/simulation/marker",
        json={"marker": "TEST_TRAVERSAL"},
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "detected"
    assert data["marker"] == "TEST_TRAVERSAL"
    assert data["event"]["attack_type"] == "DIRECTORY_TRAVERSAL"
    assert data["event"]["risk_score"] >= 85


# Test 6: Exfiltration behavior is detected
def test_06_exfiltration_behavior_detected() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-exfiltration-session"

    for _ in range(4):
        resp = client.get(
            "/api/patients?limit=25",
            headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
        )
        assert resp.status_code == 200

    records = security_repository.list_forensic_records(limit=20)
    exfil_records = [r for r in records if r["attack_type"] == "DATA_EXFILTRATION" and r["session_id"] == session_id]
    assert len(exfil_records) >= 1


# Test 7: Credential stuffing simulation is detected
def test_07_credential_stuffing_detected() -> None:
    session_id = "test-cred-stuff-session"
    usernames = ["user-alpha", "user-beta", "user-gamma", "user-delta"]
    for u in usernames:
        resp = client.post(
            "/api/auth/login",
            json={"username": u, "password": "wrong-password"},
            headers={"X-Session-Id": session_id},
        )
        assert resp.status_code == 401

    records = security_repository.list_forensic_records(limit=20)
    stuff_records = [r for r in records if r["attack_type"] == "CREDENTIAL_STUFFING" and r["session_id"] == session_id]
    assert len(stuff_records) >= 1
    assert stuff_records[0]["risk_score"] >= 85


# Test 8: Session abuse is detected
def test_08_session_abuse_detected() -> None:
    session_id = "test-session-abuse"
    resp = client.get(
        "/api/patients",
        headers={"Authorization": "Bearer invalid-test-token-xyz", "X-Session-Id": session_id},
    )
    assert resp.status_code == 401

    records = security_repository.list_forensic_records(limit=20)
    abuse_records = [r for r in records if r["attack_type"] == "SESSION_ABUSE" and r["session_id"] == session_id]
    assert len(abuse_records) >= 1


# Test 9: Admin receives real-time alerts
def test_09_admin_receives_realtime_alerts() -> None:
    admin_token = login("admin", "admin123")
    hacker_token = login("hacker", "hacker123")

    with client.websocket_connect(f"/api/realtime/ws?token={admin_token}") as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "snapshot"

        # Trigger marker attack from hacker
        marker_resp = client.post(
            "/api/security/simulation/marker",
            json={"marker": "TEST_SQL_INJECTION"},
            headers={"Authorization": f"Bearer {hacker_token}", "X-Session-Id": "ws-alert-session"},
        )
        assert marker_resp.status_code == 200

        # Receive WebSocket message
        received_alert = None
        for _ in range(5):
            msg = websocket.receive_json()
            if msg.get("type") in {"ATTACK_DETECTED", "THREAT_SCORE_UPDATED", "DECEPTION_STARTED"}:
                received_alert = msg
                break
        assert received_alert is not None
        assert received_alert["payload"]["attack_type"] == "SQL_INJECTION" or received_alert["payload"]["session_id"] == "ws-alert-session"


# Test 10: Suspicious requests receive synthetic data
def test_10_suspicious_requests_receive_synthetic_data() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-synthetic-recv-session"

    resp = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    patients = data.get("patients", [])
    assert len(patients) > 0
    # Every patient received by hacker must have is_synthetic True
    for p in patients:
        assert p.get("is_synthetic") is True


def test_hacker_output_matches_existing_admin_synthetic_twins_and_caps_count() -> None:
    twins = synthetic_repository.list_all()
    assert twins

    token = login("hacker", "hacker123")
    target_twin = twins[0]
    single_response = client.get(
        f"/api/patients?patient_id={target_twin.real_patient_id}",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": "test-exact-twin-session"},
    )
    assert single_response.status_code == 200
    returned_twin = single_response.json()["patient"]
    assert returned_twin["synthetic_patient_id"] == target_twin.synthetic_patient_id
    assert returned_twin["name"] == target_twin.name
    assert returned_twin["disease"] == target_twin.disease
    assert returned_twin["diagnosis"] == target_twin.diagnosis
    assert returned_twin["phone"] == target_twin.phone_number
    assert returned_twin["email"] == target_twin.email
    assert returned_twin["aadhaar"] == target_twin.aadhaar_number

    bulk_response = client.get(
        f"/api/patients?limit={len(twins) + 10}",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": "test-bounded-twin-session"},
    )
    assert bulk_response.status_code == 200
    returned_records = bulk_response.json()["patients"]
    assert len(returned_records) == len(twins)
    assert {record["synthetic_patient_id"] for record in returned_records} == {
        twin.synthetic_patient_id for twin in twins
    }

    missing_response = client.get(
        "/api/patients?patient_id=P-NO-PERSISTED-TWIN",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": "test-missing-twin-session"},
    )
    assert missing_response.status_code == 200
    assert missing_response.json()["patient"] is None
    assert missing_response.json()["patients"] == []


def test_malformed_persisted_synthetic_ids_are_excluded_from_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    valid = TwinRecord(
        real_patient_id="P-VALID",
        synthetic_patient_id="SYN-VALID",
        name="Persisted Twin",
        address="Address",
        phone_number="+1-555-0100",
        aadhaar_number="0000-0000-0000",
        email="twin@example.test",
        insurance_details="Insurance",
        emergency_contact="+1-555-0101",
        disease="Condition",
        diagnosis="Diagnosis",
    )
    malformed = valid.model_copy(update={"synthetic_patient_id": "SYN-01' OR 1=1 --"})
    monkeypatch.setattr(synthetic_repository, "list_all", lambda: [valid, malformed])

    assert [t.synthetic_patient_id for t in synthetic_repository.valid_catalog()] == ["SYN-VALID"]
    token = login("hacker", "hacker123")
    response = client.get(
        "/api/patients?limit=99",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": "test-malformed-catalog"},
    )
    assert response.status_code == 200
    records = response.json()["patients"]
    assert [record["synthetic_patient_id"] for record in records] == ["SYN-VALID"]


def test_dashboard_catalog_count_matches_hacker_bulk_output(monkeypatch: pytest.MonkeyPatch) -> None:
    valid = TwinRecord(
        real_patient_id="P-CATALOG",
        synthetic_patient_id="SYN-CATALOG",
        name="Catalog Twin",
        address="Address",
        phone_number="+1-555-0200",
        aadhaar_number="1111-1111-1111",
        email="catalog@example.test",
        insurance_details="Insurance",
        emergency_contact="+1-555-0201",
        disease="Condition",
        diagnosis="Diagnosis",
    )
    malformed = valid.model_copy(update={"synthetic_patient_id": "SYN-CATALOG UNION SELECT"})
    monkeypatch.setattr(synthetic_repository, "list_all", lambda: [valid, malformed])

    admin = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {login('admin', 'admin123')}"})
    hacker = client.get("/api/patients?limit=99", headers={"Authorization": f"Bearer {login('hacker', 'hacker123')}"})
    assert admin.status_code == 200
    assert hacker.status_code == 200
    assert admin.json()["metrics"]["synthetic_twins"] == len(admin.json()["synthetic_records"]) == len(hacker.json()["patients"])
    assert admin.json()["synthetic_records"][0]["synthetic_patient_id"] == "SYN-CATALOG"


def test_sqli_input_does_not_create_twin_or_emit_raw_synthetic_id() -> None:
    token = login("hacker", "hacker123")
    before = {t.synthetic_patient_id for t in synthetic_repository.list_all()}
    response = client.get(
        "/api/patients",
        params={"patient_id": "P-01' OR 1=1 --"},
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": "test-sqli-raw-id"},
    )
    assert response.status_code == 200
    after = {t.synthetic_patient_id for t in synthetic_repository.list_all()}
    assert after == before
    recent = security_repository.list_forensic_records(limit=1)[0]
    assert "P-01' OR 1=1 --" not in str(recent.get("synthetic_patient_id"))
    assert "SYN-P-01' OR 1=1 --" not in str(recent.get("synthetic_patient_id"))


def test_security_marker_uses_valid_catalog_only(monkeypatch: pytest.MonkeyPatch) -> None:
    valid = TwinRecord(
        real_patient_id="P-VALID",
        synthetic_patient_id="SYN-VALID",
        name="Valid Twin",
        address="Address",
        phone_number="+1-555-0100",
        aadhaar_number="0000-0000-0000",
        email="valid@example.test",
        insurance_details="Insurance",
        emergency_contact="+1-555-0101",
        disease="Condition",
        diagnosis="Diagnosis",
    )
    malformed = valid.model_copy(update={"synthetic_patient_id": "SYN-01' OR 1=1 --"})
    monkeypatch.setattr(synthetic_repository, "list_all", lambda: [malformed, valid])
    monkeypatch.setattr("app.api.security_extra.require_simulation_enabled", lambda: None)
    monkeypatch.setattr(
        "app.api.security_extra.evaluate_request",
        lambda **kwargs: SimpleNamespace(threat_score=90.0, attack_probability=90.0, action="deceive"),
    )
    monkeypatch.setattr("app.api.security_extra.record_forensic_attack", lambda **kwargs: {"ok": True})
    monkeypatch.setattr("app.repositories.watermark_repository.watermark_repository.find_by_source_id", lambda *_args, **_kwargs: None)

    response = security_test_marker(
        payload=SimpleNamespace(marker="TEST_SQL_INJECTION"),
        current_user=SimpleNamespace(role="hacker", username="hacker"),
        context={"session_id": "session-marker", "ip_address": "127.0.0.1", "browser": ""},
    )

    assert response["deceptive_payload"]["sample_decoy"]["synthetic_patient_id"] == "SYN-VALID"
    assert "OR 1=1" not in response["deceptive_payload"]["sample_decoy"]["synthetic_patient_id"]


def test_dashboard_alert_uses_unresolved_target_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.api.dashboard.security_repository.find_by_event_type",
        lambda _event_type: [SimpleNamespace(details="session=s1; query=SELECT * FROM synthetic; target=Patient Records")],
    )
    monkeypatch.setattr("app.api.dashboard.deception_orchestrator.status", lambda: [])

    alerts = __import__("app.api.dashboard", fromlist=["_build_alerts"])._build_alerts()

    assert alerts
    assert "UNRESOLVED_ATTACK_TARGET" in alerts[0]["message"]
    assert "SYN-DECOY-TWIN" not in alerts[0]["message"]


# Test 11: Real patient data is never returned to attacker sessions
def test_11_real_patient_data_never_returned_to_attacker() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-never-real-session"

    real_patients = patient_repository.list_all()
    real_names = {p.name for p in real_patients}
    real_phones = {p.phone for p in real_patients if p.phone}
    real_emails = {p.email for p in real_patients if p.email}

    resp = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp.status_code == 200
    returned_patients = resp.json().get("patients", [])

    for p in returned_patients:
        assert p.get("is_synthetic") is True
        assert p.get("name") not in real_names
        if p.get("phone"):
            assert p.get("phone") not in real_phones
        if p.get("email"):
            assert p.get("email") not in real_emails


# Test 12: Watermark is generated
def test_12_watermark_is_generated() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-watermark-gen-session"

    resp = client.get(
        "/api/patients?patient_id=P-01",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp.status_code == 200
    patient = resp.json().get("patient")
    assert patient is not None
    assert patient.get("watermark_id") is not None
    assert len(patient["watermark_id"]) >= 8


# Test 13: Forensic event is stored with all 15 fields
def test_13_forensic_event_is_stored() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-15fields-session"

    resp = client.get(
        "/api/patients?patient_id=P-02",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp.status_code == 200

    admin_token = login("admin", "admin123")
    records_resp = client.get(
        "/api/security/forensic-records?limit=10",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert records_resp.status_code == 200
    records = records_resp.json().get("records", [])
    assert len(records) > 0

    record = records[0]
    required_fields = [
        "attack_id",
        "attack_type",
        "patient_id",
        "synthetic_patient_id",
        "session_id",
        "username",
        "ip_address",
        "user_agent",
        "timestamp",
        "risk_score",
        "attack_probability",
        "gateway_decision",
        "watermark_id",
        "records_returned",
        "blocked_status",
    ]
    for field in required_fields:
        assert field in record, f"Missing required field {field} in forensic record"


# Test 14: One patient maps to one synthetic twin
def test_14_one_patient_maps_to_one_synthetic_twin() -> None:
    token = login("hacker", "hacker123")
    session_id = "test-1to1-twin-session"

    resp1 = client.get(
        "/api/patients?patient_id=P-01",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp1.status_code == 200
    twin1 = resp1.json()["patient"]

    resp2 = client.get(
        "/api/patients?patient_id=P-01",
        headers={"Authorization": f"Bearer {token}", "X-Session-Id": session_id},
    )
    assert resp2.status_code == 200
    twin2 = resp2.json()["patient"]

    # Must map deterministically to the same synthetic twin
    assert twin1["id"] == twin2["id"]
    assert twin1["name"] == twin2["name"]
    assert twin1["disease"] == twin2["disease"]
    assert twin1["phone"] == twin2["phone"]


# Test 15: Normal Admin/User requests continue to receive legitimate data
def test_15_normal_admin_and_user_requests_receive_legitimate_data() -> None:
    admin_token = login("admin", "admin123")
    doctor_token = login("doctor", "doctor123")
    session_id = "doctor-normal-session"

    resp = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {doctor_token}", "X-Session-Id": session_id},
    )
    assert resp.status_code == 200
    patients = resp.json().get("patients", [])
    if len(patients) == 0:
        create_resp = client.post(
            "/api/patients",
            json={
                "name": "Test Real Patient",
                "age": 40,
                "gender": "Female",
                "disease": "Hypertension",
                "diagnosis": "Stage 1 Essential Hypertension",
                "medicines": ["Amlodipine 5mg"],
                "dosages": ["1 OD"],
                "treatment_pattern": "Standard Care",
            },
            headers={"Authorization": f"Bearer {admin_token}", "X-Session-Id": "admin-seed-session"},
        )
        assert create_resp.status_code == 200
        resp = client.get(
            "/api/patients",
            headers={"Authorization": f"Bearer {doctor_token}", "X-Session-Id": session_id},
        )
        assert resp.status_code == 200
        patients = resp.json().get("patients", [])

    assert len(patients) > 0
    for p in patients:
        assert p.get("is_synthetic") is False

    resp_admin = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {admin_token}", "X-Session-Id": "admin-normal-session"},
    )
    assert resp_admin.status_code == 200
    patients_admin = resp_admin.json().get("patients", [])
    assert len(patients_admin) > 0
    for p in patients_admin:
        assert p.get("is_synthetic") is False
