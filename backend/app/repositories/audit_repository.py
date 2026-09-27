from uuid import uuid4

from app.db.engines import SecuritySessionLocal
from app.models.security import AuditLog


class AuditRepository:
    def append(self, actor: str, action: str, details: str) -> AuditLog:
        audit = AuditLog(id=str(uuid4()), actor=actor, action=action, details=details)
        with SecuritySessionLocal() as session:
            session.add(audit)
            session.commit()
            session.refresh(audit)
        return audit

    def list_all(self) -> list[AuditLog]:
        with SecuritySessionLocal() as session:
            return session.query(AuditLog).order_by(AuditLog.created_at.asc()).all()
