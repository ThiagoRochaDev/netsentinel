from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.security import COOKIE_NAME, decode_access_token
from app.ws_manager import ws_manager

router = APIRouter(tags=["ws"])


@router.websocket("/api/ws/live")
async def ws_live(websocket: WebSocket):
    token = websocket.cookies.get(COOKIE_NAME)
    if not token or not decode_access_token(token):
        await websocket.close(code=4401)
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            # Client doesn't need to send anything; just keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket)
