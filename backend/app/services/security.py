import time
from datetime import datetime, timezone
from uuid import uuid4

from collections import defaultdict
from typing import Optional
from hashlib import sha256

from app.repositories.password_reset_repository import PasswordResetTokenRecord, password_reset_repository
from app.repositories.security_repository import SecurityRepository
from app.repositories.user_repository import user_repository
from app.services.realtime import publish_event

security_repository = SecurityRepository()
blocked_sessions: set[str] = set()


def _hash_reset_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(username: str, email: str, token: str, expires_at: datetime) -> PasswordResetTokenRecord:
    return password_reset_repository.create_token(
        username=username,
        email=email,
        token_hash=_hash_reset_token(token),
        expires_at=expires_at,
    )


def verify_password_reset_token(token: str) -> PasswordResetTokenRecord | None:
    return password_reset_repository.verify_token(_hash_reset_token(token))


def mark_password_reset_token_used(token_id: str) -> bool:
    return password_reset_repository.mark_used(token_id)
_suspicious_session_counts: dict[str, int] = defaultdict(int)
_suspicious_user_counts: dict[str, int] = defaultdict(int)
_failed_login_accounts: dict[str, set[str]] = defaultdict(set)
_failed_login_counts: dict[str, int] = defaultdict(int)
AUTO_BLOCK_SESSION_THRESHOLD = 25
AUTO_BLOCK_USER_THRESHOLD = 25


class PasswordResetStore:
    def __init__(self) -> None:
        self._otp_store: dict[str, tuple[str, float]] = {}
        self.expiration_seconds = 300

    def _key(self, purpose: str, email: str) -> str:
        return f"{purpose}:{email.lower()}"

    def set_otp(self, email: str, otp: str) -> None:
        self._otp_store[self._key('reset', email)] = (otp, time.time() + self.expiration_seconds)

    def verify_reset_otp(self, email: str, otp: str) -> bool:
        key = self._key('reset', email)
        value = self._otp_store.get(key)
        if value is None:
            return False
        stored_otp, expiry = value
        if time.time() > expiry:
            del self._otp_store[key]
            return False
        if stored_otp != otp:
            return False
        del self._otp_store[key]
        return True

    def set_email_verification_otp(self, email: str, otp: str) -> None:
        self._otp_store[self._key('verify_email', email)] = (otp, time.time() + self.expiration_seconds)

    def verify_email_otp(self, email: str, otp: str) -> bool:
        key = self._key('verify_email', email)
        value = self._otp_store.get(key)
        if value is None:
            return False
        stored_otp, expiry = value
        if time.time() > expiry:
            del self._otp_store[key]
            return False
        if stored_otp != otp:
            return False
        del self._otp_store[key]
        return True

    def get_otp(self, email: str, purpose: str = 'reset') -> str | None:
        value = self._otp_store.get(self._key(purpose, email))
        return value[0] if value else None


password_reset_store = PasswordResetStore()


