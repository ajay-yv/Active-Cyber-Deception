from fastapi.testclient import TestClient

from app.main import app
from app.services.decoy_catalog import get_admin_decoy_catalog
from app.services.registries import patient_repository, synthetic_repository

client = TestClient(app)


def login(username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_hospital_dashboard_route_returns_metrics() -> None:
    token = login("doctor", "Doctor@1432")
    response = client.get("/api/dashboard/hospital", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "hospital_user"
    assert isinstance(payload["metrics"]["total_patients"], int)
    assert payload["metrics"]["total_patients"] >= 0
    assert isinstance(payload["metrics"]["synthetic_twins"], int)
    assert payload["metrics"]["synthetic_twins"] >= 0


def test_hacker_dashboard_route_returns_deception_assets() -> None:
    token = login("hacker", "hacker123")
    response = client.get("/api/dashboard/hacker", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "hacker"
    assert isinstance(payload["metrics"]["honeytokens"], int)
    assert payload["metrics"]["honeytokens"] >= 0


def test_admin_decoy_catalog_does_not_create_twins_on_read(monkeypatch) -> None:
    def reject_patient_scan() -> list:
        raise AssertionError("Catalog reads must not scan or create twins for all patients")

    monkeypatch.setattr(patient_repository, "list_all", reject_patient_scan)
    monkeypatch.setattr(synthetic_repository, "valid_catalog", lambda: [])

    assert get_admin_decoy_catalog() == []
