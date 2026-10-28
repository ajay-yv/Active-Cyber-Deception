from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from tools.security_simulator import _format_response_summary, _print_extracted_patient, _print_marker_decoy_catalog
from app.services.decoy_catalog import (
    DECOY_CARD_FIELDS,
    get_attacker_decoy_catalog,
    get_public_decoy_catalog,
)
from app.core.simulation import validate_local_target
from app.main import app


client = TestClient(app)


def test_hacker_dashboard_summary_does_not_print_raw_payload() -> None:
    summary = _format_response_summary(
        {
            "role": "hacker",
            "metrics": {"synthetic_records": 3, "honeytokens": 2},
        }
    )

    assert summary == "Dashboard response received"
    assert "synthetic_records" not in summary
    assert "'role': 'hacker'" not in summary
    assert "hacker" not in summary.lower()


def test_public_decoy_catalog_uses_independent_fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_patient_catalog() -> list[dict]:
        raise AssertionError("public decoys must not read patient-derived catalog data")

    monkeypatch.setattr("app.services.decoy_catalog.get_admin_decoy_catalog", reject_patient_catalog)

    records = get_public_decoy_catalog()

    assert len(records) == 2
    assert all(record["is_synthetic"] for record in records)
    assert all("id" not in record and "patient_id" not in record for record in records)
    assert all(record["email"].endswith("@example.test") for record in records)


