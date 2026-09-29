import json
from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.breach_repository import BreachLogRecord, BreachRepository
from app.repositories.synthetic_repository import SyntheticRepository, is_valid_synthetic_id
from app.services.audit import record_audit
from app.services.deception import deception_orchestrator
from app.services.realtime import publish_event
from app.services.security import security_repository
from app.services.watermark import create_watermark, poison_synthetic_payload, watermark_repository

breach_repository = BreachRepository()
synthetic_repository = SyntheticRepository()


def _get_existing_synthetic_twin(real_patient_id: str) -> tuple[dict, str] | None:
    existing_twin = synthetic_repository.find_by_real_patient_id(real_patient_id)
    if existing_twin is None:
        existing_twin = synthetic_repository.find_by_synthetic_id(real_patient_id)
    if existing_twin is not None and not is_valid_synthetic_id(existing_twin.synthetic_patient_id):
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


def handle_hacker_breach_request(session_id: str, hacker_id: str, query: str, target_patient_id: str, requested_payload: dict) -> dict:
    is_bulk = target_patient_id in {"ALL_PATIENTS", "*", "ALL", ""} or "," in target_patient_id
    
    # AI Risk Score calculation
    if is_bulk:
        threat_score = 98
    elif any(kw in query.upper() for kw in ["SELECT", "UNION", "DROP", "OR 1=1", "DUMP", "EXFILTRATE"]):
        threat_score = 96
    else:
        threat_score = 94

    is_high_risk = threat_score >= 50
    gateway_decision = "DECEIVE"
    threat_level = "CRITICAL" if threat_score >= 90 else "HIGH"

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

    if is_bulk:
        target_ids = [t.real_patient_id for t in synthetic_repository.list_all() if t.real_patient_id]
        target_name_summary = f"ALL {len(target_ids)} Patient Records (Bulk Dump Attempt)"
    elif "," in target_patient_id:
        target_ids = [t.strip() for t in target_patient_id.split(",") if t.strip()]
        target_name_summary = f"Multiple Patients ({', '.join(target_ids)})"
    else:
        target_ids = [target_patient_id]
        target_name_summary = f"Patient {target_patient_id}"

    decoy_records = []
    watermark_ids = []
    syn_patient_ids = []
    requested_fields = requested_payload.get("requested_fields") or requested_payload.get("fields") or []
    if not isinstance(requested_fields, list):
        requested_fields = []
    requested_fields = [str(field) for field in requested_fields[:25]]

    for pid in target_ids:
        result = _get_existing_synthetic_twin(pid)
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
    else:
        response_data = {
            "exfiltration_type": "BULK_DATABASE_DUMP" if is_bulk else "MULTI_RECORD_PROBE",
            "total_records_intercepted": len(decoy_records),
            "target_patient_ids": target_ids,
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
    attack_details = f"session={session_id}; query={query}; target={target_patient_id}; synthetic_twin={primary_syn_id}; decision={gateway_decision}; ado_state={ado_session.state.value}; risk={threat_score}%; watermark={primary_wm}"
    security_repository.append("attack", attack_details)

    # Real-time WebSocket alert broadcast to Admin/User Dashboard
    publish_event("hacker_attack_alert", {
        "session_id": session_id,
        "hacker_id": hacker_id,
        "action": query or f"Attacker Exfiltration Query against {target_name_summary}",
        "gateway_decision": gateway_decision,
        "ado_state": ado_session.state.value,
        "threat_level": threat_level,
        "threat_score": threat_score,
        "ai_risk_score": threat_score,
        "details": f"Adversary probe attempting to steal clinical EHR data for {target_name_summary}",
        "target_patient_id": target_patient_id,
        "synthetic_patient_id": primary_syn_id,
        "target_patient_name": target_name_summary,
        "data_type": "Patient PII (Aadhaar Number, Mobile Phone, Clinical Diagnosis, Prescriptions & Insurance)",
        "stolen_categories": [
            "🆔 Patient Aadhaar Number & Government Identification",
            "📞 Mobile Phone Number & Residential Address",
            "🩺 Clinical Diagnoses, Symptoms & Medical History",
            "💊 Prescription Medicines & Treatment Regimens",
            "🏥 Attending Doctor & Department Allocation",
            "🏦 Insurance Policy Account & Emergency Family Contacts",
        ],
        "watermark_id": primary_wm,
        "is_invisible_watermark": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_high_risk": is_high_risk,
        "attack_type": "DATA_EXFILTRATION" if is_bulk else "PATIENT_ENUMERATION",
        "records_requested": len(target_ids),
        "records_returned": len(decoy_records),
        "requested_fields": requested_fields,
        "synthetic_patient_ids": syn_patient_ids,
    })
    return response_data


