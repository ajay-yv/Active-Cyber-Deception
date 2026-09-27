from collections import Counter

from app.repositories.ai_decision_repository import ai_decision_repository
from app.services.deception import deception_orchestrator
from app.services.registries import patient_repository, synthetic_repository
from app.services.security import security_repository
from app.services.watermark import watermark_repository


def build_patient_analytics() -> dict[str, int | dict[str, int] | float]:
    patients = patient_repository.list_all()
    synthetic_twins = synthetic_repository.list_all()
    diseases = Counter(patient.disease for patient in patients)
    age_groups = Counter(
        "18-35" if patient.age <= 35 else "36-55" if patient.age <= 55 else "56+" for patient in patients
    )
    total_patients = len(patients)
    total_synthetic_twins = len(synthetic_twins)
    twin_ratio = float(total_synthetic_twins) / total_patients if total_patients else 0.0

    return {
        "total_patients": total_patients,
        "total_synthetic_twins": total_synthetic_twins,
        "synthetic_to_real_ratio": round(twin_ratio, 2),
        "disease_distribution": dict(diseases),
        "age_ranges": dict(age_groups),
    }


def build_security_metrics() -> dict[str, int | float]:
    ai_decision_records = ai_decision_repository.list_all()
    ai_route_synthetic = sum(1 for record in ai_decision_records if record.route == "synthetic")
    average_threat_score = round(sum(record.score for record in ai_decision_records) / len(ai_decision_records), 2) if ai_decision_records else 0.0

    return {
        "total_attacks": len(security_repository.find_by_event_type("attack")),
        "total_audit_events": len(security_repository.find_by_event_type("audit")),
        "total_ai_decisions": len(security_repository.find_by_event_type("ai_decision")),
        "total_persisted_ai_decisions": len(ai_decision_records),
        "persisted_synthetic_routes": ai_route_synthetic,
        "average_ai_threat_score": average_threat_score,
        "total_session_blocks": len(security_repository.find_by_event_type("session_block")),
        "total_user_blocks": len(security_repository.find_by_event_type("user_block")),
        "total_watermarks": len(watermark_repository.list_all()),
        "active_deception_sessions": len(deception_orchestrator.status()),
    }
