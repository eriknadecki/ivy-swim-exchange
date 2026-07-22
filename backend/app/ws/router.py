import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import TokenType, decode_token
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    try:
        if token is None:
            raise ValueError("missing token")
        payload = decode_token(token)
        if payload.get("type") != TokenType.access.value:
            raise ValueError("not an access token")
        user_id = payload["sub"]
    except (jwt.PyJWTError, ValueError):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    own_channel = f"user:{user_id}"
    await manager.subscribe(websocket, own_channel)

    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("type")
            channel = message.get("channel")
            if not channel or channel == own_channel:
                continue
            if action == "subscribe":
                await manager.subscribe(websocket, channel)
            elif action == "unsubscribe":
                await manager.unsubscribe(websocket, channel)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
