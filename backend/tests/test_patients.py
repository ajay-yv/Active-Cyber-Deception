from app.api.patients import service
from app.db.bootstrap import create_all_tables
from app.db.engines import SyntheticSessionLocal
from app.models.synthetic import Honeytoken, SyntheticReport, SyntheticPatient
from app.repositories.watermark_repository import watermark_repository
from app.schemas import PatientCreate
from app.services.registries import patient_repository, synthetic_repository

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


def test_delete_patient_removes_linked_synthetic_twin_and_watermark() -> None:
    patient, twin = service.create_patient(
        PatientCreate(
            name="Meera Shah",
            age=39,
            disease="Asthma",
            diagnosis="Moderate asthma",
            medicines=["Inhaler"],
            treatment_pattern="Maintenance",
        )
    )
    with SyntheticSessionLocal() as session:
        session.add(
            SyntheticReport(
                id=f"REPORT-{twin.synthetic_patient_id}",
                patient_id=twin.synthetic_patient_id,
                report_type="Lab",
                report_content="Synthetic report",
            )
        )
        session.add(
            Honeytoken(
                id=f"TOKEN-{twin.synthetic_patient_id}",
                token_type="email",
                value="synthetic@example.test",
                session_id="delete-patient-test",
                twin_id=twin.synthetic_patient_id,
            )
        )
        session.commit()

    deleted, generated_twin = service.delete_patient(patient.id, route="real")

    assert deleted is not None
    assert deleted.id == patient.id
    assert generated_twin is None
    assert patient_repository.find_by_id(patient.id) is None
    assert synthetic_repository.find_by_real_patient_id(patient.id) is None
    assert watermark_repository.find_by_source_id(twin.synthetic_patient_id, source_type="synthetic") is None
    with SyntheticSessionLocal() as session:
        assert session.query(SyntheticPatient).filter(SyntheticPatient.id == twin.synthetic_patient_id).first() is None
        assert session.query(SyntheticReport).filter(SyntheticReport.patient_id == twin.synthetic_patient_id).first() is None
        assert session.query(Honeytoken).filter(Honeytoken.twin_id == twin.synthetic_patient_id).first() is None
