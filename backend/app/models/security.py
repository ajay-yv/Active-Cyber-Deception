from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SecurityBase


class SecurityEventRecord(SecurityBase):
    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserAccount(SecurityBase):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(128), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    patient_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(nullable=False, server_default="0")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(SecurityBase):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(nullable=False, server_default="0")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginLog(SecurityBase):
    __tablename__ = "login_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    device: Mapped[str] = mapped_column(String(255), nullable=False)
    browser: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ThreatLog(SecurityBase):
    __tablename__ = "threat_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    threat_score: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class AttackLog(SecurityBase):
    __tablename__ = "attack_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(SecurityBase):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIDecision(SecurityBase):
    __tablename__ = "ai_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    route: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anomaly_flag: Mapped[int] = mapped_column(nullable=False, default=0)
    random_forest_label: Mapped[str] = mapped_column(String(64), nullable=False, default="normal")
    random_forest_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attack_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    xgboost_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attacker_ip: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    user_agent: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionHistory(SecurityBase):
    __tablename__ = "session_history"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[str] = mapped_column(String(64), nullable=True)


class BreachLog(SecurityBase):
    __tablename__ = "breach_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    hacker_id: Mapped[str] = mapped_column(String(64), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    target_patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_request: Mapped[bool] = mapped_column(nullable=False)
    request_payload: Mapped[str] = mapped_column(Text, nullable=False)
    response_payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Watermark(SecurityBase):
    __tablename__ = "watermarks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    watermark_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="synthetic")
    hospital_id: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    watermark_text: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    watermark_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, default="")


class ForensicAttackRecord(SecurityBase):
    __tablename__ = "forensic_records"

    attack_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    attack_type: Mapped[str] = mapped_column(String(64), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=True)
    synthetic_patient_id: Mapped[str] = mapped_column(String(64), nullable=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    username: Mapped[str] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, default="127.0.0.1")
    user_agent: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attack_probability: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    gateway_decision: Mapped[str] = mapped_column(String(64), nullable=False, default="MONITOR")
    watermark_id: Mapped[str] = mapped_column(String(128), nullable=True)
    records_returned: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    blocked_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

