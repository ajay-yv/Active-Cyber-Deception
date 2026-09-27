"""Comprehensive integration test suite verifying all 15 cyber-range attack simulation requirements."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.registries import patient_repository
from app.services.security import reset_security_state, security_repository
from app.services.gateway import reset_gateway_state


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
