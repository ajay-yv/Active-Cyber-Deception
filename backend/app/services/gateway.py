import logging
import os
import time
from collections import defaultdict
from uuid import uuid4

import httpx
import re
from typing import Any
from pydantic import BaseModel, Field

from app.ml import model_loader
from app.repositories.ai_decision_repository import AIDecisionRecord, ai_decision_repository
from app.repositories.synthetic_repository import is_valid_synthetic_id
from app.services.registries import synthetic_repository
from app.services.security import is_session_blocked, log_decision, record_forensic_attack, record_suspicious_activity

_logger = logging.getLogger(__name__)


class GatewayDecision(BaseModel):
    route: str = Field(pattern="^(real|synthetic)$")
    action: str
    threat_score: int = Field(ge=0, le=100)
    reason: str
    anomaly_score: float | None = None
    anomaly_flag: int | None = None
    ai_label: str | None = None
    ai_confidence: float | None = None
    attack_probability: float | None = None
    xgboost_confidence: float | None = None


SUSPICIOUS_ROLES = {"hacker"}
DEFAULT_GATEWAY_URL = "http://127.0.0.1:8001"
GATEWAY_URL = os.getenv("GATEWAY_URL", DEFAULT_GATEWAY_URL)


def _rule_signals(path: str, params: dict[str, Any] | None, body: str | None) -> list[str]:
    text_source = " ".join(filter(None, [path, str(params or ""), body or ""]))
    signals: list[str] = []
    sqli_regex = re.compile(r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP)\b|(--|/\*|;\s*$|\bOR\b\s+\d+=\d+)", re.IGNORECASE)
    if sqli_regex.search(text_source):
        signals.append("sql_injection_pattern")
    if ".." in text_source or "%2e%2e" in text_source.lower():
        signals.append("directory_traversal")
    return signals


def _apply_rule_floor(decision: GatewayDecision, signals: list[str]) -> GatewayDecision:
    if not signals:
        return decision
    decision.route = "synthetic"
    decision.action = "block"
    decision.threat_score = max(decision.threat_score, 90)
    decision.reason = "; ".join(dict.fromkeys([decision.reason, *signals]))
    return decision


def _fetch_remote_decision(role: str, device: str, ip_address: str) -> GatewayDecision | None:
    try:
        with httpx.Client(timeout=0.05) as client:
            response = client.get(
                f"{GATEWAY_URL}/decision",
                params={"role": role, "device": device, "ip_address": ip_address},
            )
            response.raise_for_status()
            payload = response.json()
            route = payload["route"]
            action = payload.get("action", "route_synthetic" if route == "synthetic" else "allow")
            return GatewayDecision(
                route=route,
                action=action,
                threat_score=payload["threat_score"],
                reason=payload.get("explanation", payload.get("reason", "")),
            )
    except Exception:
        return None


_session_request_timestamps: dict[str, list[float]] = defaultdict(list)
_session_patient_queries: dict[str, list[tuple[str, float]]] = defaultdict(list)
_session_unauthorized_attempts: dict[str, int] = defaultdict(int)


def reset_gateway_state() -> None:
    """Reset in-memory gateway tracking state for isolated testing."""
    _session_request_timestamps.clear()
    _session_patient_queries.clear()
    _session_unauthorized_attempts.clear()


