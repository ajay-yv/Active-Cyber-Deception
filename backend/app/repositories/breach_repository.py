import json
from dataclasses import dataclass
from uuid import uuid4

from app.db.engines import SecuritySessionLocal
from app.models.security import BreachLog


@dataclass(frozen=True)
class BreachLogRecord:
    id: str
    session_id: str
    hacker_id: str
    query: str
    target_patient_id: str
    valid_request: bool
    request_payload: str
    response_payload: str
    created_at: str


class BreachRepository:
    def add(self, record: BreachLogRecord) -> BreachLogRecord:
        with SecuritySessionLocal() as session:
            row = BreachLog(
                id=record.id,
                session_id=record.session_id,
                hacker_id=record.hacker_id,
                query=record.query,
                target_patient_id=record.target_patient_id,
                valid_request=record.valid_request,
                request_payload=record.request_payload,
                response_payload=record.response_payload,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
        return record

    def list_all(self) -> list[BreachLogRecord]:
        with SecuritySessionLocal() as session:
            rows = session.query(BreachLog).order_by(BreachLog.created_at.desc()).all()
        return [
            BreachLogRecord(
                id=row.id,
                session_id=row.session_id,
                hacker_id=row.hacker_id,
                query=row.query,
                target_patient_id=row.target_patient_id,
                valid_request=row.valid_request,
                request_payload=row.request_payload,
                response_payload=row.response_payload,
                created_at=row.created_at.isoformat() if row.created_at is not None else '',
            )
            for row in rows
        ]