def record_forensic_attack(
    attack_type: str,
    session_id: str,
    risk_score: float,
    gateway_decision: str,
    patient_id: str | None = None,
    synthetic_patient_id: str | None = None,
    username: str | None = None,
    ip_address: str = "127.0.0.1",
    user_agent: str = "",
    attack_probability: float | None = None,
    watermark_id: str | None = None,
    records_returned: int = 0,
    blocked_status: bool = False,
    requested_fields: list[str] | None = None,
    records_requested: int = 0,
    synthetic_patient_ids: list[str] | None = None,
) -> dict:
    now_str = datetime.now(timezone.utc).isoformat()
    attack_id = f"atk_{uuid4().hex[:12]}"
    payload = {
        "attack_id": attack_id,
        "attack_type": attack_type,
        "patient_id": patient_id,
        "synthetic_patient_id": synthetic_patient_id,
        "session_id": session_id,
        "username": username,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp": now_str,
        "risk_score": float(risk_score),
        "attack_probability": float(attack_probability) if attack_probability is not None else round(min(risk_score * 0.98, 99.0), 1),
        "gateway_decision": gateway_decision,
        "watermark_id": watermark_id,
        "records_returned": int(records_returned),
        "records_requested": int(records_requested or records_returned),
        "requested_fields": list(requested_fields or []),
        "synthetic_patient_ids": list(synthetic_patient_ids or ([synthetic_patient_id] if synthetic_patient_id else [])),
        "blocked_status": bool(blocked_status),
    }

    try:
        security_repository.add_forensic_record(payload)
    except Exception:
        pass

    security_repository.append(
        "attack",
        f"session={session_id}; attack_type={attack_type}; score={risk_score}; action={gateway_decision}; blocked={blocked_status}",
    )

    try:
        publish_event("ATTACK_DETECTED", payload)
        publish_event("THREAT_SCORE_UPDATED", {
            "session_id": session_id,
            "risk_score": float(risk_score),
            "attack_probability": payload["attack_probability"],
            "timestamp": now_str,
        })

        target_summary = f"Patient {patient_id}" if patient_id else "Hospital Patient Database (All Patients)"
        hacker_alert_payload = {
            "session_id": session_id,
            "hacker_id": username or "simulated_hacker",
            "action": f"Adversary {attack_type} Attack Probe",
            "details": f"Attacker probe attempting to extract data from {target_summary}",
            "target_patient_id": patient_id or "ALL_PATIENTS",
            "target_patient_name": target_summary,
            "synthetic_patient_id": synthetic_patient_id or "SYN-01",
            "data_type": "Patient PII (Aadhaar Number, Mobile Phone, Residential Address, Clinical Diagnosis & Prescriptions)",
            "stolen_categories": [
                "🆔 Patient Aadhaar Number & Government Identification",
                "📞 Mobile Phone Number & Residential Address",
                "🩺 Clinical Diagnoses, Symptoms & Medical History",
                "💊 Prescription Medicines & Treatment Regimens",
                "🏥 Attending Doctor & Department Allocation",
                "🏦 Insurance Policy Account & Emergency Family Contacts",
            ],
            "watermark_id": watermark_id or "WM-AI-SECURITY-ACTIVE",
            "timestamp": now_str,
            "threat_score": int(risk_score),
            "attack_type": attack_type,
            "gateway_decision": gateway_decision,
            "blocked_status": blocked_status,
            "records_requested": payload["records_requested"],
            "records_returned": payload["records_returned"],
            "requested_fields": payload["requested_fields"],
            "synthetic_patient_ids": payload["synthetic_patient_ids"],
        }
        publish_event("hacker_attack_alert", hacker_alert_payload)

        if gateway_decision == "DECEIVE":
            publish_event("DECEPTION_STARTED", {
                "session_id": session_id,
                "target_patient_id": patient_id,
                "synthetic_patient_id": synthetic_patient_id,
                "timestamp": now_str,
            })
        if records_returned > 0 or synthetic_patient_id:
            publish_event("SYNTHETIC_DATA_RETURNED", {
                "session_id": session_id,
                "patient_id": patient_id,
                "synthetic_patient_id": synthetic_patient_id,
                "records_returned": records_returned,
                "timestamp": now_str,
            })
        if watermark_id:
            publish_event("WATERMARK_CREATED", {
                "watermark_id": watermark_id,
                "synthetic_id": synthetic_patient_id,
                "session_id": session_id,
                "timestamp": now_str,
            })
        if blocked_status:
            publish_event("SESSION_BLOCKED", {
                "session_id": session_id,
                "reason": f"Attack detected: {attack_type} (Risk: {risk_score}%)",
                "blocked_status": True,
                "timestamp": now_str,
            })
    except Exception:
        pass

    return payload


def log_login(username: str, role: str, ip_address: str, device: str, browser: str, country: str) -> None:
    security_repository.append(
        "login",
        f"username={username}; role={role}; ip={ip_address}; device={device}; browser={browser}; country={country}",
    )
    try:
        publish_event("login", {"username": username, "role": role, "ip": ip_address, "device": device, "browser": browser, "country": country})
    except Exception:
        pass


