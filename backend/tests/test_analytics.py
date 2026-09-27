from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _admin_token() -> str:
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_list_synthetic_returns_array() -> None:
    token = _admin_token()
    response = client.get("/api/analytics/synthetic", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert "synthetic" in payload
    assert isinstance(payload["synthetic"], list)


def test_analytics_summary_includes_patient_and_security_metrics() -> None:
    token = _admin_token()
    response = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert "patient_metrics" in payload
    assert "security_metrics" in payload
    assert payload["patient_metrics"]["total_patients"] >= 0
    assert payload["patient_metrics"]["total_synthetic_twins"] >= 0
    assert isinstance(payload["patient_metrics"]["synthetic_to_real_ratio"], float)
    assert payload["security_metrics"]["total_attacks"] >= 0
    assert payload["security_metrics"]["total_ai_decisions"] >= 0
    assert payload["security_metrics"]["active_deception_sessions"] >= 0
