import asyncio
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class RealtimeConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            try:
                self.active_connections.remove(websocket)
            except ValueError:
                pass

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self.active_connections:
            return
        stale_connections: list[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await asyncio.wait_for(connection.send_json(message), timeout=1.0)
            except Exception:
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(connection)


manager = RealtimeConnectionManager()


def publish_event(event_type: str, payload: dict[str, Any]) -> None:
    if not manager.active_connections:
        return

    message = {"type": event_type, "payload": payload}
    target_loop = getattr(manager, "loop", None)

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if current_loop is not None and current_loop.is_running():
        current_loop.create_task(manager.broadcast(message))
    elif target_loop is not None and target_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(manager.broadcast(message), target_loop)
        except Exception:
            pass