def login(username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_simulator_target_rejects_external_hosts() -> None:
    with pytest.raises(ValueError):
        validate_local_target("https://example.com")


def test_security_marker_is_detected_without_executing_input() -> None:
    token = login("hacker", "hacker123")
    admin_token = login("admin", "admin123")
    created_patient = client.post(
        "/api/patients",
        json={
            "name": f"Catalog Parity Test {uuid4().hex}",
            "age": 47,
            "disease": "Synthetic catalog parity condition",
            "diagnosis": "Synthetic catalog parity diagnosis",
        },
        headers={"Authorization": "Bearer " + admin_token},
    )
    assert created_patient.status_code == 200

    dashboard_response = client.get(
        "/api/dashboard/admin",
        headers={"Authorization": "Bearer " + admin_token},
    )
    assert dashboard_response.status_code == 200

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
    assert payload["event"]["attack_type"] == "SQL_INJECTION"
    assert payload["event"]["requested_fields"] == list(DECOY_CARD_FIELDS)
    assert payload["event"]["ip_address"] == "testclient"
    decoy_records = payload["deceptive_payload"]["synthetic_records"]
    dashboard_records = dashboard_response.json()["synthetic_records"]
    assert decoy_records == get_attacker_decoy_catalog()
    assert all(set(record) == {*DECOY_CARD_FIELDS, "is_synthetic"} for record in decoy_records)
    assert all("id" not in record and "patient_id" not in record for record in decoy_records)
    dashboard_decoys = [
        {
            field: record[field]
            for field in (*DECOY_CARD_FIELDS, "is_synthetic")
        }
        for record in dashboard_records
        if record.get("is_synthetic") is True
        and isinstance(record.get("synthetic_patient_id"), str)
        and record["synthetic_patient_id"].startswith("SYN-")
    ]
    assert decoy_records == dashboard_decoys


def test_simulator_refuses_to_print_non_synthetic_patient_data(capsys: pytest.CaptureFixture[str]) -> None:
    _print_extracted_patient(
        "[SIMULATED OUTPUT]:",
        {
            "patient_id": "P-01",
            "name": "Real Patient",
            "synthetic_patient_id": "SYN-01",
            "is_synthetic": False,
        },
    )

    output = capsys.readouterr().out
    assert "Real Patient" not in output
    assert "P-01" not in output
    assert "Refusing to display" in output


def test_simulator_prints_only_synthetic_catalog_identifier(capsys: pytest.CaptureFixture[str]) -> None:
    _print_extracted_patient(
        "[SIMULATED OUTPUT]:",
        {
            "patient_id": "P-01",
            "synthetic_patient_id": "SYN-01",
            "name": "Decoy Patient",
            "is_synthetic": True,
        },
    )

    output = capsys.readouterr().out
    assert "Patient ID:          P-01" in output
    assert "SYN-01" not in output
    assert "Record Checksum:" not in output


def test_marker_without_verified_decoy_suggests_updated_backend_port(capsys: pytest.CaptureFixture[str]) -> None:
    _print_marker_decoy_catalog(
        "[SIMULATED OUTPUT]:",
        {
            "deceptive_payload": {
                "is_synthetic": True,
                "synthetic_records": [],
            }
        },
    )

    output = capsys.readouterr().out
    assert "Admin Dashboard synthetic decoy catalog is empty" in output


def test_simulator_prints_all_admin_catalog_card_fields(capsys: pytest.CaptureFixture[str]) -> None:
    records = [
        {
            "synthetic_patient_id": "SYN-01",
            "name": "Synthetic Decoy One",
            "disease": "Demo Condition One",
            "diagnosis": "Demo Diagnosis One",
            "treatment_pattern": "Demo Treatment One",
            "age_range": "40-45 yrs",
            "phone_number": "555-0101",
            "aadhaar_number": "0000-0000-0001",
            "email": "decoy1@example.invalid",
            "watermark_fingerprint": "fingerprint-one",
            "is_synthetic": True,
        },
        {
            "synthetic_patient_id": "SYN-02",
            "name": "Synthetic Decoy Two",
            "disease": "Demo Condition Two",
            "diagnosis": "Demo Diagnosis Two",
            "treatment_pattern": "Demo Treatment Two",
            "age_range": "50-55 yrs",
            "phone_number": "555-0102",
            "aadhaar_number": "0000-0000-0002",
            "email": "decoy2@example.invalid",
            "watermark_fingerprint": "fingerprint-two",
            "is_synthetic": True,
        },
    ]
    _print_marker_decoy_catalog(
        "[SIMULATED OUTPUT]:",
        {"deceptive_payload": {"is_synthetic": True, "synthetic_records": records}},
    )

    output = capsys.readouterr().out
    assert "[SIMULATED OUTPUT]:" in output
    assert "Catalog" not in output
    assert "Patient 1 of 2" in output
    assert "Patient 2 of 2" in output
    assert "Patient ID:" in output
    assert "Synthetic Patient ID:" not in output
    assert "Treatment Pattern:" in output
    assert "Watermark Fingerprint:" not in output
    assert "fingerprint-one" not in output and "fingerprint-two" not in output
    assert "Patient ID:                 P-01" in output
    assert "Patient ID:                 P-02" in output
    assert "SYN-" not in output


def test_simulator_does_not_print_default_demo_fixtures(capsys: pytest.CaptureFixture[str]) -> None:
    _print_marker_decoy_catalog(
        "[SIMULATED OUTPUT]:",
        {
            "deceptive_payload": {
                "is_synthetic": True,
                "synthetic_records": [
                    {
                        "synthetic_patient_id": "SYN-DECOY-01",
                        "name": "Synthetic Patient Alpha",
                        "is_synthetic": True,
                    },
                    {
                        "synthetic_patient_id": "SYN-DECOY-02",
                        "name": "Synthetic Patient Beta",
                        "is_synthetic": True,
                    },
                ],
            }
        },
    )

    output = capsys.readouterr().out
    assert "Synthetic Patient Alpha" not in output
    assert "Synthetic Patient Beta" not in output
    assert "No persisted Admin Dashboard synthetic twins were returned" in output


def test_simulator_reads_persisted_patient_catalog_when_marker_is_legacy(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from argparse import Namespace
    from tools.security_simulator import run_attack

    catalog_record = {
        "id": "P-01",
        "patient_id": "P-01",
        "synthetic_patient_id": "SYN-P-01",
        "name": "Admin Catalog Decoy",
        "disease": "Synthetic condition",
        "diagnosis": "Synthetic diagnosis",
        "treatment_pattern": "Synthetic treatment",
        "age_range": "35-40 yrs",
        "phone_number": "555-0100",
        "aadhaar_number": "0000-0000-0001",
        "email": "decoy@example.invalid",
        "watermark_fingerprint": "catalog-fingerprint",
        "is_synthetic": True,
    }
    requested_paths: list[str] = []

    def fake_request(
        target: str,
        path: str,
        method: str = "GET",
        payload: dict | None = None,
        token: str | None = None,
        session_id: str = "sim-session",
    ) -> tuple[int, dict]:
        requested_paths.append(path)
        if path == "/api/security/simulation/marker":
            return 200, {
                "status": "detected",
                "deceptive_payload": {
                    "is_synthetic": True,
                    "synthetic_records": [
                        {
                            "synthetic_patient_id": "SYN-DECOY-01",
                            "name": "Synthetic Patient Alpha",
                            "is_synthetic": True,
                        }
                    ],
                },
            }
        if path == "/api/patients?limit=25":
            return 200, {"patients": [catalog_record]}
        return 200, {"status": "ok"}

    monkeypatch.setattr("tools.security_simulator.login", lambda _target: "test-token")
    monkeypatch.setattr("tools.security_simulator.request", fake_request)

    run_attack(
        Namespace(
            attack="sql-injection",
            target="http://127.0.0.1:8010",
            allow_private_network=False,
            session="legacy-marker-test",
            interval=0.05,
            count=None,
            attempts=None,
            requests=None,
            records=None,
        )
    )

    output = capsys.readouterr().out
    assert "/api/patients?limit=25" in requested_paths
    assert "Admin Catalog Decoy" in output
    assert "catalog-fingerprint" not in output
    assert "P-01" in output
    assert "Synthetic Patient Alpha" not in output
    assert "patient_id:" not in output


def test_enumeration_prints_persisted_admin_catalog(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from argparse import Namespace
    from tools.security_simulator import run_attack

    catalog_record = {
        "synthetic_patient_id": "SYN-P-42",
        "name": "Persisted Admin Twin",
        "disease": "Synthetic condition",
        "diagnosis": "Synthetic diagnosis",
        "treatment_pattern": "Synthetic treatment",
        "age_range": "35-40 yrs",
        "phone_number": "555-0142",
        "aadhaar_number": "0000-0000-0042",
        "email": "twin@example.invalid",
        "watermark_fingerprint": "must-not-print",
        "is_synthetic": True,
    }
    requested_paths: list[str] = []

    def fake_request(
        target: str,
        path: str,
        method: str = "GET",
        payload: dict | None = None,
        token: str | None = None,
        session_id: str = "sim-session",
    ) -> tuple[int, dict]:
        requested_paths.append(path)
        if path == "/api/patients?limit=25":
            return 200, {"patients": [catalog_record]}
        return 200, {"patient": None, "patients": []}

    monkeypatch.setattr("tools.security_simulator.login", lambda _target: "test-token")
    monkeypatch.setattr("tools.security_simulator.request", fake_request)

    run_attack(
        Namespace(
            attack="enumeration",
            target="http://127.0.0.1:8010",
            allow_private_network=False,
            session="enumeration-catalog-test",
            interval=0.05,
            count=2,
            attempts=None,
            requests=None,
            records=None,
        )
    )

    output = capsys.readouterr().out
    assert "/api/patients?limit=25" in requested_paths
    assert "Persisted Admin Twin" in output
    assert "[HACKER RECEIVED ENUMERATION DECOY CATALOG]:" not in output
    assert "Synthetic Patient ID:" not in output
    assert "must-not-print" not in output
    assert "P-42" in output


def test_api_abuse_prints_persisted_admin_catalog(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from argparse import Namespace
    from tools.security_simulator import run_attack

    catalog_record = {
        "synthetic_patient_id": "SYN-P-43",
        "name": "API Abuse Demo Twin",
        "disease": "Synthetic condition",
        "diagnosis": "Synthetic diagnosis",
        "treatment_pattern": "Synthetic treatment",
        "age_range": "35-40 yrs",
        "phone_number": "555-0143",
        "aadhaar_number": "0000-0000-0043",
        "email": "twin@example.invalid",
        "watermark_fingerprint": "must-not-print",
        "is_synthetic": True,
    }
    requested_paths: list[str] = []

    def fake_request(
        target: str,
        path: str,
        method: str = "GET",
        payload: dict | None = None,
        token: str | None = None,
        session_id: str = "sim-session",
    ) -> tuple[int, dict]:
        requested_paths.append(path)
        if path == "/api/patients?limit=25":
            return 200, {"patients": [catalog_record]}
        return 200, {"status": "ok"}

    monkeypatch.setattr("tools.security_simulator.login", lambda _target: "test-token")
    monkeypatch.setattr("tools.security_simulator.request", fake_request)

    run_attack(
        Namespace(
            attack="api-abuse",
            target="http://127.0.0.1:8010",
            allow_private_network=False,
            session="api-abuse-catalog-test",
            interval=0.05,
            count=None,
            attempts=None,
            requests=1,
            records=None,
        )
    )

    output = capsys.readouterr().out
    assert "/api/dashboard" in requested_paths
    assert "/api/patients?limit=25" in requested_paths
    assert "API Abuse Demo Twin" in output
    assert "must-not-print" not in output
    assert "P-43" in output


def test_simulator_omits_records_not_verified_synthetic(capsys: pytest.CaptureFixture[str]) -> None:
    _print_marker_decoy_catalog(
        "[SIMULATED OUTPUT]:",
        {
            "deceptive_payload": {
                "is_synthetic": True,
                "synthetic_records": [
                    {"name": "Not synthetic", "is_synthetic": False},
                    {"name": "Verified decoy", "is_synthetic": True, "synthetic_patient_id": "SYN-01"},
                ],
            }
        },
    )

    output = capsys.readouterr().out
    assert "Verified decoy" in output
    assert "Not synthetic" not in output


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