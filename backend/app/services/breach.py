import json
from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.breach_repository import BreachLogRecord, BreachRepository
from app.repositories.synthetic_repository import SyntheticRepository, is_valid_synthetic_id
from app.services.audit import record_audit
from app.services.deception import deception_orchestrator
from app.services.security import record_forensic_attack
from app.services.watermark import create_watermark, poison_synthetic_payload, watermark_repository

breach_repository = BreachRepository()
synthetic_repository = SyntheticRepository()


def _get_existing_synthetic_twin(
    real_patient_id: str,
    available_synthetic_ids: set[str] | None = None,
) -> tuple[dict, str] | None:
    if available_synthetic_ids is None:
        available_synthetic_ids = {
            twin.synthetic_patient_id for twin in synthetic_repository.valid_catalog()
        }
    existing_twin = synthetic_repository.find_by_real_patient_id(real_patient_id)
    if existing_twin is None:
        existing_twin = synthetic_repository.find_by_synthetic_id(real_patient_id)
    if existing_twin is not None and (
        not is_valid_synthetic_id(existing_twin.synthetic_patient_id)
        or existing_twin.synthetic_patient_id not in available_synthetic_ids
    ):
        return None
    if existing_twin is not None:
        wm = watermark_repository.find_by_source_id(existing_twin.synthetic_patient_id, source_type="synthetic")
        if wm is None:
            wm_rec = create_watermark(existing_twin.synthetic_patient_id, "synthetic", "HOSPITAL-001", "hacker-session")
            wm_id = wm_rec.watermark_id
        else:
            wm_rec = wm
            wm_id = wm.watermark_id
        
        synthetic_payload = {
            "synthetic_patient_id": existing_twin.synthetic_patient_id,
            "patient_id": existing_twin.synthetic_patient_id,
            "name": existing_twin.name,
            "age": existing_twin.age_range or "38-43 yrs",
            "gender": getattr(existing_twin, "gender", "Male") or "Male",
            "date_of_birth": getattr(existing_twin, "date_of_birth", "") or "",
            "blood_group": getattr(existing_twin, "blood_group", "O+") or "O+",
            "doctor_assigned": getattr(existing_twin, "doctor_assigned", "Dr. Priya Nair (Cardiology)") or "Dr. Priya Nair (Cardiology)",
            "department": getattr(existing_twin, "department", "Cardiology") or "Cardiology",
            "ward": getattr(existing_twin, "ward", "CCU-2") or "CCU-2",
            "admission_date": getattr(existing_twin, "admission_date", "") or "",
            "discharge_date": getattr(existing_twin, "discharge_date", "") or "",
            "disease": existing_twin.disease,
            "diagnosis": existing_twin.diagnosis,
            "symptoms": getattr(existing_twin, "symptoms", ["Fatigue", "Exertional dyspnea"]),
            "allergies": getattr(existing_twin, "allergies", ["No Known Drug Allergies (NKDA)"]),
            "medicines": getattr(existing_twin, "medicines", []) or [],
            "dosages": getattr(existing_twin, "dosages", ["1 tablet twice daily after meals"]),
            "treatment_pattern": existing_twin.treatment_pattern or "Standard Clinical Care Protocol",
            "lab_reports": getattr(existing_twin, "lab_reports", ["Complete Blood Count (CBC): Normal"]),
            "aadhaar_number": existing_twin.aadhaar_number,
            "phone_number": existing_twin.phone_number,
            "email": existing_twin.email,
            "address": existing_twin.address,
            "insurance_details": existing_twin.insurance_details or "Star Health Platinum Cover #SH-772910",
            "emergency_contact": existing_twin.emergency_contact or "+91-98421-74892",
            "source_type": "synthetic",
            "watermark_id": wm_id,
            "watermark": "Verified",
            "is_attractive_lure": getattr(existing_twin, "is_attractive_lure", True),
            "lure_type": getattr(existing_twin, "lure_type", "high_value_clinical_trial"),
            "notes": "Patient clinical record verified. Electronic Health Record active.",
        }
        poisoned_payload = poison_synthetic_payload(synthetic_payload, wm_rec)
        return poisoned_payload, wm_id
    return None


