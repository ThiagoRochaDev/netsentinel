import asyncio
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger("netsentinel.ws")


class WebSocketManager:
    """Broadcast hub for live updates. One multiplexed channel; each message
    carries a `type` field (new_alert | new_device | suricata_event | flow_tick)
    so both the web frontend and the TUI can subscribe to the same feed."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)

    async def broadcast(self, message_type: str, payload: dict) -> None:
        data = json.dumps({"type": message_type, "payload": payload})
        async with self._lock:
            dead = set()
            for ws in self._connections:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.add(ws)
            self._connections -= dead


ws_manager = WebSocketManager()
