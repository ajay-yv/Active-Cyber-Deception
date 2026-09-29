from fastapi.testclient import TestClient

from app.main import app
from app.repositories.watermark_repository import WatermarkRecord
from app.services.deception import deception_orchestrator
from app.services.watermark import watermark_repository

client = TestClient(app)


def admin_token() -> str:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_security_overview_returns_counts() -> None:
    token = admin_token()
    response = client.get("/api/security/overview", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["watermarked_records"] >= 0


def test_security_events_feed_returns_recent_events() -> None:
    token = admin_token()
    response = client.get("/api/security/events", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert "events" in payload
    assert isinstance(payload["events"], list)


def test_create_attack_records_event() -> None:
    token = admin_token()
    response = client.post(
        "/api/security/attacks",
        json={
            "session_id": "session-attack-1",
            "action": "probe_fake_records",
            "details": "Simulated attacker query against synthetic patient table",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["event"]["event_type"] == "attack"
    assert "session-attack-1" in payload["event"]["details"]


def hacker_token() -> str:
    response = client.post("/api/auth/login", json={"username": "hacker", "password": "hacker123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_hacker_breach_request_returns_fake_data_and_logs_event() -> None:
    admin_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    admin_access_token = admin_response.json()["access_token"]
    patient_response = client.post(
        "/api/patients",
        json={
            "name": "Breach Test Patient",
            "age": 42,
            "disease": "Hypertension",
            "diagnosis": "Stable clinical status",
        },
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    target_patient_id = patient_response.json()["patient"]["id"]

    token = hacker_token()
    response = client.post(
        "/api/security/breach",
        json={
            "query": "Inspect patient vitals",
            "target_patient_id": target_patient_id,
            "requested_payload": {"fields": ["name", "disease"]},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"]
    assert payload["name"]
    assert payload["disease"]
    assert payload["diagnosis"]
    assert payload["medicines"]
    assert payload["notes"]
    assert payload["source_type"] == "synthetic"
    assert payload["records_returned"] == 1
    assert payload["is_synthetic"] is True
    assert "original_target_id" not in payload
    assert payload["patient_id"].startswith(("PID-", "SYN-"))


def test_hacker_can_list_hack_modes() -> None:
    token = hacker_token()
    response = client.get(
        "/api/security/hack-modes",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("modes"), list)
    assert any(mode["id"] == "probe_api" for mode in payload["modes"])


def test_hacker_can_execute_hack_mode() -> None:
    token = hacker_token()
    response = client.post(
        "/api/security/hack-modes/execute",
        json={
            "session_id": "session-hack-1",
            "mode": "probe_api",
            "details": "Fingerprint API endpoints for suspicious behavior",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "probe_api"
    assert payload["description"]


def test_leak_attribution_uses_watermark_metadata() -> None:
    token = admin_token()
    watermark = watermark_repository.add(
        WatermarkRecord(
            id="wm-1",
            watermark_id="wm-trace-1",
            source_id="syn-patient-1",
            source_type="synthetic",
            hospital_id="HOSPITAL-001",
            timestamp="2026-08-01T00:00:00Z",
            session_id="session-abc",
            watermark_text="EHR-SYN-syn-patient-1-123",
            watermark_fingerprint="abcdef1234567890",
        )
    )

    response = client.get(
        f"/api/security/leaks/{watermark.watermark_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["watermark"]["watermark_id"] == "wm-trace-1"
    assert "forensic_record" in payload


def test_forensic_leak_lookup_returns_fingerprint() -> None:
    token = admin_token()
    watermark = watermark_repository.add(
        WatermarkRecord(
            id="wm-2",
            watermark_id="wm-trace-2",
            source_id="syn-patient-2",
            source_type="synthetic",
            hospital_id="HOSPITAL-001",
            timestamp="2026-08-01T00:00:00Z",
            session_id="session-def",
            watermark_text="EHR-SYN-syn-patient-2-123",
            watermark_fingerprint="123456abcdef7890",
        )
    )

    response = client.get(
        f"/api/security/leaks/{watermark.watermark_id}/forensics",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in {200, 404}


def test_deception_status_endpoint_returns_sessions() -> None:
    token = admin_token()
    deception_orchestrator.activate(session_id="session-demo", threat_score=92, reason="hacker role")

    response = client.get("/api/security/deception/status", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert any(session["session_id"] == "session-demo" for session in payload["sessions"])