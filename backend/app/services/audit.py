from app.repositories.audit_repository import AuditRepository


audit_repository = AuditRepository()


def record_audit(actor: str, action: str, details: str) -> None:
    audit_repository.append(actor, action, details)
