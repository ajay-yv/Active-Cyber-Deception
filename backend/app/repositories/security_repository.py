from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from uuid import uuid4

from sqlalchemy import func

from app.db.engines import SecuritySessionLocal
from app.models.security import FailedLoginAttempt, ForensicAttackRecord, SecurityEventRecord


@dataclass(frozen=True)
class SecurityEvent:
    id: str
    event_type: str
    details: str
    created_at: str = ""


class SecurityRepository:
    def clear_failed_login_attempts(self) -> None:
        with SecuritySessionLocal() as session:
            session.query(FailedLoginAttempt).delete(synchronize_session=False)
            session.commit()

    def record_failed_login(
        self,
        username: str,
        ip_address: str,
        threshold: int,
        window: timedelta,
        now: datetime | None = None,
    ) -> tuple[int, bool]:
        now = now or datetime.now(timezone.utc)
        cutoff = now - window
        username_key_hash = sha256(username.strip().casefold().encode("utf-8")).hexdigest()
        attempt = FailedLoginAttempt(
            id=str(uuid4()),
            username_key_hash=username_key_hash,
            ip_address=ip_address,
            created_at=now,
        )

        with SecuritySessionLocal() as session:
            session.query(FailedLoginAttempt).filter(FailedLoginAttempt.created_at < cutoff).delete(
                synchronize_session=False
            )
            session.add(attempt)
            session.flush()
            recent_attempts = session.query(FailedLoginAttempt).filter(
                FailedLoginAttempt.username_key_hash == username_key_hash,
                FailedLoginAttempt.ip_address == ip_address,
                FailedLoginAttempt.created_at >= cutoff,
            )
            count = int(recent_attempts.with_entities(func.count(FailedLoginAttempt.id)).scalar() or 0)
            alert_already_sent = recent_attempts.filter(FailedLoginAttempt.alert_sent.is_(True)).first() is not None
            should_alert = count >= threshold and not alert_already_sent
            if should_alert:
                attempt.alert_sent = True
            session.commit()

        return count, should_alert

    def append(self, event_type: str, details: str) -> SecurityEvent:
        event = SecurityEvent(id=str(uuid4()), event_type=event_type, details=details)
        with SecuritySessionLocal() as session:
            session.add(SecurityEventRecord(id=event.id, event_type=event.event_type, details=event.details))
            session.commit()
        return event

    def list_all(self) -> list[SecurityEvent]:
        with SecuritySessionLocal() as session:
            rows = session.query(SecurityEventRecord).order_by(SecurityEventRecord.created_at.asc()).all()
        return [
            SecurityEvent(
                id=row.id,
                event_type=row.event_type,
                details=row.details,
                created_at=row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at or ""),
            )
            for row in rows
        ]

    def find_by_event_type(self, event_type: str) -> list[SecurityEvent]:
        with SecuritySessionLocal() as session:
            rows = (
                session.query(SecurityEventRecord)
                .filter(SecurityEventRecord.event_type == event_type)
                .order_by(SecurityEventRecord.created_at.asc())
                .all()
            )
        return [
            SecurityEvent(
                id=row.id,
                event_type=row.event_type,
                details=row.details,
                created_at=row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at or ""),
            )
            for row in rows
        ]

    def find_by_session(self, session_id: str) -> list[SecurityEvent]:
        with SecuritySessionLocal() as session:
            rows = (
                session.query(SecurityEventRecord)
                .filter(SecurityEventRecord.details.contains(f"session={session_id}"))
                .order_by(SecurityEventRecord.created_at.asc())
                .all()
            )
        return [
            SecurityEvent(
                id=row.id,
                event_type=row.event_type,
                details=row.details,
                created_at=row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at or ""),
            )
            for row in rows
        ]

    def recent(self, limit: int = 10) -> list[SecurityEvent]:
        with SecuritySessionLocal() as session:
            rows = (
                session.query(SecurityEventRecord)
                .order_by(SecurityEventRecord.created_at.desc())
                .limit(limit)
                .all()
            )
        return [
            SecurityEvent(
                id=row.id,
                event_type=row.event_type,
                details=row.details,
                created_at=row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at or ""),
            )
            for row in reversed(rows)
        ]

    def add_forensic_record(self, record_data: dict) -> dict:
        attack_id = record_data.get("attack_id") or f"atk_{uuid4().hex[:12]}"
        row = ForensicAttackRecord(
            attack_id=attack_id,
            attack_type=record_data.get("attack_type", "UNKNOWN_ATTACK"),
            patient_id=record_data.get("patient_id"),
            synthetic_patient_id=record_data.get("synthetic_patient_id"),
            session_id=record_data.get("session_id", "unknown-session"),
            username=record_data.get("username"),
            ip_address=record_data.get("ip_address", "127.0.0.1"),
            user_agent=record_data.get("user_agent", ""),
            timestamp=record_data.get("timestamp", ""),
            risk_score=float(record_data.get("risk_score", 0.0)),
            attack_probability=float(record_data["attack_probability"]) if record_data.get("attack_probability") is not None else None,
            gateway_decision=record_data.get("gateway_decision", "MONITOR"),
            watermark_id=record_data.get("watermark_id"),
            records_returned=int(record_data.get("records_returned", 0)) if record_data.get("records_returned") is not None else 0,
            records_requested=int(record_data.get("records_requested", 0)) if record_data.get("records_requested") is not None else 0,
            requested_fields=json.dumps(record_data.get("requested_fields", [])),
            blocked_status=bool(record_data.get("blocked_status", False)),
        )
        with SecuritySessionLocal() as session:
            session.merge(row)
            session.commit()
        return self._forensic_to_dict(row)

    def _forensic_to_dict(self, row: ForensicAttackRecord) -> dict:
        return {
            "attack_id": row.attack_id,
            "attack_type": row.attack_type,
            "patient_id": row.patient_id,
            "synthetic_patient_id": row.synthetic_patient_id,
            "session_id": row.session_id,
            "username": row.username,
            "ip_address": row.ip_address,
            "user_agent": row.user_agent,
            "timestamp": row.timestamp,
            "risk_score": row.risk_score,
            "attack_probability": row.attack_probability,
            "gateway_decision": row.gateway_decision,
            "watermark_id": row.watermark_id,
            "records_returned": row.records_returned,
            "records_requested": row.records_requested,
            "requested_fields": json.loads(row.requested_fields or "[]"),
            "blocked_status": row.blocked_status,
            "created_at": row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at or ""),
        }

    def list_forensic_records(self, limit: int = 50) -> list[dict]:
        with SecuritySessionLocal() as session:
            rows = (
                session.query(ForensicAttackRecord)
                .order_by(ForensicAttackRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._forensic_to_dict(r) for r in rows]

    def get_forensic_record_by_attack_id(self, attack_id: str) -> dict | None:
        with SecuritySessionLocal() as session:
            row = session.query(ForensicAttackRecord).filter(ForensicAttackRecord.attack_id == attack_id).first()
            return self._forensic_to_dict(row) if row else None

    def recent_forensic_records(self, limit: int = 15) -> list[dict]:
        return self.list_forensic_records(limit=limit)
