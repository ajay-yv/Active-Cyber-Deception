from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.audit import record_audit
from app.services.breach import handle_hacker_breach_request
from app.services.deception import deception_orchestrator
from app.services.monitoring import record_attack
from app.services.realtime import publish_event


def execute_attack_mode(
    session_id: str,
    mode: str,
    details: str,
    hacker_id: str | None = None,
    target_patient_id: str | None = None,
    requested_payload: dict | None = None,
) -> dict[str, Any]:
    effective_hacker = hacker_id or "hacker"
    effective_target = target_patient_id or "ALL_PATIENTS"

    threat_scores = {
        "probe_api": 70,
        "phishing_sim": 85,
        "ransomware_sim": 98,
        "exfiltrate_synthetic": 92,
        "exfiltrate_original": 95,
    }
    score = threat_scores.get(mode, 88)

    # Publish real-time hacker attack alert & burglar alarm sound to Admin/User dashboard
    publish_event("hacker_attack_alert", {
        "session_id": session_id,
        "hacker_id": effective_hacker,
        "action": f"ATTACK_MODE: {mode.upper()}",
        "details": details or f"Hacker initiated {mode} attack vector probe",
        "target_patient_id": effective_target,
        "target_patient_name": f"Target Scope: {effective_target}",
        "data_type": "Aadhaar Card, Phone, Address, Clinical Diagnosis & Medicines",
        "watermark_id": "WM-AI-SECURITY-ACTIVE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threat_score": score,
        "is_high_risk": True,
    })

    if mode == "probe_api":
        event = record_attack(session_id, mode, details or "Probe API surfaces for exposed EHR endpoints")
        record_audit("system", "probe_api", f"session={session_id}; details={details}")
        return {
            "mode": mode,
            "description": "API probing detected and logged. Deception engine may activate against suspicious requests.",
            "event": event.__dict__,
        }

    if mode == "phishing_sim":
        event = record_attack(session_id, mode, details or "Phishing simulation using decoy credentials")
        session = deception_orchestrator.activate(session_id=session_id, threat_score=72, reason="phishing_sim")
        record_audit("system", "phishing_sim", f"session={session_id}; decoys={','.join(session.decoy_ids)}")
        return {
            "mode": mode,
            "description": "Adaptive phishing simulation triggered. Decoy synthetic records and honeytokens were deployed.",
            "event": event.__dict__,
            "deception_session": session.__dict__,
        }

    if mode == "ransomware_sim":
        event = record_attack(session_id, mode, details or "Ransomware simulation against deceptive data stores")
        session = deception_orchestrator.activate(session_id=session_id, threat_score=95, reason="ransomware_sim")
        record_audit("system", "ransomware_sim", f"session={session_id}; decoys={','.join(session.decoy_ids)}")
        return {
            "mode": mode,
            "description": "Ransomware simulation triggered. High-threat decoys have been generated and a deception response is active.",
            "event": event.__dict__,
            "deception_session": session.__dict__,
        }

    if mode in {"exfiltrate_synthetic", "exfiltrate_original"}:
        response = handle_hacker_breach_request(
            session_id=session_id,
            hacker_id=effective_hacker,
            query=details or "Exfiltrate patient record",
            target_patient_id=effective_target,
            requested_payload=requested_payload or {},
        )
        record_audit("system", mode, f"session={session_id}; target={effective_target}")
        return {
            "mode": mode,
            "description": "Patient data exfiltration was intercepted. The attacker received synthetic decoy data, not original records.",
            "response": response,
        }

    event = record_attack(session_id, mode, details or "Unknown attack activity")
    record_audit("system", "unknown_attack_mode", f"session={session_id}; mode={mode}; details={details}")
    return {
        "mode": mode,
        "description": "Unknown attack mode. Logged for investigation.",
        "event": event.__dict__,
    }
