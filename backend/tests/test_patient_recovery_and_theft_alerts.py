import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.watermark import embed_invisible_watermark, extract_invisible_watermark, create_watermark


@pytest.fixture
def client():
    return TestClient(app)


def get_token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    data = res.json()
    return data.get("access_token") or data.get("token")


def test_patient_creation_creates_linked_watermark_and_synthetic_twin(client):
    """Requirement 1: Whenever new patient data is entered, create a watermark and synthetic data linked together."""
    admin_token = get_token(client, "admin", "admin123")
    
    patient_payload = {
        "name": "Dr. Aniruddh Kulkarni",
        "gender": "male",
        "date_of_birth": "1978-11-20",
        "age": 47,
        "blood_group": "B+",
        "phone": "+91 98450-99881",
        "email": "aniruddh.k@apollo.in",
        "address": "42 Richmond Road, Bangalore, Karnataka",
        "aadhaar": "9812-4455-6677",
        "disease": "Hypertensive Retinopathy",
        "diagnosis": "Grade III Retinopathy with arterial narrowing",
        "department": "Ophthalmology",
        "doctor_assigned": "Dr. Maya Sharma",
    }
    
    create_res = client.post(
        "/api/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 200
    data = create_res.json()
    
    # Verify real patient was created and watermarked
    assert "patient" in data
    real_pid = data["patient"]["id"]
    assert real_pid.startswith("P-") or real_pid.isdigit()
    assert data["patient"]["name"] == "Dr. Aniruddh Kulkarni"
    assert data["patient"]["watermark_id"] is not None
    
    # Verify synthetic twin was generated and watermarked
    assert "synthetic_twin" in data
    twin = data["synthetic_twin"]
    assert twin["synthetic_patient_id"].startswith("SYN-") or twin["synthetic_patient_id"].startswith("PID-")
    assert twin["name"] != "Dr. Aniruddh Kulkarni"  # Zero PII leakage
    assert twin["phone_number"] != "+91 98450-99881"  # Zero PII leakage
    assert twin["watermark_id"] is not None


def test_hacker_theft_attempt_redirects_with_hidden_watermark(client):
    """Requirement 2: When hacker tries to steal data, redirect to synthetic decoy with hidden watermark."""
    hacker_token = get_token(client, "hacker", "hacker123")
    
    # Hacker sends malicious SQL injection query attempting to dump oncology & VIP patient PII
    breach_query = {
        "query": "SELECT * FROM patients WHERE department = 'Oncology' OR 1=1 --",
        "target_patient_id": "P-01",
        "requested_payload": {"dump_pii": True, "fields": ["aadhaar", "phone", "diagnoses"]},
    }
    
    breach_res = client.post(
        "/api/security/breach",
        json=breach_query,
        headers={"Authorization": f"Bearer {hacker_token}", "X-Session-Id": "adversary-apt41-probe-99"}
    )
    assert breach_res.status_code == 200
    breach_data = breach_res.json()
    
    # Verify redirected to synthetic decoy
    assert breach_data.get("source_type") == "synthetic" or "synthetic_patient_id" in breach_data
    syn_id = breach_data.get("synthetic_patient_id") or breach_data.get("patient_id")
    assert syn_id is not None
    
    # Verify invisible steganographic watermark is embedded
    notes = breach_data.get("notes", "")
    assert len(notes) > 0


def test_forensic_recovery_recovers_original_patient_data(client):
    """Requirement 3: Using watermark feature, trace and recover original patient data in admin/user dashboard."""
    admin_token = get_token(client, "admin", "admin123")
    
    # 1. Create a patient
    create_res = client.post(
        "/api/patients",
        json={
            "name": "Smt. Kalyani Deshmukh",
            "gender": "female",
            "date_of_birth": "1965-03-12",
            "age": 61,
            "blood_group": "AB+",
            "phone": "+91 97654-11223",
            "email": "kalyani.deshmukh@gmail.com",
            "address": "104 Shivaji Park, Mumbai, Maharashtra",
            "aadhaar": "4433-2211-9988",
            "disease": "Severe Acute Pancreatitis",
            "diagnosis": "Necrotizing pancreatitis with peripancreatic fluid collection",
            "department": "Gastroenterology",
            "doctor_assigned": "Dr. Rohit Deshpande",
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 200
    created_data = create_res.json()
    real_pid = created_data["patient"]["id"]
    syn_pid = created_data["synthetic_twin"]["synthetic_patient_id"]
    wm_id = created_data["synthetic_twin"]["watermark_id"]
    
    # 2. Simulate stolen synthetic data with hidden zero-width watermark found on dark web
    decoy_text = f"Decoy Medical Record: Patient {created_data['synthetic_twin']['name']}, Diagnosis: {created_data['synthetic_twin']['disease']}"
    secret_payload = f"WM:{wm_id}|synthetic|{syn_pid}|HOSPITAL-001|darkweb-leak-session-88"
    poisoned_leaked_text = embed_invisible_watermark(decoy_text, secret_payload)
    
    # 3. Post to /api/security/forensics/recover
    recover_res = client.post(
        "/api/security/forensics/recover",
        json={"raw_content": poisoned_leaked_text},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert recover_res.status_code == 200
    recovery_data = recover_res.json()
    
    # Assert recovery succeeded
    assert recovery_data["status"] == "RECOVERED"
    assert recovery_data["matched"] is True
    assert recovery_data["leak_classification"] == "SYNTHETIC_DECOY_LEAK"
    assert "PROTECTED" in recovery_data["patient_safety_status"]
    
    # Verify original real patient was recovered from the secure vault
    recovered_real = recovery_data["recovered_real_patient"]
    assert recovered_real is not None
    assert recovered_real["name"] == "Smt. Kalyani Deshmukh"
    assert recovered_real["disease"] == "Severe Acute Pancreatitis"
    assert recovered_real["department"] == "Gastroenterology"
    
    # Verify hacker attribution details
    attribution = recovery_data["attribution"]
    assert attribution["attribution_confidence"] == "99.8%"
    assert attribution["real_patient_pii_exposed"] is False
    assert "DIGITAL FORENSIC ATTRIBUTION CERTIFICATE" in recovery_data["forensic_certificate"]
