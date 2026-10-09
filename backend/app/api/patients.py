from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import User, require_roles, require_roles_or_deceive, request_context_headers
from app.schemas import PatientCreate
from app.services.audit import record_audit
from app.services.gateway import evaluate_request
from app.services.patients import PatientService
from app.services.realtime import publish_event
from app.services.twin import twin_generator_proxy
from app.services.registries import patient_repository, synthetic_repository
from app.services.security import record_forensic_attack
from app.services.watermark import watermark_repository

router = APIRouter(prefix="/patients", tags=["patients"])
service = PatientService(twin_generator_proxy)


@router.post("")
def create_patient(
    payload: PatientCreate,
    current_user: User = Depends(require_roles("administrator", "doctor", "receptionist")),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    decision = evaluate_request(role=current_user.role, **context)
    patient, twin = service.create_patient(
        payload,
        session_id=context["session_id"],
        hospital_id="HOSPITAL-001",
        route=decision.route,
    )
    record_audit(current_user.username, "create_patient", f"patient={patient.id}; route={decision.route}; session={context['session_id']}")
    publish_event("patient_created", {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "route": decision.route,
        "session_id": context["session_id"],
    })
    return {
        "decision": decision.model_dump(),
        "patient": patient.model_dump(),
        "synthetic_twin": twin.model_dump(),
    }


@router.get("")
def list_patients(
    patient_id: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=0),
    current_user: object = Depends(require_roles_or_deceive("administrator", "doctor", "receptionist", "patient", "hacker")),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    if getattr(current_user, "role", "") == "patient":
        patient_record_id = getattr(current_user, "patient_record_id", None)
        patient = None
        if patient_record_id:
            patient = patient_repository.find_by_id(patient_record_id)
        if patient is None:
            all_patients = patient_repository.list_all()
            user_email = getattr(current_user, "email", None)
            if user_email:
                for p in all_patients:
                    if p.email and p.email.strip().lower() == user_email.strip().lower():
                        patient = p
                        break
            user_phone = getattr(current_user, "phone_number", None) or getattr(current_user, "username", "")
            clean_user_phone = "".join(filter(str.isdigit, str(user_phone)))
            if patient is None and clean_user_phone and len(clean_user_phone) >= 7:
                for p in all_patients:
                    clean_p_phone = "".join(filter(str.isdigit, p.phone or ""))
                    if clean_user_phone in clean_p_phone or clean_p_phone in clean_user_phone:
                        patient = p
                        break
            if patient is None and all_patients:
                patient = all_patients[-1]

        if patient is None:
            return {"patient": None, "patients": []}

        if patient_id and patient_id != patient.id:
            raise HTTPException(status_code=404, detail="Patient record not found")
        if limit == 0:
            return {"patients": []}
        patient_data = patient.model_dump()
        return {"patient": patient_data, "patients": [patient_data]}

    params_dict = {}
    if patient_id:
        params_dict["patient_id"] = patient_id
    if limit is not None:
        params_dict["limit"] = str(limit)

    decision = evaluate_request(
        role=current_user.role,
        params=params_dict,
        path="/api/patients",
        username=getattr(current_user, "username", None),
        **context,
    )

    is_legitimate_staff = getattr(current_user, "role", "") in {"administrator", "doctor", "receptionist", "patient"}
    if decision.route == "synthetic" and not is_legitimate_staff:
        if patient_id:
            deceptive_patient = service.get_patient_deceptive(
                patient_id=patient_id,
                session_id=context["session_id"],
                hospital_id="HOSPITAL-001",
                ip_address=context.get("ip_address", "127.0.0.1"),
                user_agent=context.get("browser", ""),
                username=getattr(current_user, "username", None),
            )
            return {"patient": deceptive_patient, "patients": [deceptive_patient] if deceptive_patient else []}

        syn_patients = service.list_patients(
            session_id=context["session_id"],
            hospital_id="HOSPITAL-001",
            route="synthetic",
            limit=limit,
        )
        # Record exfiltration attack probe for any number of records requested (including single patient limit=1)
        record_forensic_attack(
            attack_type="DATA_EXFILTRATION",
            session_id=context["session_id"],
            risk_score=92.0,
            gateway_decision="DECEIVE",
            patient_id=syn_patients[0].get("id") if (limit == 1 and syn_patients) else None,
            synthetic_patient_id=syn_patients[0].get("synthetic_patient_id") if (limit == 1 and syn_patients) else None,
            username=getattr(current_user, "username", None),
            ip_address=context.get("ip_address", "127.0.0.1"),
            user_agent=context.get("browser", ""),
            records_returned=len(syn_patients),
            blocked_status=False,
        )
        return {"patients": syn_patients}

    if patient_id:
        real_p = patient_repository.find_by_id(patient_id)
        p_data = real_p.model_dump() if real_p else None
        return {"patient": p_data, "patients": [p_data] if p_data else []}

    patients = service.list_patients(
        session_id=context["session_id"],
        hospital_id="HOSPITAL-001",
        route="real",
        limit=limit,
    )
    result = []
    for patient in patients:
        pdata = patient if isinstance(patient, dict) else patient.model_dump()
        pid = pdata.get("id") or pdata.get("patient_id")
        forensic = synthetic_repository.find_by_real_patient_id(pid) if pid else None
        pdata["forensic_record"] = forensic.__dict__ if forensic is not None else None
        try:
            watermark_id = pdata.get("watermark_id")
            wm = watermark_repository.find_by_watermark_id(watermark_id) if watermark_id else None
            pdata["watermark_record"] = wm.__dict__ if wm is not None else None
        except Exception:
            pdata["watermark_record"] = None
        result.append(pdata)
    return {"patients": result}



@router.get("/history")
def list_patient_history(
    current_user: object = Depends(require_roles("administrator", "doctor", "receptionist")),
) -> dict:
    history = service.list_patient_history()
    return {"history": history}


@router.delete("/history/{history_id}")
def delete_patient_history(
    history_id: str,
    current_user: User = Depends(require_roles("administrator", "doctor", "receptionist")),
) -> dict:
    success = service.delete_patient_history(history_id)
    if not success:
        raise HTTPException(status_code=404, detail="Archived patient record not found")
    record_audit(current_user.username, "delete_patient_history", f"history_id={history_id}")
    return {"status": "success", "message": f"Archived record {history_id} permanently deleted"}


@router.delete("/history")
def clear_all_patient_history(
    current_user: User = Depends(require_roles("administrator", "doctor", "receptionist")),
) -> dict:
    count = service.clear_all_patient_history()
    record_audit(current_user.username, "clear_all_patient_history", f"cleared_count={count}")
    return {"status": "success", "message": f"Cleared all {count} archived patient history records", "count": count}


@router.delete("/purge/all")
def purge_all_patients(
    current_user: User = Depends(require_roles("administrator", "doctor", "receptionist")),
) -> dict:
    result = service.purge_all_patients()
    record_audit(current_user.username, "purge_all_patients", f"result={result}")
    publish_event("patient_deleted", {"patient_id": "ALL", "patient_name": "All Patients Purged"})
    return {"status": "success", "message": "All default patient records, history, and synthetic decoys removed", "purged": result}


@router.get("/me")
def get_my_patient(current_user: User = Depends(require_roles("patient"))) -> dict:
    patient_record_id = current_user.patient_record_id
    patient = None
    if patient_record_id:
        patient = patient_repository.find_by_id(patient_record_id)
    if patient is None:
        all_patients = patient_repository.list_all()
        user_email = getattr(current_user, "email", None)
        if user_email:
            for p in all_patients:
                if p.email and p.email.strip().lower() == user_email.strip().lower():
                    patient = p
                    break
        user_phone = getattr(current_user, "phone_number", None) or getattr(current_user, "username", "")
        clean_user_phone = "".join(filter(str.isdigit, str(user_phone)))
        if patient is None and clean_user_phone and len(clean_user_phone) >= 7:
            for p in all_patients:
                clean_p_phone = "".join(filter(str.isdigit, p.phone or ""))
                if clean_user_phone in clean_p_phone or clean_p_phone in clean_user_phone:
                    patient = p
                    break
        if patient is None and all_patients:
            patient = all_patients[-1]

    if patient is None:
        return {"patient": None, "patients": []}
    patient_data = patient.model_dump()
    return {"patient": patient_data, "patients": [patient_data]}


@router.get("/{patient_id}")
def get_patient(
    patient_id: str,
    current_user: object = Depends(require_roles_or_deceive("administrator", "doctor", "receptionist", "patient", "hacker")),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    if getattr(current_user, "role", "") == "patient":
        patient_record_id = getattr(current_user, "patient_record_id", None)
        patient = patient_repository.find_by_id(patient_id)
        if patient is None:
            raise HTTPException(status_code=404, detail="Patient record not found")
        if patient_record_id and patient.id != patient_record_id:
            raise HTTPException(status_code=403, detail="Access denied to other patient records")
        return {"patient": patient.model_dump()}

    decision = evaluate_request(
        role=current_user.role,
        path=f"/api/patients/{patient_id}",
        username=getattr(current_user, "username", None),
        **context,
    )
    if decision.route == "synthetic":
        deceptive_patient = service.get_patient_deceptive(
            patient_id=patient_id,
            session_id=context["session_id"],
            hospital_id="HOSPITAL-001",
            ip_address=context.get("ip_address", "127.0.0.1"),
            user_agent=context.get("browser", ""),
            username=getattr(current_user, "username", None),
        )
        return {"patient": deceptive_patient}

    real_p = patient_repository.find_by_id(patient_id)
    if real_p is None:
        raise HTTPException(status_code=404, detail="Patient record not found")
    return {"patient": real_p.model_dump()}


@router.delete("/{patient_id}")
def delete_patient(
    patient_id: str,
    current_user: User = Depends(require_roles("administrator", "doctor", "receptionist")),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    decision = evaluate_request(role=current_user.role, **context)
    is_staff = getattr(current_user, "role", "") in {"administrator", "doctor", "receptionist"}
    effective_route = "real" if is_staff else decision.route
    deleted, twin = service.delete_patient(patient_id, session_id=context["session_id"], hospital_id="HOSPITAL-001", route=effective_route)
    if twin:
        publish_event("synthetic_twin_generated", {"real_patient_id": deleted.id if deleted else None, "synthetic_id": twin.synthetic_patient_id, "route": decision.route})

    if not deleted and decision.route == "real":
        raise HTTPException(status_code=404, detail="Patient record not found")

    record_audit(current_user.username, "delete_patient", f"patient={patient_id}; user={current_user.username}; route={decision.route}")
    if deleted:
        publish_event("patient_deleted", {
            "patient_id": patient_id,
            "patient_name": deleted.name,
            "deleted_by": current_user.username,
        })
        return {"status": "success", "message": f"Patient record for {deleted.name} moved to history", "deleted_patient": deleted.model_dump()}
    return {"status": "success", "message": "Suspicious delete routed to synthetic twin", "synthetic_twin": twin.model_dump()}


@router.put("/{patient_id}")
def update_patient(
    patient_id: str,
    payload: PatientCreate,
    current_user: User = Depends(require_roles("administrator", "doctor", "receptionist")),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict:
    decision = evaluate_request(role=current_user.role, **context)
    try:
        patient, twin = service.update_patient(payload=payload, patient_id=patient_id, session_id=context["session_id"], hospital_id="HOSPITAL-001", route=decision.route)
    except ValueError:
        raise HTTPException(status_code=404, detail="Patient not found")

    record_audit(current_user.username, "update_patient", f"patient={patient.id}; route={decision.route}; session={context['session_id']}")
    publish_event("patient_updated", {"patient_id": patient.id, "patient_name": patient.name, "route": decision.route, "session_id": context["session_id"]})
    return {"decision": decision.model_dump(), "patient": patient.model_dump(), "synthetic_twin": twin.model_dump()}
