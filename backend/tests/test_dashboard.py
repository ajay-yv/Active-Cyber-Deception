from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_hospital_dashboard_route_returns_metrics() -> None:
    token = login("doctor", "doctor123")
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
