import time
from datetime import datetime, timezone
from uuid import uuid4

from collections import defaultdict
from datetime import timedelta
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
FAILED_LOGIN_ALERT_THRESHOLD = 5
FAILED_LOGIN_ALERT_WINDOW = timedelta(minutes=5)


class PasswordResetStore:
    def __init__(self) -> None:
        self._otp_store: dict[str, tuple[str, float]] = {}
        self._admin_reset_otp_store: dict[
            str,
            tuple[str, dict[str, str], str | None, str | None, float, int],
        ] = {}
        self.expiration_seconds = 300

    def _key(self, purpose: str, email: str) -> str:
        return f"{purpose}:{email.lower()}"

    def set_otp(self, email: str, otp: str) -> None:
        self._otp_store[self._key('reset', email)] = (otp, time.time() + self.expiration_seconds)

    def clear_reset_otps(self, username: str) -> None:
        self._otp_store.pop(self._key("reset", username), None)
        self._admin_reset_otp_store.pop(self._key("admin_reset", username), None)

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

    def set_admin_reset_otps(
        self,
        username: str,
        email_otp: str,
        recovery_otps: dict[str, str],
        recovery_email: str | None,
        recovery_phone: str | None,
    ) -> None:
        self._admin_reset_otp_store[self._key("admin_reset", username)] = (
            email_otp,
            recovery_otps.copy(),
            recovery_email,
            recovery_phone,
            time.time() + self.expiration_seconds,
            0,
        )

    def verify_admin_reset_otps(
        self,
        username: str,
        email_otp: str,
        recovery_otps: dict[str, str],
        recovery_email: str | None,
        recovery_phone: str | None,
    ) -> bool:
        key = self._key("admin_reset", username)
        value = self._admin_reset_otp_store.get(key)
        if value is None:
            return False
        stored_email_otp, stored_recovery_otps, stored_email, stored_phone, expiry, attempts = value
        if time.time() > expiry:
            del self._admin_reset_otp_store[key]
            return False
        if (
            stored_email_otp != email_otp
            or stored_recovery_otps != recovery_otps
            or stored_email != recovery_email
            or stored_phone != recovery_phone
        ):
            attempts += 1
            if attempts >= 5:
                del self._admin_reset_otp_store[key]
            else:
                self._admin_reset_otp_store[key] = (
                    stored_email_otp,
                    stored_recovery_otps,
                    stored_email,
                    stored_phone,
                    expiry,
                    attempts,
                )
            return False
        del self._admin_reset_otp_store[key]
        return True

    def has_admin_reset_for_contact(
        self,
        username: str,
        email: str | None,
        phone_number: str | None,
    ) -> bool:
        value = self._admin_reset_otp_store.get(self._key("admin_reset", username))
        if value is None:
            return False
        _, _, stored_email, stored_phone, expiry, _ = value
        if time.time() > expiry:
            del self._admin_reset_otp_store[self._key("admin_reset", username)]
            return False
        return stored_email == email and stored_phone == phone_number

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
    records_requested: int = 0,
    blocked_status: bool = False,
    requested_fields: list[str] | None = None,
    synthetic_patient_ids: list[str] | None = None,
) -> dict:
    from app.repositories.synthetic_repository import is_valid_synthetic_id

    now_str = datetime.now(timezone.utc).isoformat()
    attack_id = f"atk_{uuid4().hex[:12]}"
    resolved_synthetic_id = (
        synthetic_patient_id
        if is_valid_synthetic_id(synthetic_patient_id)
        else "UNRESOLVED_ATTACK_TARGET"
    )
    payload = {
        "attack_id": attack_id,
        "attack_type": attack_type,
        "patient_id": patient_id,
        "synthetic_patient_id": resolved_synthetic_id,
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
        "synthetic_patient_ids": [
            value if is_valid_synthetic_id(value) else "UNRESOLVED_ATTACK_TARGET"
            for value in (synthetic_patient_ids or ([synthetic_patient_id] if synthetic_patient_id else []))
        ] or ["UNRESOLVED_ATTACK_TARGET"],
        "blocked_status": bool(blocked_status),
    }

    security_repository.add_forensic_record(payload)

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

        if patient_id:
            target_summary = f"Patient {patient_id}"
        else:
            target_summary = "Hospital Patient Database (All Patients)"

        hacker_alert_payload = {
            "session_id": session_id,
            "hacker_id": username or "simulated_hacker",
            "action": f"Adversary {attack_type} Attack Probe",
            "details": f"Attacker probe attempting to extract {', '.join(payload['requested_fields']) or 'patient data'} from {target_summary}",
            "target_patient_id": patient_id or "ALL_PATIENTS",
            "synthetic_patient_id": resolved_synthetic_id,
            "data_type": ", ".join(payload["requested_fields"]) or "Patient clinical record",
            "stolen_categories": [
                "🆔 Patient Aadhaar Number & Government Identification",
                "📞 Mobile Phone Number & Residential Address",
                "🩺 Clinical Diagnoses, Symptoms & Medical History",
                "💊 Prescription Medicines & Treatment Regimens",
                "🏥 Attending Doctor & Department Allocation",
                "🏦 Insurance Policy Account & Emergency Family Contacts",
            ],
            "watermark_id": watermark_id or "UNRESOLVED_ATTACK_TARGET",
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
                "synthetic_patient_id": resolved_synthetic_id,
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
                "synthetic_id": resolved_synthetic_id,
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
    attempted_username = (username or "").strip()[:255]
    failure_count, should_alert = security_repository.record_failed_login(
        username=(username or "").strip(),
        ip_address=ip_address,
        threshold=FAILED_LOGIN_ALERT_THRESHOLD,
        window=FAILED_LOGIN_ALERT_WINDOW,
    )
    security_repository.append(
        "login_failure",
        f"username={attempted_username}; session={session_id}; ip={ip_address}; device={device}; browser={browser}; country={country}",
    )
    _failed_login_accounts[session_id].add(username)
    _failed_login_counts[session_id] += 1
    session_failure_count = _failed_login_counts[session_id]
    distinct_users = len(_failed_login_accounts[session_id])

    is_credential_stuffing = distinct_users >= 3
    attack_type = "CREDENTIAL_STUFFING" if is_credential_stuffing else "BRUTE_FORCE"

    if session_failure_count >= AUTO_BLOCK_SESSION_THRESHOLD or is_credential_stuffing:
        block_session(session_id, f"Repeated login failures ({session_failure_count} attempts) - {attack_type}")

    record_suspicious_activity(session_id=session_id, reason=f"repeated_login_failure_{attack_type}", username=username)

    if should_alert or session_failure_count == FAILED_LOGIN_ALERT_THRESHOLD:
        now_str = datetime.now(timezone.utc).isoformat()
        forensic_attack = security_repository.add_forensic_record({
            "attack_type": attack_type,
            "session_id": session_id,
            "username": attempted_username,
            "ip_address": ip_address,
            "timestamp": now_str,
            "risk_score": 90,
            "gateway_decision": "MONITOR",
            "records_requested": 0,
            "records_returned": 0,
            "requested_fields": [],
            "blocked_status": session_id in blocked_sessions,
        })
        alert_payload = {
            "attack_id": forensic_attack["attack_id"],
            "attempted_username": attempted_username,
            "ip_address": ip_address,
            "attempt_count": failure_count,
            "threshold": FAILED_LOGIN_ALERT_THRESHOLD,
            "window_minutes": int(FAILED_LOGIN_ALERT_WINDOW.total_seconds() // 60),
            "attack_type": attack_type,
            "threat_score": 90,
            "timestamp": now_str,
            "session_id": session_id,
        }
        security_repository.append(
            "failed_login_alert",
            f"username={attempted_username}; session={session_id}; ip={ip_address}; attempts={failure_count}; window_minutes={alert_payload['window_minutes']}",
        )
        publish_event("FAILED_LOGIN_THRESHOLD_REACHED", alert_payload)


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
    security_repository.clear_failed_login_attempts()


def is_session_blocked(session_id: str) -> bool:
    if session_id in TRUSTED_SESSIONS:
        return False
    return session_id in blocked_sessions
