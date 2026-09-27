from typing import TypedDict


class ExternalLabResult(TypedDict):
    patient_id: str
    test_name: str
    result: str
    reported_at: str


def fetch_lab_results(patient_id: str) -> ExternalLabResult:
    # Placeholder integration for a lab information system.
    return {
        "patient_id": patient_id,
        "test_name": "Complete Blood Count",
        "result": "Normal",
        "reported_at": "2026-08-01T00:00:00Z",
    }