def log_login_failure(username: str, session_id: str, ip_address: str, device: str, browser: str, country: str) -> None:
    security_repository.append(
        "login_failure",
        f"username={username}; session={session_id}; ip={ip_address}; device={device}; browser={browser}; country={country}",
    )
    _failed_login_accounts[session_id].add(username)
    _failed_login_counts[session_id] += 1
    distinct_users = len(_failed_login_accounts[session_id])
    failure_count = _failed_login_counts[session_id]

    is_credential_stuffing = distinct_users >= 3
    attack_type = "CREDENTIAL_STUFFING" if is_credential_stuffing else "BRUTE_FORCE"
    risk_score = 95.0 if is_credential_stuffing else min(55.0 + failure_count * 15.0, 96.0)

    if failure_count >= AUTO_BLOCK_SESSION_THRESHOLD or is_credential_stuffing:
        block_session(session_id, f"Repeated login failures ({failure_count} attempts) - {attack_type}")

    is_blocked = session_id in blocked_sessions
    decision = "BLOCK" if is_blocked else ("DECEIVE" if risk_score >= 70 else "MONITOR")

    record_forensic_attack(
        attack_type=attack_type,
        session_id=session_id,
        risk_score=risk_score,
        gateway_decision=decision,
        username=username,
        ip_address=ip_address,
        user_agent=browser,
        blocked_status=is_blocked,
    )
    record_suspicious_activity(session_id=session_id, reason=f"repeated_login_failure_{attack_type}", username=username)


def log_decision(session_id: str, route: str, score: int, reason: str = "", username: str | None = None) -> None:
    security_repository.append("ai_decision", f"session={session_id}; route={route}; score={score}; reason={reason}")
    from app.services.deception import deception_orchestrator

    deception_orchestrator.observe_decision(session_id=session_id, route=route, score=score, reason=reason)
    try:
        publish_event("ai_decision", {"session_id": session_id, "route": route, "score": score, "reason": reason})
    except Exception:
        pass

    if route == "synthetic" or score >= 60:
        record_suspicious_activity(session_id=session_id, reason=reason, username=username)


TRUSTED_SESSIONS = {"active-user-session", "doc-user-session", "admin-user-session", "hospital-user-session"}


def block_session(session_id: str, reason: str) -> None:
    if session_id in TRUSTED_SESSIONS:
        return
    if session_id not in blocked_sessions:
        blocked_sessions.add(session_id)
        security_repository.append("session_block", f"session={session_id}; reason={reason}")
        now_str = datetime.now(timezone.utc).isoformat()
        try:
            publish_event("session_block", {"session_id": session_id, "reason": reason})
            publish_event("SESSION_BLOCKED", {"session_id": session_id, "reason": reason, "blocked_status": True, "timestamp": now_str})
        except Exception:
            pass


def _block_user(username: str, reason: str) -> None:
    if username in {"doctor", "admin", "reception", "administrator", "hacker"}:
        return
    if user_repository.set_block(username, True):
        security_repository.append("user_block", f"user={username}; reason={reason}")
        try:
            publish_event("user_block", {"username": username, "reason": reason})
        except Exception:
            pass


def record_suspicious_activity(session_id: str, reason: str = "", username: str | None = None) -> None:
    if not session_id or session_id in TRUSTED_SESSIONS:
        return

    _suspicious_session_counts[session_id] += 1
    session_count = _suspicious_session_counts[session_id]
    if session_count >= AUTO_BLOCK_SESSION_THRESHOLD and session_id not in blocked_sessions:
        block_session(session_id, f"Repeated suspicious activity ({session_count}) - {reason}")

    if username and username not in {"doctor", "admin", "reception", "administrator", "hacker"}:
        _suspicious_user_counts[username] += 1
        user_count = _suspicious_user_counts[username]
        if user_count >= AUTO_BLOCK_USER_THRESHOLD:
            _block_user(username, f"Repeated malicious activity ({user_count}) - {reason}")


def reset_security_state() -> None:
    """Reset in-memory security state for isolated test execution."""
    blocked_sessions.clear()
    _suspicious_session_counts.clear()
    _suspicious_user_counts.clear()
    _failed_login_accounts.clear()
    _failed_login_counts.clear()


def is_session_blocked(session_id: str) -> bool:
    if session_id in TRUSTED_SESSIONS:
        return False
    return session_id in blocked_sessions
