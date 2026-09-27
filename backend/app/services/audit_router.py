from fastapi import APIRouter, Depends

from app.core.dependencies import require_roles
from app.repositories.security_repository import SecurityRepository

router = APIRouter(prefix="/audit", tags=["audit"])
security_repository = SecurityRepository()


@router.get("/events")
def audit_events(_: object = Depends(require_roles("administrator"))) -> dict:
    return {"events": [event.__dict__ for event in security_repository.list_all() if event.event_type == "audit"]}
