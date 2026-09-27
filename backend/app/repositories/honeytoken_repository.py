from dataclasses import dataclass
from uuid import uuid4

from app.db.engines import SyntheticSessionLocal
from app.models.synthetic import Honeytoken as HoneytokenModel


@dataclass(frozen=True)
class HoneytokenRecord:
    id: str
    token_type: str
    value: str
    session_id: str
    twin_id: str


class HoneytokenRepository:
    def add(self, record: HoneytokenRecord) -> HoneytokenRecord:
        with SyntheticSessionLocal() as session:
            session.merge(
                HoneytokenModel(
                    id=record.id,
                    token_type=record.token_type,
                    value=record.value,
                    session_id=record.session_id,
                    twin_id=record.twin_id,
                )
            )
            session.commit()
        return record

    def list_all(self) -> list[HoneytokenRecord]:
        with SyntheticSessionLocal() as session:
            rows = session.query(HoneytokenModel).order_by(HoneytokenModel.id.asc()).all()
        return [
            HoneytokenRecord(
                id=row.id,
                token_type=row.token_type,
                value=row.value,
                session_id=row.session_id,
                twin_id=row.twin_id,
            )
            for row in rows
        ]

    def find_by_session(self, session_id: str) -> list[HoneytokenRecord]:
        with SyntheticSessionLocal() as session:
            rows = session.query(HoneytokenModel).filter(HoneytokenModel.session_id == session_id).all()
        return [
            HoneytokenRecord(
                id=row.id,
                token_type=row.token_type,
                value=row.value,
                session_id=row.session_id,
                twin_id=row.twin_id,
            )
            for row in rows
        ]
