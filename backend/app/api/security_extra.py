from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import require_roles, request_context_headers
from app.core.simulation import require_simulation_enabled
from app.repositories.user_repository import user_repository
from app.services.attack_mode import execute_attack_mode
from app.services.audit import record_audit
from app.services.realtime import publish_event
from app.services.security import record_forensic_attack, security_repository
from app.services.gateway import evaluate_request
from app.services.registries import synthetic_repository

router = APIRouter(prefix="/security", tags=["security"])


class AttackModeRequest(BaseModel):
    session_id: str
    mode: str
    details: str | None = None
    target_patient_id: str | None = None
    requested_payload: dict | None = None


class SecurityMarkerRequest(BaseModel):
    marker: str


class SimulationFinishRequest(BaseModel):
    attack: str
    session_id: str
    target: str | None = None


ALLOWED_SECURITY_MARKERS = {
    "TEST_SQL_INJECTION",
    "TEST_TRAVERSAL",
}


@router.post("/users/{username}/block")
def block_user(username: str, _: object = Depends(require_roles("administrator"))) -> dict:
    ok = user_repository.set_block(username, True)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    record_audit("system", "block_user", f"user={username}")
    return {"status": "ok", "username": username, "blocked": True}


@router.post("/users/{username}/unblock")
def unblock_user(username: str, _: object = Depends(require_roles("administrator"))) -> dict:
    ok = user_repository.set_block(username, False)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    record_audit("system", "unblock_user", f"user={username}")
    return {"status": "ok", "username": username, "blocked": False}


@router.get("/hack-modes")
def hack_modes(_: object = Depends(require_roles("hacker"))) -> dict:
    modes = [
        {"id": "probe_api", "label": "API Probing", "description": "Probe endpoints for available data (simulated)"},
        {"id": "exfiltrate_original", "label": "Exfiltrate Original Patient Data", "description": "Attempt to steal original patient data, but the system returns synthetic decoy data."},
        {"id": "exfiltrate_synthetic", "label": "Exfiltrate Synthetic Records", "description": "Attempt to exfiltrate synthetic EHR records (returns decoy data)"},
        {"id": "phishing_sim", "label": "Phishing Simulation", "description": "Simulate credential harvesting against decoy targets"},
        {"id": "ransomware_sim", "label": "Ransomware Simulation", "description": "Simulate data encryption activity on decoy storage"},
    ]
    return {"modes": modes}


@router.post("/hack-modes/execute")
def execute_hack_mode(payload: AttackModeRequest, current_user: object = Depends(require_roles("hacker"))) -> dict:
    result = execute_attack_mode(
        session_id=payload.session_id,
        mode=payload.mode,
        details=payload.details or "",
        hacker_id=getattr(current_user, "username", "hacker"),
        target_patient_id=payload.target_patient_id,
        requested_payload=payload.requested_payload,
    )
    return result


@router.post("/simulation/marker")
def security_test_marker(
    payload: SecurityMarkerRequest,
    current_user: object = Depends(require_roles("hacker", "administrator")),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    require_simulation_enabled()
    if payload.marker not in ALLOWED_SECURITY_MARKERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported security test marker")

    probe = "TEST_SQL_INJECTION UNION SELECT 1" if payload.marker == "TEST_SQL_INJECTION" else "TEST_TRAVERSAL ../TEST_TRAVERSAL"
    decision = evaluate_request(
        role=getattr(current_user, "role", "hacker"),
        username=getattr(current_user, "username", "hacker"),
        method="POST",
        path="/api/security/simulation/marker",
        body=probe,
        **context,
    )

    attack_type = "SQL_INJECTION" if payload.marker == "TEST_SQL_INJECTION" else "DIRECTORY_TRAVERSAL"
    event_payload = record_forensic_attack(
        attack_type=attack_type,
        session_id=context["session_id"],
        risk_score=float(decision.threat_score),
        gateway_decision=decision.action,
        username=getattr(current_user, "username", "hacker"),
        ip_address=context.get("ip_address", "127.0.0.1"),
        user_agent=context.get("browser", ""),
        attack_probability=decision.attack_probability,
        blocked_status=decision.action == "block",
        requested_fields=[],
        records_requested=0,
        records_returned=0,
    )

    from app.repositories.watermark_repository import watermark_repository
    existing_twins = synthetic_repository.valid_catalog()
    first_decoy = existing_twins[0] if existing_twins else None

    sample_decoy = None
    if first_decoy is not None:
        twin_id = first_decoy.synthetic_patient_id
        wm = watermark_repository.find_by_source_id(twin_id, source_type="synthetic")
        sample_decoy = {
            "patient_id": twin_id,
            "id": twin_id,
            "synthetic_patient_id": twin_id,
            "name": first_decoy.name,
            "disease": first_decoy.disease,
            "diagnosis": first_decoy.diagnosis,
            "gender": first_decoy.gender,
            "age": first_decoy.age_range,
            "doctor_assigned": first_decoy.doctor_assigned,
            "department": first_decoy.department,
            "ward": first_decoy.ward,
            "phone": first_decoy.phone_number,
            "email": first_decoy.email,
            "aadhaar": first_decoy.aadhaar_number,
            "watermark_id": wm.watermark_id if wm else None,
        }

    deceptive_payload = {
        "attack_type": attack_type,
        "is_synthetic": True,
        "sample_decoy": sample_decoy,
        "message": f"Query intercepted and redirected to honeypot telemetry layer.",
    }

    if hasattr(decision, "model_dump"):
        decision_payload = decision.model_dump()
    elif hasattr(decision, "dict"):
        decision_payload = decision.dict()
    else:
        decision_payload = vars(decision)

    return {
        "status": "detected",
        "marker": payload.marker,
        "decision": decision_payload,
        "event": event_payload,
        "deceptive_payload": deceptive_payload,
    }


@router.post("/simulation/finish")
def simulation_finish(
    payload: SimulationFinishRequest,
) -> dict:
    require_simulation_enabled()
    now_str = datetime.now(timezone.utc).isoformat()
    event_payload = {
        "attack_type": payload.attack,
        "session_id": payload.session_id,
        "status": "completed",
        "target": payload.target or "http://127.0.0.1:8000",
        "timestamp": now_str,
    }
    publish_event("ATTACK_FINISHED", event_payload)
    return {"status": "ok", "event": event_payload}


@router.get("/forensic-records")
def list_forensic_records(
    limit: int = 50,
    _: object = Depends(require_roles("administrator", "doctor", "receptionist")),
) -> dict:
    return {"records": security_repository.list_forensic_records(limit=limit)}

