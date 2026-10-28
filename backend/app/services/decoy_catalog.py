from app.repositories.synthetic_repository import serialize_catalog_twin
from app.services.registries import synthetic_repository


DECOY_CARD_FIELDS = (
    "synthetic_patient_id",
    "name",
    "disease",
    "diagnosis",
    "treatment_pattern",
    "medicines",
    "age_range",
    "phone_number",
    "aadhaar_number",
    "email",
    "address",
    "watermark_fingerprint",
)

_PUBLIC_DECOY_FIXTURES = (
    {
        "synthetic_patient_id": "SYN-DECOY-01",
        "name": "Synthetic Patient Alpha",
        "disease": "Hypertension",
        "diagnosis": "Synthetic cardiovascular follow-up",
        "treatment_pattern": "Routine monitoring",
        "medicines": ["Example Medication A"],
        "age_range": "45-60",
        "phone_number": "000-000-0000",
        "aadhaar_number": "0000-0000-0000",
        "email": "alpha@example.test",
        "address": "Example District, Synthetic State",
        "watermark_fingerprint": "SYNTHETIC-DECOY-ALPHA",
    },
    {
        "synthetic_patient_id": "SYN-DECOY-02",
        "name": "Synthetic Patient Beta",
        "disease": "Type 2 diabetes",
        "diagnosis": "Synthetic metabolic health review",
        "treatment_pattern": "Lifestyle review",
        "medicines": ["Example Medication B"],
        "age_range": "30-45",
        "phone_number": "000-000-0000",
        "aadhaar_number": "0000-0000-0000",
        "email": "beta@example.test",
        "address": "Example District, Synthetic State",
        "watermark_fingerprint": "SYNTHETIC-DECOY-BETA",
    },
)


def get_admin_decoy_catalog() -> list[dict]:
    """Return only twins created through patient workflows; never seed on catalog reads."""
    return [serialize_catalog_twin(twin) for twin in synthetic_repository.valid_catalog()]


def get_attacker_decoy_catalog() -> list[dict]:
    """Return Admin Dashboard decoy-card fields without real-patient linkage data."""
    return [
        {
            field: list(record[field]) if isinstance(record.get(field), list) else record.get(field)
            for field in DECOY_CARD_FIELDS
        }
        | {"is_synthetic": True}
        for record in get_admin_decoy_catalog()
        if record.get("is_synthetic") is True
        and isinstance(record.get("synthetic_patient_id"), str)
        and record["synthetic_patient_id"].startswith("SYN-")
    ]


def get_public_decoy_catalog() -> list[dict]:
    """Return decoy cards sourced only from independent synthetic fixtures."""
    return [
        {
            field: list(fixture[field]) if field == "medicines" else fixture[field]
            for field in DECOY_CARD_FIELDS
        }
        | {"is_synthetic": True}
        for fixture in _PUBLIC_DECOY_FIXTURES
    ]
