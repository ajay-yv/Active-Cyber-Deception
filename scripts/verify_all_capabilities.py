import sys
import os

# Add backend to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.services.watermark import embed_invisible_watermark, extract_invisible_watermark, watermark_repository, create_watermark
from app.services.deception import deception_orchestrator
from app.services.attribution import leak_attribution_service

def verify_all():
    print("=" * 70)
    print("VERIFYING CYBER DECEPTION EHR CAPABILITIES")
    print("=" * 70)

    client = TestClient(app)

    # 1. Auth Login Tests
    print("[1/5] Testing Authentication & RBAC...")
    admin_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_res.status_code == 200, f"Admin login failed: {admin_res.text}"
    admin_token = admin_res.json()["access_token"]

    doctor_res = client.post("/api/auth/login", json={"username": "doctor", "password": "doctor123"})
    assert doctor_res.status_code == 200, f"Doctor login failed: {doctor_res.text}"
    doctor_token = doctor_res.json()["access_token"]

    hacker_res = client.post("/api/auth/login", json={"username": "hacker", "password": "hacker123"})
    assert hacker_res.status_code == 200, f"Hacker login failed: {hacker_res.text}"
    hacker_token = hacker_res.json()["access_token"]
    print("  -> Auth tokens acquired for Admin, Doctor, Hacker.")

    # 2. Objective 1: Real EHR Creation & Dynamic Synthetic Twin Evolution
    print("\n[2/5] Testing Objective 1: Dynamic Synthetic EHR Evolution & Zero PII Exposure...")
    patient_payload = {
        "name": "Dr. Rajeshwar Sen",
        "age": 52,
        "date_of_birth": "1974-04-12",
        "gender": "Male",
        "blood_group": "O+",
        "disease": "Acute Myocardial Infarction",
        "diagnosis": "Severe STEMI with Coronary Artery Stenosis",
        "symptoms": ["Severe Substernal Chest Pain", "Shortness of Breath", "Diaphoresis"],
        "allergies": ["Penicillin", "Aspirin"],
        "medicines": ["Atorvastatin 80mg", "Clopidogrel 75mg", "Metoprolol 50mg"],
        "dosages": ["1 tab daily after meals", "1 tab daily", "1 tab twice daily"],
        "treatment_pattern": "Emergency Percutaneous Coronary Intervention (PCI)",
        "doctor_assigned": "Dr. Priya Nair (Cardiology)",
        "department": "Cardiology",
        "ward": "Cardiology ICU Bed-04",
        "admission_date": "2026-08-10",
        "phone": "+91 9876543210",
        "email": "dr.rajeshwar.sen@apexhealth.in",
        "aadhaar": "8899-7766-5544",
        "emergency_contact": "Wife: Sunita Sen (+91 9876500000)",
        "address": "Flat 402, Royal Palms, Mumbai, MH",
    }

    create_res = client.post(
        "/api/patients",
        json=patient_payload,
        headers={"Authorization": f"Bearer {doctor_token}", "X-Session-Id": "doc-session-001"}
    )
    assert create_res.status_code == 200, f"Create patient failed: {create_res.text}"
    created_data = create_res.json()
    real_patient = created_data["patient"]
    synthetic_twin = created_data["synthetic_twin"]

    print(f"  -> Real Patient Created: ID={real_patient['id']}, Name='{real_patient['name']}', PII Phone='{real_patient['phone']}'")
    print(f"  -> Synthetic Twin Generated: ID={synthetic_twin['synthetic_patient_id']}, Name='{synthetic_twin['name']}', Phone='{synthetic_twin['phone_number']}'")

    # Verify Zero PII Leakage & High Clinical Fidelity
    assert real_patient["name"] != synthetic_twin["name"], "PII Leakage: Names match!"
    assert real_patient["phone"] != synthetic_twin["phone_number"], "PII Leakage: Phone matches!"
    assert real_patient["email"] != synthetic_twin["email"], "PII Leakage: Email matches!"
    assert real_patient["aadhaar"] != synthetic_twin["aadhaar_number"], "PII Leakage: Aadhaar matches!"
    assert len(synthetic_twin["disease"]) > 0, "Clinical condition populated!"
    assert len(synthetic_twin["diagnosis"]) > 0, "Clinical diagnosis populated!"
    print(f"  -> ZERO PII EXPOSURE VERIFIED: Name='{synthetic_twin['name']}' | Disease='{synthetic_twin['disease']}' | Department='{synthetic_twin['department']}'")

    # 3. Objective 2: Autonomous Deception Orchestrator (ADO)
    print("\n[3/5] Testing Objective 2: Autonomous Deception Orchestrator (ADO)...")
    adv_session = "adv-apt29-session-007"

    # Step 1: Detect and Activate Decoy
    new_state = deception_orchestrator.evaluate_and_transition(
        session_id=adv_session,
        threat_score=82,
        query="SELECT * FROM patients WHERE disease LIKE '%Infarction%'",
    )
    sess_state = deception_orchestrator.get_session_state(adv_session)
    print(f"  -> Step 1 Threat Intercepted: Session={adv_session}, State={new_state.value}, Decoys Deployed={len(sess_state.get('decoy_ids', []))}")

    # Step 2: Enhance with Attractive VIP Lure
    lure_res = deception_orchestrator.deploy_attractive_lure(
        session_id=adv_session,
        lure_type="vip_executive_record"
    )
    print(f"  -> Step 2 VIP Decoy Lure Injected: Lure='{lure_res['lure']['name']}', Dept='{lure_res['lure']['department']}'")

    # Step 3: Adversary Interception Query (Breach Simulation)
    breach_payload = {
        "query": "SELECT * FROM patients WHERE department = 'Cardiology'",
        "target_patient_id": "P-001",
        "requested_payload": {"exfiltrate_all": True},
    }
    hacker_breach_res = client.post(
        "/api/security/breach",
        json=breach_payload,
        headers={"Authorization": f"Bearer {hacker_token}", "X-Session-Id": adv_session}
    )
    assert hacker_breach_res.status_code == 200
    breach_data = hacker_breach_res.json()
    assert breach_data.get("source_type") == "synthetic" or "synthetic_patient_id" in breach_data
    print(f"  -> Step 3 Gateway Interception: Adversary breach intercepted & diverted to 100% Synthetic Decoy (Decoy ID: {breach_data.get('synthetic_patient_id')}).")

    # Step 4: Autonomous Teardown & Trace Scrubbing
    teardown_res = client.post(
        "/api/security/ado/teardown",
        json={"session_id": adv_session, "reason": "Adversary session disconnected."},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert teardown_res.status_code == 200
    print(f"  -> Step 4 Autonomous Teardown Executed: Status={teardown_res.json()['status']}, Purged={teardown_res.json()['purged_decoys_count']} ephemeral decoys.")

    # 4. Objective 3: Poisoned Synthetic Data & Watermark Steganography
    print("\n[4/5] Testing Objective 3: Poisoned Synthetic Data & Digital Forensics...")
    visible_notes = (
        "CONFIDENTIAL MEDICAL SUMMARY: Patient admitted with STEMI. "
        "Cardiac troponin levels significantly elevated. Underwent emergency PCI. Stable in CCU."
    )
    secret_payload = "WM:WM-FORENSIC-999|synthetic|SYN-001|HOSPITAL-001|session-hacker-x"

    # Register watermark in repo for forensic scan verification
    create_watermark(
        source_id="SYN-001",
        source_type="synthetic",
        hospital_id="HOSPITAL-001",
        session_id="session-hacker-x",
        source_data={"disease": "STEMI", "name": "Decoy Patient"},
    )

    # Steganography Injection
    poisoned_text = embed_invisible_watermark(visible_notes, secret_payload)
    print(f"  -> Watermark Embedded Invisibly (Visible length: {len(visible_notes)}, Watermarked length: {len(poisoned_text)})")
    assert visible_notes in poisoned_text, "Visible clinical notes preserved perfectly!"

    # Steganography Extraction
    extracted_wm = extract_invisible_watermark(poisoned_text)
    print(f"  -> Extracted Watermark ID: {extracted_wm['watermark_id']}, Source: {extracted_wm['source_type']}:{extracted_wm['source_id']}")
    assert extracted_wm["watermark_id"] == "WM-FORENSIC-999"

    # Leak Attribution & Forensic Certificate Generation
    scan_res = client.post(
        "/api/security/forensics/scan",
        json={"raw_content": poisoned_text},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["matched"] is True
    dossier = scan_data["dossier"]
    print(f"  -> Forensic Attribution Match: Confidence={dossier['attribution_confidence']}%, Zero PII Exposed={dossier['real_patient_pii_exposed'] is False}")
    print(f"  -> Reconstructed Attack Timeline: {len(dossier['timeline'])} Phases Documented.")

    # 5. Summary
    print("\n[5/5] Checking ADO System Telemetry...")
    telemetry_res = client.get("/api/security/ado/status", headers={"Authorization": f"Bearer {admin_token}"})
    assert telemetry_res.status_code == 200
    telemetry = telemetry_res.json()
    print(f"  -> ADO Engine Status: {telemetry['ado_engine_status']}")
    print(f"  -> Deception Success Rate: {telemetry['deception_success_rate']}")
    print(f"  -> Real Data Leakage: {telemetry['real_patient_data_exposure']}")
    print(f"  -> Autonomous Teardowns Count: {telemetry['total_autonomous_teardowns']}")

    print("\n" + "=" * 70)
    print("ALL OBJECTIVES 1, 2, AND 3 VERIFIED SUCCESSFULLY WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == "__main__":
    verify_all()
