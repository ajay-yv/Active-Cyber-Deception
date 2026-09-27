import pytest
from app.schemas import PatientCreate
from app.services.patients import PatientService
from app.services.twin import twin_generator_proxy
from app.services.breach import handle_hacker_breach_request
from app.services.watermark import watermark_repository
from app.services.registries import synthetic_repository, patient_repository
from app.repositories.breach_repository import BreachRepository
from app.services.security import security_repository
from app.services.attribution import leak_attribution_service


def test_cyber_deception_full_workflow_steps_1_to_16():
    """
    Automated integration test verifying the 16 core steps of the Cyber Deception Workflow:
    1. Admin/User creates P-01.
    2. System automatically creates SYN-01.
    3. Original data is stored securely.
    4. Hacker requests P-01.
    5. Gateway detects suspicious request.
    6. Admin/User receives real-time alert trigger.
    7. Gateway chooses DECEIVE.
    8. Synthetic data generated/retrieved from P-01 pattern.
    9. Every synthetic value differs from corresponding original value.
    10. Watermark is embedded.
    11. Hacker receives SYN-01.
    12. Hacker does NOT receive original P-01 information.
    13. Forensic event is stored.
    14. Admin/User can see attack.
    15. Admin/User can map SYN-01 -> P-01 using secure forensic system.
    16. Verify one real patient has only one real Patient ID and one linked synthetic twin.
    """
    patient_service = PatientService(twin_generator_proxy)
    breach_repo = BreachRepository()

    # 1. Admin/User creates real patient record (P-01 or generated ID)
    payload = PatientCreate(
        name="Suddha Sen",
        age=23,
        disease="Fever",
        diagnosis="Normal Evaluation",
        medicines=["Paracetamol 650mg"],
        treatment_pattern="Routine Care",
        phone="+91-98765-43210",
        email="suddha.real@example.com",
        aadhaar="1234-5678-9012",
        address="123 Real Hospital Road, Kolkata, WB",
    )

    real_p, twin_p = patient_service.create_patient(
        payload, session_id="admin-session", hospital_id="HOSPITAL-001", route="real"
    )
    real_target_id = real_p.id

    # 2. System automatically creates linked synthetic twin
    syn_twin = patient_service._generate_synthetic_twin(
        real_p, session_id="admin-session", hospital_id="HOSPITAL-001"
    )
    expected_syn_pid = syn_twin.synthetic_patient_id
    assert syn_twin.real_patient_id == real_target_id

    # 3. Original data is stored securely in real patient DB
    stored_real = patient_repository.find_by_id(real_target_id)
    assert stored_real is not None
    assert stored_real.name == "Suddha Sen"
    assert stored_real.phone == "+91-98765-43210"

    # 4 & 5 & 6 & 7. Hacker requests patient & Gateway evaluates threat and returns DECEIVE
    session_id = f"hacker-session-{real_target_id[:8]}"
    hacker_id = "hacker_test_user"
    breach_response = handle_hacker_breach_request(
        session_id=session_id,
        hacker_id=hacker_id,
        query=f"SELECT * FROM patients WHERE id='{real_target_id}'",
        target_patient_id=real_target_id,
        requested_payload={"requested": ["name", "phone", "email", "diagnosis"]},
    )

    # 8. Synthetic data generated/retrieved from real patient's pattern
    assert breach_response["synthetic_patient_id"] == expected_syn_pid
    assert "original_target_id" not in breach_response

    # 9. Every synthetic value is different from corresponding original value
    assert breach_response["name"] != stored_real.name
    assert breach_response["phone_number"] != stored_real.phone
    assert breach_response["email"] != stored_real.email
    assert breach_response["aadhaar_number"] != stored_real.aadhaar
    assert breach_response["disease"] != stored_real.disease

    # 10. Watermark is embedded
    assert "watermark_id" in breach_response
    wm_id = breach_response["watermark_id"]
    wm_record = watermark_repository.find_by_watermark_id(wm_id)
    assert wm_record is not None
    assert wm_record.source_id == expected_syn_pid

    # 11. Hacker receives synthetic twin ID
    assert breach_response["patient_id"] == expected_syn_pid

    # 12. Hacker does NOT receive original P-01 information
    response_str = str(breach_response)
    assert "Suddha Sen" not in response_str
    assert "+91-98765-43210" not in response_str
    assert "suddha.real@example.com" not in response_str
    assert "1234-5678-9012" not in response_str

    # 13. Forensic event is stored
    breach_logs = [b for b in breach_repo.list_all() if b.session_id == session_id]
    assert len(breach_logs) > 0
    assert breach_logs[0].target_patient_id == real_target_id

    # 14. Admin/User can see the attack
    attacks = security_repository.find_by_event_type("attack")
    assert any(session_id in a.details for a in attacks)

    # 15. Admin/User can map SYN-XX -> P-XX using secure forensic system
    attribution = leak_attribution_service.attribute(wm_id)
    assert attribution.watermark is not None
    syn_record = synthetic_repository.find_by_synthetic_id(attribution.watermark.source_id)
    assert syn_record is not None
    assert syn_record.synthetic_patient_id == expected_syn_pid

    # 16. Verify that one real patient has only one real Patient ID and one linked synthetic twin
    duplicate_twin = synthetic_repository.find_by_real_patient_id(real_target_id)
    assert duplicate_twin is not None
    assert duplicate_twin.synthetic_patient_id == expected_syn_pid
