from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.repositories.user_repository import user_repository
from app.services.realtime import manager
from app.services.security import security_repository

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None) -> None:
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    try:
        username = str(decode_token(token).get("sub", ""))
        user = user_repository.get_by_username(username)
    except Exception:
        user = None
    if user is None or user.role not in {"administrator", "doctor", "receptionist"} or getattr(user, "is_blocked", False):
        await websocket.close(code=1008, reason="Defender role required")
        return

    await manager.connect(websocket)
    try:
        recent_events = [
            {"event_type": event.event_type, "details": event.details}
            for event in security_repository.recent(10)
        ]
        await websocket.send_json({"type": "snapshot", "payload": {"events": recent_events}})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