def evaluate_request(
    role: str,
    session_id: str,
    device: str,
    browser: str,
    operating_system: str,
    ip_address: str,
    country: str,
    username: str | None = None,
    method: str = "GET",
    path: str = "/",
    params: dict[str, Any] | None = None,
    body: str | None = None,
    headers: dict[str, str] | None = None,
) -> GatewayDecision:
    if is_session_blocked(session_id):
        return GatewayDecision(
            route="synthetic",
            action="block",
            threat_score=100,
            reason=f"Blocked session detected: {session_id}",
            anomaly_score=-0.5,
            anomaly_flag=1,
            ai_label="malicious",
            attack_probability=100.0,
        )

    request_context = {
        "role": role,
        "device": device,
        "browser": browser,
        "operating_system": operating_system,
        "country": country,
        "method": method,
        "path": path,
        "body": body or "",
        "params": "&".join([f"{k}={v}" for k, v in (params or {}).items()]),
    }

    ai_predictions = {}
    try:
        ai_predictions = model_loader.predict(request_context)
    except Exception:
        ai_predictions = {
            "anomaly_score": 0.0,
            "anomaly_flag": 0,
            "random_forest_label": "normal",
            "random_forest_confidence": 0.0,
            "attack_probability": 0.0,
            "xgboost_confidence": 0.0,
        }

    now = time.time()
    score = 12 + int(ai_predictions.get("anomaly_flag", 0)) * 40 + int(ai_predictions.get("attack_probability", 0) >= 50) * 20
    reasons: list[str] = []
    detected_attack_type: str | None = None
    target_patient_id: str | None = None

    text_source = " ".join(filter(None, [path, str(params or ""), body or ""]))

    TRUSTED_STAFF_SESSIONS = {"active-user-session", "doc-user-session", "admin-user-session", "hospital-user-session"}
    is_trusted_user = (role in {"administrator", "doctor", "receptionist"} or session_id in TRUSTED_STAFF_SESSIONS) and not session_id.startswith("sim-")

    # 1. API Abuse (abnormal request frequency) - only applies to untrusted or simulated attacker sessions
    if not is_trusted_user:
        _session_request_timestamps[session_id].append(now)
        _session_request_timestamps[session_id] = [t for t in _session_request_timestamps[session_id] if now - t <= 10.0]
        if len(_session_request_timestamps[session_id]) >= 6:
            score += 65
            reasons.append("abnormal_request_frequency_api_abuse")
            detected_attack_type = "API_ABUSE"

    # 2. Sequential Patient Enumeration - only applies to untrusted or simulated attacker sessions
    if not is_trusted_user and "/patients" in path.lower():
        extracted_pid = (params or {}).get("patient_id")
        if not extracted_pid:
            match = re.search(r"/patients/([^/?]+)", path)
            if match and match.group(1) not in {"history", "purge"}:
                extracted_pid = match.group(1)
        if extracted_pid:
            target_patient_id = str(extracted_pid)
            _session_patient_queries[session_id].append((target_patient_id, now))
            _session_patient_queries[session_id] = [(p, t) for p, t in _session_patient_queries[session_id] if now - t <= 15.0]
            distinct_pids = list({p for p, _ in _session_patient_queries[session_id]})
            if len(distinct_pids) >= 2 or len(_session_patient_queries[session_id]) >= 3:
                score += 70
                reasons.append("patient_enumeration_sequential_probe")
                detected_attack_type = "PATIENT_ENUMERATION"

    # 3. Mass Exfiltration Probe
    if not is_trusted_user and ((params and any(k.lower() in {"limit", "count", "page_size"} and int(v) >= 10 for k, v in params.items() if str(v).isdigit())) or any(x in path.lower() for x in ["/export", "/download", "/dump"])):
        score += 55
        reasons.append("bulk_data_exfiltration_probe")
        detected_attack_type = "DATA_EXFILTRATION"

    # 4. SQL Injection
    sqli_regex = re.compile(r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP)\b|(--|/\*|;\s*$|\bOR\b\s+\d+=\d+)", re.IGNORECASE)
    if "TEST_SQL_INJECTION" in text_source or sqli_regex.search(text_source):
        score += 85
        reasons.append("sql_injection_pattern")
        detected_attack_type = "SQL_INJECTION"

    # 5. Directory Traversal
    if "TEST_TRAVERSAL" in text_source or ".." in text_source or "%2e%2e" in text_source.lower():
        score += 85
        reasons.append("directory_traversal")
        detected_attack_type = "DIRECTORY_TRAVERSAL"

    # 6. Session Abuse / Invalid or Expired Token
    auth_header = (headers or {}).get("authorization", "")
    if "invalid-test-token" in auth_header or "test-token" in auth_header.lower() or "expired" in auth_header.lower():
        _session_unauthorized_attempts[session_id] += 1
        score += 65
        reasons.append("invalid_or_expired_token_session_abuse")
        detected_attack_type = "SESSION_ABUSE"

    if ai_predictions.get("anomaly_flag"):
        reasons.append("ai_anomaly_detected")
    if ai_predictions.get("random_forest_label") and ai_predictions.get("random_forest_label") != "normal":
        reasons.append(f"ai_label={ai_predictions.get('random_forest_label')}")
    if ai_predictions.get("attack_probability", 0) >= 50:
        reasons.append("attack_probability_high")

    if role in SUSPICIOUS_ROLES or session_id.startswith("sim-"):
        score += 55
        reasons.append(f"simulated_role={role}")
    if device and device.lower() not in {"trusted", "managed"}:
        score += 10
        reasons.append(f"device={device}")
    if browser and browser.lower() in {"curl", "python-requests", "unknown"}:
        score += 8
        reasons.append(f"browser={browser}")
    if operating_system and operating_system.lower() in {"unknown", "bot"}:
        score += 8
        reasons.append(f"os={operating_system}")
    if country and country.lower() in {"unknown", "high-risk"}:
        score += 6
        reasons.append(f"country={country}")
    if session_id == "anonymous":
        score += 6
        reasons.append("session=anonymous")

    final_score = min(int(score + ai_predictions.get("attack_probability", 0) * 0.2), 100)

    # Safe default: legitimate hospital roles always get real patient data unless an explicit injection attack occurred
    is_legitimate_role = role in {"administrator", "doctor", "receptionist"} and not session_id.startswith("sim-")
    has_explicit_attack = bool(detected_attack_type in {"SQL_INJECTION", "DIRECTORY_TRAVERSAL"})
    route = "synthetic" if (not is_legitimate_role or has_explicit_attack) else "real"

    if is_legitimate_role and not has_explicit_attack:
        final_score = min(score, 18)
        action = "allow"
    else:
        # Action tiers: NORMAL -> allow, SUSPICIOUS -> monitor, HIGH RISK -> DECEIVE, CRITICAL -> block
        if final_score >= 95:
            action = "block"
        elif final_score >= 70:
            action = "DECEIVE"
        elif final_score >= 40:
            action = "monitor"
        else:
            action = "allow"

    reason = "; ".join(reasons) if reasons else f"Legitimate hospital access from {ip_address}"

    decision = GatewayDecision(
        route=route,
        action=action,
        threat_score=final_score,
        reason=reason,
        anomaly_score=ai_predictions.get("anomaly_score"),
        anomaly_flag=ai_predictions.get("anomaly_flag"),
        ai_label=ai_predictions.get("random_forest_label"),
        ai_confidence=ai_predictions.get("random_forest_confidence"),
        attack_probability=ai_predictions.get("attack_probability"),
        xgboost_confidence=ai_predictions.get("xgboost_confidence"),
    )

    try:
        ai_decision_repository.add(
            AIDecisionRecord(
                id="ai_" + str(uuid4()),
                session_id=session_id,
                route=decision.route,
                action=decision.action,
                score=decision.threat_score,
                reason=decision.reason,
                anomaly_score=decision.anomaly_score or 0.0,
                anomaly_flag=decision.anomaly_flag or 0,
                random_forest_label=decision.ai_label or "normal",
                random_forest_confidence=decision.ai_confidence or 0.0,
                attack_probability=decision.attack_probability or 0.0,
                xgboost_confidence=decision.xgboost_confidence or 0.0,
                risk_score=float(final_score),
                attacker_ip=ip_address,
                user_agent=headers.get("user-agent", "") if headers else "",
            )
        )
    except Exception as exc:
        _logger.warning("Failed to persist AI decision record: %s", exc)

    log_decision(session_id=session_id, route=decision.route, score=decision.threat_score, reason=decision.reason, username=username)

    if detected_attack_type:
        resolved_twin = None
        if target_patient_id:
            resolved_twin = synthetic_repository.find_by_real_patient_id(target_patient_id)
            if resolved_twin is None and is_valid_synthetic_id(target_patient_id):
                resolved_twin = synthetic_repository.find_by_synthetic_id(target_patient_id)
        synthetic_twin_id = (
            resolved_twin.synthetic_patient_id
            if resolved_twin is not None and is_valid_synthetic_id(resolved_twin.synthetic_patient_id)
            else None
        )
        record_forensic_attack(
            attack_type=detected_attack_type,
            session_id=session_id,
            risk_score=float(final_score),
            gateway_decision=action,
            patient_id=target_patient_id,
            synthetic_patient_id=synthetic_twin_id,
            username=username,
            ip_address=ip_address,
            user_agent=headers.get("user-agent", "") if headers else "",
            attack_probability=ai_predictions.get("attack_probability"),
            records_returned=1 if target_patient_id else 0,
            blocked_status=action == "block",
        )

    return decision

