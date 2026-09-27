from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, request_context_headers
from app.core.users import User
from app.services.gateway import evaluate_request

router = APIRouter()


@router.get("/gateway/decision")
def gateway_decision(
    current_user: User = Depends(get_current_user),
    context: dict[str, str] = Depends(request_context_headers),
) -> dict[str, str | int]:
    decision = evaluate_request(role=current_user.role, **context)
    return decision.model_dump()
