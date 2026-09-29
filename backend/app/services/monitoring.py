from uuid import uuid4

from app.repositories.security_repository import SecurityRepository, SecurityEvent
from app.services.deception import deception_orchestrator
from app.services.realtime import publish_event

monitoring_repository = SecurityRepository()


def record_attack(session_id: str, action: str, details: str) -> SecurityEvent:
    event = monitoring_repository.append(
        "attack",
        f"session={session_id}; action={action}; details={details}",
    )
    deception_orchestrator.activate(session_id=session_id, threat_score=80, reason=f"attack={action}")
    publish_event("hacker_attack_alert", {
        "session_id": session_id,
        "hacker_id": "hacker",
        "action": action,
        "details": details,
        "target_patient_id": "ALL_PATIENTS",
        "target_patient_name": "Hospital Inpatient Database",
        "threat_score": 88,
        "stolen_categories": [
            "🆔 Patient Aadhaar Number & Government Identification",
            "📞 Mobile Phone Number & Residential Address",
            "🩺 Clinical Diagnoses, Symptoms & Medical History",
            "💊 Prescription Medicines & Treatment Regimens",
            "🏥 Attending Doctor & Department Allocation",
            "🏦 Insurance Policy Account & Emergency Family Contacts",
        ],
        "synthetic_patient_id": "UNRESOLVED_ATTACK_TARGET",
        "watermark_id": "UNRESOLVED_ATTACK_TARGET",
    })
    return event


def record_audit(actor: str, action: str, details: str) -> SecurityEvent:
    event = monitoring_repository.append(
        "audit",
        f"actor={actor}; action={action}; details={details}",
    )
    publish_event("audit", {"actor": actor, "action": action, "details": details})
    return event