def handle_hacker_breach_request(
    session_id: str,
    hacker_id: str,
    query: str,
    target_patient_id: str,
    requested_payload: dict,
    ip_address: str = "127.0.0.1",
    user_agent: str = "",
) -> dict:
    is_bulk = target_patient_id in {"ALL_PATIENTS", "*", "ALL", ""} or "," in target_patient_id
    requested_fields = requested_payload.get("requested_fields") or requested_payload.get("fields") or []
    if not isinstance(requested_fields, list):
        requested_fields = []
    requested_fields = [str(field).strip() for field in requested_fields[:25] if str(field).strip()]
    sensitive_fields = {
        "aadhaar",
        "aadhaar_number",
        "address",
        "diagnosis",
        "disease",
        "email",
        "insurance",
        "insurance_details",
        "medicines",
        "phone",
        "phone_number",
        "prescriptions",
        "symptoms",
    }
    normalized_fields = {field.lower() for field in requested_fields}
    query_upper = query.upper()
    contains_attack_syntax = any(
        keyword in query_upper for keyword in ("SELECT", "UNION", "DROP", "OR 1=1", "DUMP", "EXFILTRATE")
    )
    threat_score = min(
        100,
        60
        + (20 if is_bulk else 0)
        + (20 if contains_attack_syntax else 0)
        + min(5 * len(normalized_fields & sensitive_fields), 20)
        + (10 if requested_payload.get("dump_pii") else 0),
    )

    gateway_decision = "DECEIVE"

    # Activate Autonomous Deception Orchestrator (ADO)
    ado_session = deception_orchestrator.activate(
        session_id=session_id,
        threat_score=threat_score,
        reason=f"Exfiltration Attack Vector: {query}",
        lure_type="high_value_clinical_trial" if is_bulk else "vip_executive_record",
    )
    deception_orchestrator.record_interception(session_id, target_patient_id, query)

    # Format single target ID e.g. "1" -> "P-01"
    if not is_bulk and target_patient_id.strip().isdigit():
        target_patient_id = f"P-{int(target_patient_id.strip()):02d}"

    available_twins = synthetic_repository.valid_catalog()
    available_synthetic_ids = {twin.synthetic_patient_id for twin in available_twins}
    if is_bulk:
        target_ids = [t.real_patient_id for t in available_twins if t.real_patient_id]
    elif "," in target_patient_id:
        target_ids = [t.strip() for t in target_patient_id.split(",") if t.strip()]
    else:
        target_ids = [target_patient_id]

    decoy_records = []
    watermark_ids = []
    syn_patient_ids = []
    for pid in target_ids:
        result = _get_existing_synthetic_twin(pid, available_synthetic_ids)
        if result is None:
            continue
        syn_payload, wm_id = result
        watermark_ids.append(wm_id)
        syn_patient_ids.append(syn_payload["synthetic_patient_id"])
        decoy_records.append(syn_payload)

    if len(decoy_records) == 1:
        response_data = decoy_records[0]
        response_data["records_returned"] = 1
        response_data["is_synthetic"] = True
        response_data["threat_score"] = threat_score
        response_data["gateway_decision"] = gateway_decision
        response_data["attack_type"] = "DATA_EXFILTRATION" if is_bulk else "PATIENT_ENUMERATION"
    else:
        response_data = {
            "exfiltration_type": "BULK_DATABASE_DUMP" if is_bulk else "MULTI_RECORD_PROBE",
            "attack_type": "DATA_EXFILTRATION" if is_bulk or contains_attack_syntax else "PATIENT_ENUMERATION",
            "total_records_intercepted": len(decoy_records),
            "gateway_action": "AI_GATEWAY_HIGH_THREAT_REDIRECT_ACTIVE",
            "ado_lifecycle_state": ado_session.state.value,
            "gateway_decision": gateway_decision,
            "threat_score": threat_score,
            "ai_risk_score": threat_score,
            "watermark_type": "Zero-Width Unicode Steganography (Invisible)",
            "decoy_records": decoy_records,
            "records_requested": len(target_ids),
            "records_returned": len(decoy_records),
            "synthetic_patient_ids": syn_patient_ids,
        }

    original_payload = json.dumps(requested_payload, sort_keys=True)
    response_payload = json.dumps(response_data, default=str)
    primary_wm = watermark_ids[0] if watermark_ids else None
    primary_syn_id = syn_patient_ids[0] if syn_patient_ids else None

    audit_text = f"hacker_request={query}; target={target_patient_id}; threat_score={threat_score}; ado_state={ado_session.state.value}; redirected=synthetic({primary_syn_id}); watermark={primary_wm}"

    breach_repository.add(
        BreachLogRecord(
            id=str(uuid4()),
            session_id=session_id,
            hacker_id=hacker_id,
            query=query,
            target_patient_id=target_patient_id,
            valid_request=True,
            request_payload=original_payload,
            response_payload=response_payload,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    record_audit("system", "hacker_breach_request", audit_text)
    record_forensic_attack(
        attack_type="DATA_EXFILTRATION" if is_bulk or contains_attack_syntax else "PATIENT_ENUMERATION",
        session_id=session_id,
        risk_score=threat_score,
        gateway_decision=gateway_decision,
        patient_id=None if is_bulk else target_patient_id,
        synthetic_patient_id=primary_syn_id,
        username=hacker_id,
        ip_address=ip_address,
        user_agent=user_agent,
        watermark_id=primary_wm,
        records_requested=len(target_ids),
        records_returned=len(decoy_records),
        requested_fields=requested_fields,
        synthetic_patient_ids=syn_patient_ids,
    )
    return response_data
