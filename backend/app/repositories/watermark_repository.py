from dataclasses import dataclass

from app.db.engines import SecuritySessionLocal
from app.models.security import Watermark as WatermarkModel


class WatermarkRepository:
    def __init__(self) -> None:
        self._session_factory = SecuritySessionLocal

    def add(self, record: "WatermarkRecord") -> "WatermarkRecord":
        with self._session_factory() as session:
            existing = (
                session.query(WatermarkModel)
                .filter(WatermarkModel.source_id == record.source_id)
                .filter(WatermarkModel.source_type == record.source_type)
                .first()
            )
            if existing is not None:
                existing.watermark_id = record.watermark_id
                existing.hospital_id = record.hospital_id
                existing.timestamp = record.timestamp
                existing.session_id = record.session_id
                existing.watermark_text = record.watermark_text
                existing.watermark_fingerprint = record.watermark_fingerprint
                session.add(existing)
                session.commit()
                return WatermarkRecord(
                    id=existing.id,
                    watermark_id=existing.watermark_id,
                    source_id=existing.source_id,
                    source_type=existing.source_type,
                    hospital_id=existing.hospital_id,
                    timestamp=existing.timestamp,
                    session_id=existing.session_id,
                    watermark_text=existing.watermark_text,
                    watermark_fingerprint=existing.watermark_fingerprint,
                )

            session.add(
                WatermarkModel(
                    id=record.id,
                    watermark_id=record.watermark_id,
                    source_id=record.source_id,
                    source_type=record.source_type,
                    hospital_id=record.hospital_id,
                    timestamp=record.timestamp,
                    session_id=record.session_id,
                    watermark_text=record.watermark_text,
                    watermark_fingerprint=record.watermark_fingerprint,
                )
            )
            session.commit()
        return record

    def list_all(self) -> list["WatermarkRecord"]:
        with self._session_factory() as session:
            rows = session.query(WatermarkModel).order_by(WatermarkModel.timestamp.asc()).all()
        return [
            WatermarkRecord(
                id=row.id,
                watermark_id=row.watermark_id,
                source_id=row.source_id,
                source_type=row.source_type,
                hospital_id=row.hospital_id,
                timestamp=row.timestamp,
                session_id=row.session_id,
                watermark_text=row.watermark_text,
                watermark_fingerprint=row.watermark_fingerprint,
            )
            for row in rows
        ]

    def find_by_watermark_id(self, watermark_id: str) -> "WatermarkRecord | None":
        with self._session_factory() as session:
            row = session.query(WatermarkModel).filter(WatermarkModel.watermark_id == watermark_id).first()
        if row is None:
            return None
        return WatermarkRecord(
            id=row.id,
            watermark_id=row.watermark_id,
            source_id=row.source_id,
            source_type=row.source_type,
            hospital_id=row.hospital_id,
            timestamp=row.timestamp,
            session_id=row.session_id,
            watermark_text=row.watermark_text,
            watermark_fingerprint=row.watermark_fingerprint,
        )

    def find_by_session(self, session_id: str) -> list["WatermarkRecord"]:
        with self._session_factory() as session:
            rows = session.query(WatermarkModel).filter(WatermarkModel.session_id == session_id).all()
        return [
            WatermarkRecord(
                id=row.id,
                watermark_id=row.watermark_id,
                source_id=row.source_id,
                source_type=row.source_type,
                hospital_id=row.hospital_id,
                timestamp=row.timestamp,
                session_id=row.session_id,
                watermark_text=row.watermark_text,
                watermark_fingerprint=row.watermark_fingerprint,
            )
            for row in rows
        ]

    def find_by_source_id(self, source_id: str, source_type: str | None = None) -> "WatermarkRecord | None":
        with self._session_factory() as session:
            query = session.query(WatermarkModel).filter(WatermarkModel.source_id == source_id)
            if source_type is not None:
                query = query.filter(WatermarkModel.source_type == source_type)
            row = query.first()
        if row is None:
            return None
        return WatermarkRecord(
            id=row.id,
            watermark_id=row.watermark_id,
            source_id=row.source_id,
            source_type=row.source_type,
            hospital_id=row.hospital_id,
            timestamp=row.timestamp,
            session_id=row.session_id,
            watermark_text=row.watermark_text,
            watermark_fingerprint=row.watermark_fingerprint,
        )




@dataclass(frozen=True)
class WatermarkRecord:
    id: str
    watermark_id: str
    source_id: str
    source_type: str
    hospital_id: str
    timestamp: str
    session_id: str
    watermark_text: str
    watermark_fingerprint: str
    forensic_link: str = ""
    forensic_forensics_link: str = ""




watermark_repository = WatermarkRepository()
