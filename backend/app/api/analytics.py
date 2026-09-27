from fastapi import APIRouter, Depends

from app.core.dependencies import require_roles
from app.repositories.ai_decision_repository import ai_decision_repository
from app.services.analytics import build_patient_analytics, build_security_metrics
from app.services.registries import synthetic_repository

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    return {
        "patient_metrics": build_patient_analytics(),
        "security_metrics": build_security_metrics(),
    }


@router.get("/synthetic")
def list_synthetic(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    """Return a list of synthetic twin forensic records for inspection."""
    records = [r.model_dump() for r in synthetic_repository.list_all()]
    return {"synthetic": records}


@router.get("/ai-decisions")
def list_ai_decisions(_: object = Depends(require_roles("administrator", "doctor", "receptionist"))) -> dict:
    records = [r.__dict__ for r in ai_decision_repository.list_all()]
    return {"ai_decisions": records}
