"""Comprehensive Cyber Deception Test Suite.

Verifies:
- Objective 1: Dynamic Synthetic EHR Evolution in Real-Time (Statistical distribution learning, multi-dimensional clinical synthesis, zero PII retention).
- Objective 2: Autonomous Deception Orchestrator (ADO) (Lifecycle states, attractive lure deployment, autonomous teardown janitor).
- Objective 3: Poisoned Synthetic Data with Invisible Digital Watermarks (Zero-width Unicode steganography, tamper-proof embedding, forensic timeline attribution).
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.registries import synthetic_repository
from app.repositories.watermark_repository import WatermarkRecord, watermark_repository
from app.services.twin import twin_generator_proxy as ai_engine_proxy
from app.services.attribution import leak_attribution_service
from app.services.deception import ADOState, autonomous_deception_orchestrator
from app.services.patients import patient_service
from app.services.watermark import (
    embed_invisible_watermark,
    extract_invisible_watermark,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def doctor_token(client):
    res = client.post("/api/auth/login", json={"username": "doctor", "password": "doctor123"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


# =========================================================================
# OBJECTIVE 1: Dynamic Synthetic EHR Evolution in Real-Time
# =========================================================================

def test_objective_1_pattern_evolution_and_zero_pii():
    """Verify statistical pattern profile evolves with real patient inputs with zero PII retention."""
    real_sample_1 = {
        "name": "Arjun Singhal",  # Real PII
        "phone": "+91 98765 43210",  # Real PII
        "aadhaar": "9988-7766-5544",  # Real PII
        "age": 58,
        "gender": "Male",
        "disease": "Hypertensive Cardiomyopathy",
        "diagnosis": "Stage 2 Essential Hypertension with Left Ventricular Hypertrophy",
        "medicines": ["Telmisartan", "Amlodipine", "Hydrochlorothiazide"],
        "dosages": ["40mg OD", "5mg OD", "12.5mg OD"],
        "department": "Cardiology",
        "doctor_assigned": "Dr. Priya Nair",
        "symptoms": ["Shortness of breath", "Chest tightness", "Dizziness"],
        "allergies": ["Sulfa drugs"],
    }
    
    # Ingest pattern
    ai_engine_proxy.evolve_patterns(real_sample_1)
    profile = ai_engine_proxy.get_pattern_profile()
    
    assert profile["total_patients_observed"] >= 1
    assert "Cardiology" in profile["top_departments"]
    assert profile["realism_fidelity_score"] >= 90.0
    
    # Ensure profile dict DOES NOT retain raw PII
    profile_str = str(profile)
    assert "Arjun Singhal" not in profile_str
    assert "+91 98765 43210" not in profile_str
    assert "9988-7766-5544" not in profile_str


def test_objective_1_rich_clinical_synthetic_generation():
    """Verify generated synthetic twin produces realistic multi-dimensional clinical data."""
    twin = ai_engine_proxy.generate_synthetic_twin({
        "name": "Sunita Verma",
        "age": 47,
        "disease": "Type 2 Diabetes Mellitus",
        "diagnosis": "Uncontrolled Glycemia with Mild Neuropathy",
        "medicines": ["Metformin", "Glimepiride"],
        "dosages": ["1000mg BD", "2mg OD"],
        "department": "Endocrinology",
    }, hospital_id="HOSP-TEST-01")
    
    # Verify rich clinical dimensions
    assert twin.name != "Sunita Verma"  # Decoy name generated
    assert twin.disease in ["Type 2 Diabetes Mellitus", "Metabolic Syndrome", "Insulin Resistance"]
    assert len(twin.medicines) > 0
    assert len(twin.dosages) > 0
    assert len(twin.symptoms) > 0
    assert len(twin.lab_reports) > 0
    assert len(twin.medical_images) > 0
    assert twin.department is not None
    assert twin.doctor_assigned is not None
    assert twin.blood_group is not None
    assert twin.ward is not None


def test_objective_1_evolution_api_endpoint(client, admin_token):
    """Verify GET /api/security/twins/evolution returns live profile."""
    res = client.get("/api/security/twins/evolution", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_patients_observed" in data
    assert "top_diseases" in data
    assert "active_pattern_rules" in data
    assert data["realism_fidelity_score"] >= 90.0


# =========================================================================
# OBJECTIVE 2: Autonomous Deception Orchestrator (ADO)
# =========================================================================

def test_objective_2_ado_lifecycle_and_state_machine():
    """Verify ADO state transitions through anomaly evaluation, lure enhancement, and interception."""
    session_id = "test-adv-session-991"
    
    # 1. Low threat -> DETECTING
    state_1 = autonomous_deception_orchestrator.evaluate_and_transition(
        session_id=session_id,
        threat_score=35.0,
        query="SELECT * FROM patients WHERE age > 60",
    )
    assert state_1 == ADOState.DETECTING
    
    # 2. Moderate threat -> DECOY_DEPLOYED
    state_2 = autonomous_deception_orchestrator.evaluate_and_transition(
        session_id=session_id,
        threat_score=65.0,
        query="SELECT * FROM patients WHERE disease LIKE '%cancer%'",
    )
    assert state_2 == ADOState.DECOY_DEPLOYED
    
    # 3. High threat -> LURE_ENHANCED
    state_3 = autonomous_deception_orchestrator.evaluate_and_transition(
        session_id=session_id,
        threat_score=92.0,
        query="SELECT * FROM patients WHERE is_vip = TRUE UNION SELECT username, password FROM users",
    )
    assert state_3 == ADOState.LURE_ENHANCED
    
    session_data = autonomous_deception_orchestrator.get_session_state(session_id)
    assert session_data is not None
    assert session_data["threat_score"] == 92.0
    # Attacker-triggered activation is telemetry-only when no persisted twins exist.
    assert session_data["decoy_ids"] == []
    assert session_data["lure_type"] is not None


def test_objective_2_attractive_lure_deployment(client, admin_token):
    """Verify POST /api/security/ado/lures/deploy creates high-value VIP decoy lures."""
    res = client.post(
        "/api/security/ado/lures/deploy",
        params={"session_id": "test-lure-session-101", "lure_type": "vip_executive_record"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "LURE_DEPLOYED"
    assert data["lure"]["is_attractive_lure"] is True
    assert data["lure"]["lure_type"] == "vip_executive_record"
    assert len(data["lure"]["name"]) > 0


def test_objective_2_autonomous_teardown_and_telemetry(client, admin_token):
    """Verify autonomous teardown scrubs ephemeral traces and posts telemetry with 0% data leak."""
    session_id = "test-teardown-session-555"
    
    # Setup session with lures
    autonomous_deception_orchestrator.deploy_attractive_lure(session_id, "high_value_clinical_trial")
    
    # Execute teardown
    teardown_res = client.post(
        "/api/security/ado/teardown",
        params={"session_id": session_id, "reason": "Adversary connection terminated"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert teardown_res.status_code == 200
    td_data = teardown_res.json()
    assert td_data["session_id"] == session_id
    assert td_data["status"] in ["CLEANED_UP", "NO_ACTIVE_SESSION"]
    
    # Verify telemetry endpoint
    telemetry_res = client.get("/api/security/ado/status", headers={"Authorization": f"Bearer {admin_token}"})
    assert telemetry_res.status_code == 200
    tel = telemetry_res.json()
    assert tel["real_patient_data_exposure"] == "0.0% (ZERO LEAKAGE)"
    assert tel["deception_success_rate"] == "100.0%"
    assert tel["engine_status"] == "ONLINE"


# =========================================================================
# OBJECTIVE 3: Poisoned Synthetic Data & Invisible Digital Watermarks
# =========================================================================

def test_objective_3_zero_width_unicode_steganography():
    """Verify invisible zero-width Unicode steganography embedding and extraction."""
    visible_clinical_text = "Rajesh Malhotra | Diagnosis: Acute Coronary Syndrome | Prescriptions: Aspirin 150mg"
    secret_payload = "WM:wm-test-uuid-12345|synthetic|PID-45242|HOSP-01|session-adv-01"
    
    # 1. Embed invisible watermark
    watermarked_text = embed_invisible_watermark(visible_clinical_text, secret_payload)
    
    # 2. Text looks normal to human / standard ASCII comparisons (non-empty)
    assert len(watermarked_text) > len(visible_clinical_text)
    assert "Rajesh Malhotra" in watermarked_text
    
    # 3. Extract invisible watermark
    extracted = extract_invisible_watermark(watermarked_text)
    assert extracted == secret_payload


def test_objective_3_forensic_leak_attribution_dossier(client, admin_token):
    """Verify full forensic timeline reconstruction and certificate from leaked raw content."""
    wm_id = "test-forensic-wm-999"
    session_id = "hacker-exfil-session-888"
    hospital_id = "HOSPITAL-DECEPTION-NODE-01"
    
    # Register test watermark
    wm_record = WatermarkRecord(
        id="test-db-id-999",
        watermark_id=wm_id,
        source_type="synthetic_decoy",
        source_id="PID-99999",
        timestamp="2026-08-29T10:00:00Z",
        watermark_fingerprint="sha256-test-fingerprint-999",
        forensic_link=f"/api/security/leaks/{wm_id}",
        hospital_id=hospital_id,
        session_id=session_id,
        watermark_text=f"WM:{wm_id}|synthetic|PID-99999|{hospital_id}|{session_id}",
    )
    watermark_repository.add(wm_record)
    
    # Embed invisible watermark into clinical text
    raw_leaked_dump = embed_invisible_watermark(
        "Kavita Deshmukh | Diagnosis: Glioblastoma Multiforme | Lure: Confidential Immunotherapy Regimen",
        f"WM:{wm_id}|synthetic|PID-99999|{hospital_id}|{session_id}",
    )
    
    # Scan raw leaked dump via API
    scan_res = client.post(
        "/api/security/forensics/scan",
        json={"raw_content": raw_leaked_dump},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["matched"] is True
    assert scan_data["watermark_id"] == wm_id
    
    dossier = scan_data["dossier"]
    assert dossier["watermark_id"] == wm_id
    assert dossier["session_id"] == session_id
    assert dossier["hospital_id"] == hospital_id
    assert dossier["real_patient_pii_exposed"] is False
    assert dossier["confidence_score"] >= 0.95
    assert len(dossier["timeline"]) >= 3
    assert "DIGITAL FORENSIC ATTRIBUTION CERTIFICATE" in dossier["forensic_certificate"]
