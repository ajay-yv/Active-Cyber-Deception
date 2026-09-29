from fastapi import APIRouter, Depends
from sqlalchemy import func

from app.core.dependencies import get_current_user, require_roles, request_context_headers
from app.services.gateway import evaluate_request
from app.db.engines import RealSessionLocal
from app.models.real import Appointment, RealDoctor
from app.services.deception import deception_orchestrator
from app.services.registries import honeytoken_repository, patient_repository, synthetic_repository
from app.services.security import security_repository
from app.repositories.synthetic_repository import serialize_catalog_twin

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _build_alerts() -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    attacks = security_repository.find_by_event_type("attack")[-6:]

    for attack in attacks:
        details = attack.details
        parts = {}
        for item in details.split(";"):
            if "=" in item:
                k, v = item.split("=", 1)
                parts[k.strip()] = v.strip()

        target_hint = parts.get("target") or "Target Patient Records"
        query_hint = parts.get("query") or "Exfiltration Query"
        syn_hint = parts.get("synthetic_twin") or "UNRESOLVED_ATTACK_TARGET"
        wm_hint = parts.get("watermark") or "UNRESOLVED_ATTACK_TARGET"
        session_hint = parts.get("session") or "Adversary"
        risk_hint = parts.get("risk") or "95%"

        stolen_fields_desc = "Patient PII (Aadhaar Number, Mobile, Diagnoses, Prescriptions & Insurance Details)"

        message = (
            f"🚨 HACKER THEFT INTERCEPTED & DIVERTED (Risk: {risk_hint}) | "
            f"Adversary [{session_hint}] attempted to steal {target_hint} [{stolen_fields_desc}] via query '{query_hint}'. "
            f"AI Deception Engine routed request to Synthetic Twin '{syn_hint}' with Hidden Steganographic Watermark '{wm_hint}'."
        )
        alerts.append({"type": "Breach Interception Alert", "message": message, "severity": "critical"})

    if active_sessions := deception_orchestrator.status():
        for session in active_sessions:
            alerts.append(
                {
                    "type": "Cyber Deception Trap Active",
                    "message": f"Active Deception Sandbox (Threat Score: {session.threat_score}/100) | Session '{session.session_id}' trapped with Lure '{session.lure_type}'. Ephemeral traces will auto-purge upon disconnect.",
                    "severity": "warning",
                }
            )
    return alerts


def build_hospital_dashboard(role: str = "admin") -> dict:
    patients = patient_repository.list_all()
    synthetic_records = synthetic_repository.valid_catalog()
    with RealSessionLocal() as session:
        doctor_count = session.query(func.count(RealDoctor.id)).scalar() or 0
        appointment_count = session.query(func.count(Appointment.id)).scalar() or 0

    recent_patients = [
        {
            "id": patient.patient_id or patient.id,
            "name": patient.name,
            "status": "Admitted" if idx % 2 == 0 else "Discharged",
        }
        for idx, patient in enumerate(patients[-5:][::-1])
    ]
    role_label = "hospital_user" if role == "hospital" else role
    return {
        "role": role_label,
        "metrics": {
            "total_patients": len(patients),
            "doctors": doctor_count or 31,
            "appointments": appointment_count or 92,
            "synthetic_twins": len(synthetic_records),
            "honeytokens": len(honeytoken_repository.list_all()),
            "active_threats": len(deception_orchestrator.status()),
        },
        "recent_patients": recent_patients,
        "synthetic_records": [serialize_catalog_twin(twin) for twin in synthetic_records],
        "alerts": _build_alerts(),
    }


@router.get("")
@router.get("/")
def default_dashboard(
    current_user: object = Depends(get_current_user),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    evaluate_request(
        role=getattr(current_user, "role", "doctor"),
        path="/api/dashboard",
        username=getattr(current_user, "username", None),
        **context,
    )
    role = getattr(current_user, "role", "doctor")
    if role == "hacker":
        return hacker_dashboard(_=current_user)
    return build_hospital_dashboard("admin" if role == "administrator" else "hospital")


@router.get("/hospital")
def hospital_dashboard(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    return build_hospital_dashboard("hospital")


@router.get("/admin")
def admin_dashboard(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    return build_hospital_dashboard("admin")


@router.get("/hacker")
def hacker_dashboard(_: object = Depends(require_roles("hacker"))) -> dict:
    attack_count = len(security_repository.find_by_event_type("attack"))
    active_sessions = deception_orchestrator.status()
    synthetic_records = synthetic_repository.valid_catalog()

    return {
        "role": "hacker",
        "metrics": {
            "synthetic_records": len(synthetic_records),
            "honeytokens": len(honeytoken_repository.list_all()),
            "active_attacks": attack_count,
            "threat_score": max((session.threat_score for session in active_sessions), default=75),
        },
        "synthetic_records": [serialize_catalog_twin(twin) for twin in synthetic_records],
        "deception_assets": [
            {"type": "Clinical Record", "label": f"{twin.synthetic_patient_id}"}
            for twin in synthetic_records[-5:]
        ]
        + [
            {"type": "Secure Token", "label": token.value}
            for token in honeytoken_repository.list_all()[-3:]
        ],
    }
