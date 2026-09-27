from app.api.patients import service
from app.db.bootstrap import create_all_tables
from app.schemas import PatientCreate

create_all_tables()


def test_update_patient_refreshes_watermark_and_synthetic_twin() -> None:
    patient, twin = service.create_patient(
        PatientCreate(
            name="Anjali Rao",
            age=45,
            disease="Hypertension",
            diagnosis="Stage 1 hypertension",
            medicines=["Amlodipine"],
            treatment_pattern="Medication first",
        )
    )

    assert patient.watermark_id
    assert patient.watermark_text.startswith("EHR-")
    assert patient.watermark_fingerprint
    assert twin.real_patient_id == patient.id

    updated_payload = PatientCreate(
        name="Anjali Rao",
        age=46,
        disease="Hypertension",
        diagnosis="Stage 2 hypertension",
        medicines=["Amlodipine", "Losartan"],
        treatment_pattern="Medication and lifestyle",
    )

    updated_patient, updated_twin = service.update_patient(
        patient_id=patient.id,
        payload=updated_payload,
        session_id="session-test",
        hospital_id="HOSPITAL-001",
        route="real",
    )

    assert updated_patient.id == patient.id
    assert updated_patient.age == 46
    assert updated_patient.diagnosis == "Stage 2 hypertension"
    assert updated_patient.watermark_id
    assert updated_patient.watermark_text.startswith("EHR-")
    assert updated_patient.watermark_fingerprint != patient.watermark_fingerprint
    assert updated_twin.real_patient_id == patient.id
    assert "Hypertension" in updated_twin.disease
    assert "Losartan" in updated_twin.medicines
    assert updated_twin.watermark_fingerprint


def test_update_patient_raises_not_found_for_missing_record() -> None:
    missing_payload = PatientCreate(
        name="Unknown Patient",
        age=33,
        disease="Unknown",
        diagnosis="No diagnosis",
        medicines=["None"],
        treatment_pattern="None",
    )

    try:
        service.update_patient(
            patient_id="nonexistent-id",
            payload=missing_payload,
            session_id="session-test",
            hospital_id="HOSPITAL-001",
            route="real",
        )
        assert False, "Expected ValueError for missing patient id"
    except ValueError as exc:
        assert "Patient not found" in str(exc)
