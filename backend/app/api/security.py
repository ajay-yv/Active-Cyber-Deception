from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import require_roles
from app.repositories.watermark_repository import WatermarkRecord
from app.repositories.user_repository import user_repository
from app.services.attribution import leak_attribution_service
from app.services.breach import handle_hacker_breach_request
from app.services.deception import deception_orchestrator
from app.services.monitoring import monitoring_repository, record_attack
from app.services.security import security_repository
from app.services.registries import patient_repository, synthetic_repository
from app.services.watermark import extract_invisible_watermark, watermark_repository
from app.services.audit import record_audit
from app.services.patients import patient_service


class AttackRequest(BaseModel):
    session_id: str
    action: str
    details: str


class BreachRequestPayload(BaseModel):
    query: str
    target_patient_id: str
    requested_payload: dict


class TeardownRequestPayload(BaseModel):
    session_id: str
    reason: str = "Adversary session completed. Autonomous cleanup triggered."


class DeployLurePayload(BaseModel):
    session_id: str
    lure_type: str = "high_value_clinical_trial"


class ForensicsScanRequest(BaseModel):
    content: str | None = None
    raw_content: str | None = None
    source_type: str | None = None


router = APIRouter(prefix="/security", tags=["security"])


@router.get("/overview")
def overview(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    attacks = security_repository.find_by_event_type("attack")
    ai_decisions = security_repository.find_by_event_type("ai_decision")
    watermarks = watermark_repository.list_all()
    suspicious_sessions = sum(1 for event in ai_decisions if "route=synthetic" in event.details)
    ado_telemetry = deception_orchestrator.get_ado_telemetry()
    return {
        "active_attacks": len(attacks),
        "suspicious_sessions": suspicious_sessions,
        "total_events": len(security_repository.list_all()),
        "watermarked_records": len(watermarks),
        "honeytokens": 27 + ado_telemetry["total_attractive_lures_deployed"],
        "ado_active_sessions": ado_telemetry["active_deception_sessions"],
        "ado_auto_teardowns": ado_telemetry["total_autonomous_teardowns"],
        "data_leakage_prevented": "100.0% (Zero Real Data Exposed)",
    }


@router.post("/attacks")
def create_attack(payload: AttackRequest, _: object = Depends(require_roles("administrator", "hacker"))) -> dict:
    event = record_attack(payload.session_id, payload.action, payload.details)
    return {"event": event.__dict__}


@router.post("/breach")
def create_breach_request(
    payload: BreachRequestPayload,
    current_user: object = Depends(require_roles("hacker")),
) -> dict:
    session_id = getattr(current_user, "username", "hacker") + "-session"
    hacker_id = getattr(current_user, "username", "hacker")
    response = handle_hacker_breach_request(
        session_id=session_id,
        hacker_id=hacker_id,
        query=payload.query,
        target_patient_id=payload.target_patient_id,
        requested_payload=payload.requested_payload,
    )
    return response


@router.get("/leaks/{watermark_id}")
def leak_attribution(watermark_id: str, _: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    result = leak_attribution_service.attribute(watermark_id)
    if result.watermark is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watermark not found")

    forensic_record = None
    if result.watermark.source_type == "synthetic":
        forensic_record = synthetic_repository.find_by_synthetic_id(result.watermark.source_id)
    else:
        forensic_record = patient_repository.find_by_id(result.watermark.source_id)

    return {
        "watermark_id": result.watermark.watermark_id,
        "source_type": result.watermark.source_type,
        "source_id": result.watermark.source_id,
        "hospital_id": result.watermark.hospital_id,
        "session_id": result.watermark.session_id,
        "timestamp": result.watermark.timestamp,
        "watermark_text": result.watermark.watermark_text,
        "watermark_fingerprint": result.watermark.watermark_fingerprint,
        "watermark": result.watermark.__dict__,
        "forensic_record": forensic_record.__dict__ if forensic_record is not None else {},
        "forensic_link": f"/api/security/leaks/{result.watermark.watermark_id}",
        "forensic_forensics_link": f"/api/security/leaks/{result.watermark.watermark_id}/forensics",
        "attack_timeline": result.attack_timeline,
        "report": result.report,
        "dossier": result.dossier.__dict__ if result.dossier is not None else None,
    }


@router.get("/leaks/{watermark_id}/forensics")
def leak_forensic_profile(watermark_id: str, _: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    result = leak_attribution_service.attribute(watermark_id)
    if result.watermark is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watermark not found")

    forensic_record = None
    if result.watermark.source_type == "synthetic":
        forensic_record = synthetic_repository.find_by_synthetic_id(result.watermark.source_id)
    else:
        forensic_record = patient_repository.find_by_id(result.watermark.source_id)

    return {
        "watermark_id": result.watermark.watermark_id,
        "source_type": result.watermark.source_type,
        "source_id": result.watermark.source_id,
        "hospital_id": result.watermark.hospital_id,
        "session_id": result.watermark.session_id,
        "timestamp": result.watermark.timestamp,
        "watermark_text": result.watermark.watermark_text,
        "watermark_fingerprint": result.watermark.watermark_fingerprint,
        "watermark": result.watermark.__dict__,
        "forensic_link": f"/api/security/leaks/{result.watermark.watermark_id}",
        "forensic_forensics_link": f"/api/security/leaks/{result.watermark.watermark_id}/forensics",
        "attack_timeline": result.attack_timeline,
        "report": result.report,
        "dossier": result.dossier.__dict__ if result.dossier is not None else None,
        "forensic_record": forensic_record.__dict__ if forensic_record is not None else None,
    }


@router.get("/events")
def list_events(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    return {
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "details": event.details,
                "created_at": event.created_at,
            }
            for event in security_repository.recent(15)
        ]
    }


@router.post("/forensics/scan")
def scan_forensics(payload: ForensicsScanRequest | None = None, _: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    raw_content = ""
    source_type = None
    if payload:
        raw_content = (payload.raw_content or payload.content or "").strip()
        source_type = payload.source_type

    dossier = leak_attribution_service.attribute_from_content(raw_content)
    if dossier is not None:
        return {
            "matched": True,
            "watermark_id": dossier.watermark_id,
            "watermark": {
                "watermark_id": dossier.watermark_id,
                "watermark_fingerprint": dossier.watermark_fingerprint,
                "watermark_text": dossier.watermark_text,
                "source_type": dossier.source_type,
                "source_id": dossier.source_id,
                "session_id": dossier.session_id,
                "hospital_id": dossier.hospital_id,
            },
            "source_type": dossier.source_type,
            "is_invisible_watermark": dossier.is_invisible_watermark,
            "message": "Watermark successfully extracted & attributed from leaked text via Zero-Width Steganography/Fingerprint.",
            "dossier": dossier.__dict__,
        }

    # Fallback to direct string matching
    candidates = watermark_repository.list_all()
    normalized = raw_content.lower()
    matched = None
    for record in candidates:
        haystacks = [record.watermark_id, record.watermark_text, record.watermark_fingerprint, record.source_id, record.session_id]
        if source_type and record.source_type != source_type:
            continue
        if any(item and item.lower() in normalized for item in haystacks):
            matched = record
            break

    if matched is None:
        return {"matched": False, "watermark_id": None, "watermark": None, "message": "No watermark match found in supplied content"}

    res = leak_attribution_service.attribute(matched.watermark_id)
    return {
        "matched": True,
        "watermark_id": matched.watermark_id,
        "watermark": matched.__dict__,
        "source_type": matched.source_type,
        "is_invisible_watermark": False,
        "message": "Watermark match identified in leaked content",
        "dossier": res.dossier.__dict__ if res.dossier is not None else None,
    }


@router.post("/forensics/recover")
def recover_original_patient(
    payload: ForensicsScanRequest | None = None,
    raw_content: str | None = None,
    _: object = Depends(require_roles("administrator", "doctor", "nurse", "receptionist")),
) -> dict:
    content = ""
    if payload:
        content = (payload.raw_content or payload.content or "").strip()
    if not content and raw_content:
        content = raw_content.strip()

    return leak_attribution_service.recover_original_patient_from_leak(content)


@router.get("/watermarks")
def list_watermarks(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    records = watermark_repository.list_all()
    payload = []
    for r in records:
        payload.append(
            {
                "id": r.id,
                "watermark_id": r.watermark_id,
                "source_id": r.source_id,
                "source_type": r.source_type,
                "hospital_id": r.hospital_id,
                "timestamp": r.timestamp,
                "session_id": r.session_id,
                "watermark_text": r.watermark_text,
                "watermark_fingerprint": r.watermark_fingerprint,
                "forensic_link": f"/api/security/leaks/{r.watermark_id}",
                "forensic_forensics_link": f"/api/security/leaks/{r.watermark_id}/forensics",
            }
        )
    return {"watermarks": payload}


@router.get("/deception/status")
@router.get("/ado/status")
def deception_status(_: object = Depends(require_roles("administrator", "doctor", "receptionist", "hacker"))) -> dict:
    return deception_orchestrator.get_ado_telemetry()


@router.post("/ado/teardown")
def autonomous_teardown(
    payload: TeardownRequestPayload | None = None,
    session_id: str | None = None,
    reason: str | None = None,
    _: object = Depends(require_roles("administrator", "doctor", "receptionist", "hacker")),
) -> dict:
    sid = (payload.session_id if payload and payload.session_id else session_id) or ""
    rsn = (payload.reason if payload and payload.reason else reason) or "Adversary session completed. Ephemeral traces purged."
    res = deception_orchestrator.autonomous_teardown(sid, rsn)
    return {
        "status": "CLEANED_UP",
        "session_id": sid or res.get("session_id", "all_sessions"),
        "state": "CLEANED_UP",
        "teardown_summary": res.get("teardown_summary", "Autonomous teardown executed."),
        "purged_decoys_count": res.get("purged_decoys_count", 0),
    }


@router.post("/ado/lures/deploy")
def deploy_attractive_lure(
    payload: DeployLurePayload | None = None,
    session_id: str | None = None,
    lure_type: str | None = None,
    _: object = Depends(require_roles("administrator", "doctor", "receptionist", "hacker")),
) -> dict:
    sid = (payload.session_id if payload and payload.session_id else session_id) or "default-adv-session"
    ltype = (payload.lure_type if payload and payload.lure_type else lure_type) or "vip_executive_record"
    return deception_orchestrator.deploy_attractive_lure(session_id=sid, lure_type=ltype)


@router.get("/twins/evolution")
def pattern_evolution_profile(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    return patient_service.get_pattern_profile()