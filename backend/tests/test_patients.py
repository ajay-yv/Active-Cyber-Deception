from app.api.patients import service
from app.db.bootstrap import create_all_tables
from app.schemas import PatientCreate

create_all_tables()


def test_create_patient_generates_synthetic_twin() -> None:
    patient, twin = service.create_patient(
        PatientCreate(
            name="Riya Sharma",
            age=34,
            disease="Diabetes",
            diagnosis="Type 2 diabetes",
            medicines=["Metformin"],
            treatment_pattern="Lifestyle + medication",
        )
    )

    assert patient.id
    assert patient.patient_id > 0
    assert patient.watermark_id
    assert patient.watermark_text.startswith("EHR-")
    assert patient.watermark_fingerprint
    assert twin.real_patient_id == patient.id
    assert twin.synthetic_patient_id.lower().startswith("syn-")
    assert "Diabetes" in twin.disease
    assert "type 2 diabetes" in twin.diagnosis.lower()
    assert len(twin.name) > 0
    assert twin.age_range
    assert twin.aadhaar_number
    assert twin.phone_number
    assert twin.email
    assert twin.watermark_fingerprint


def test_create_patient_assigns_unique_auto_incrementing_patient_id() -> None:
    first_patient, _ = service.create_patient(
        PatientCreate(
            name="Asha Patel",
            age=28,
            disease="Asthma",
            diagnosis="Mild asthma",
            medicines=["Inhaler"],
            treatment_pattern="Maintenance",
        )
    )
    second_patient, _ = service.create_patient(
        PatientCreate(
            name="Rahul Singh",
            age=42,
            disease="Hypertension",
            diagnosis="High blood pressure",
            medicines=["Beta blocker"],
            treatment_pattern="Lifestyle",
        )
    )

    assert first_patient.patient_id > 0
    assert second_patient.patient_id == first_patient.patient_id + 1


def test_update_patient_regenerates_synthetic_twin_with_new_identifiers() -> None:
    initial_patient, initial_twin = service.create_patient(
        PatientCreate(
            name="Nisha Rao",
            age=47,
            disease="Migraine",
            diagnosis="Acute headache disorder",
            medicines=["Sumatriptan"],
            treatment_pattern="Neurology follow-up",
        )
    )

    updated_patient, updated_twin = service.update_patient(
        initial_patient.id,
        PatientCreate(
            name="Nisha Rao Updated",
            age=48,
            disease="Migraine",
            diagnosis="Acute headache disorder",
            medicines=["Sumatriptan"],
            treatment_pattern="Neurology follow-up",
        ),
    )

    assert updated_patient.id == initial_patient.id
    assert updated_twin.real_patient_id == initial_patient.id
    assert updated_twin.name != initial_twin.name
    assert updated_twin.phone_number != initial_twin.phone_number
    assert updated_twin.email != initial_twin.email
    assert updated_twin.diagnosis.lower() == updated_patient.diagnosis.lower()
