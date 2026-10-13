"""WebSocket endpoint for real-time dashboard updates.

The browser sends the same httpOnly session cookie (``cai_token``) on the
WebSocket handshake that it sends on REST calls, so the connection is bound to
the logged-in user. Events are only ever delivered to that user's sockets —
never globally.

Because cookies are host-scoped (not port-scoped) the session cookie is sent to
the backend on a different port during local development, but some setups
(proxy/browser edge cases) drop it on the WebSocket handshake. For that case an
**opt-in, development-only** fallback exists: the authenticated frontend asks
``GET /ws-token`` for a short-lived, purpose-scoped token and passes it as
``?token=`` on the handshake. It is disabled by default and must be enabled with
``WS_ALLOW_QUERY_TOKEN=true`` so production authentication stays cookie-only.

Protocol: the server sends JSON ``message.created`` / ``message.updated``
payloads. The client only sends keep-alive pings (any inbound text is ignored).
"""

import logging
import os

from bson import ObjectId
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from database import users_collection
from dependencies import get_current_user
from services.realtime import manager
from services.security import (
    TOKEN_COOKIE_NAME,
    create_ws_token,
    decode_token,
    decode_ws_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])

# 1008 = policy violation (the WebSocket close code for auth failures).
WS_CLOSE_UNAUTHORIZED = 1008

_TRUTHY = {"1", "true", "yes", "on"}


def query_token_allowed() -> bool:
    """Whether a ``?token=`` handshake token may be accepted (local dev).

    Off unless ``WS_ALLOW_QUERY_TOKEN`` is truthy, so production keeps using
    the session cookie exclusively.
    """
    value = os.getenv("WS_ALLOW_QUERY_TOKEN", "").strip().lower()
    return value in _TRUTHY


async def _user_exists(user_id: str | None) -> str | None:
    """Return ``user_id`` when it names a real user, else ``None``.

    Mirrors :func:`dependencies.get_current_user`'s existence check.
    """
    if not user_id or not ObjectId.is_valid(user_id):
        return None
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    return str(user_id)


async def authenticate_websocket(websocket: WebSocket) -> str | None:
    """Resolve the authenticated user id from the handshake.

    Tries the session cookie first (every environment). Falls back to a
    short-lived ``?token=`` only when ``WS_ALLOW_QUERY_TOKEN`` is enabled.
    Returns ``None`` for a missing/invalid credential or an unknown user.
    """
    cookie_user = await _user_exists(
        decode_token(websocket.cookies.get(TOKEN_COOKIE_NAME) or "")
    )
    if cookie_user:
        return cookie_user

    if query_token_allowed():
        query_user = await _user_exists(
            decode_ws_token(websocket.query_params.get("token") or "")
        )
        if query_user:
            return query_user

    return None


@router.get("/ws-token")
async def ws_token(current_user: dict = Depends(get_current_user)):
    """Mint a short-lived WebSocket token for the logged-in user.

    Auth is the normal REST cookie; the returned token is only useful for the
    local ``?token=`` handshake fallback.
    """
    return {"token": create_ws_token(str(current_user["_id"]))}


@router.websocket("/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    user_id = await authenticate_websocket(websocket)
    if user_id is None:
        # Reject before accept — the handshake fails (no events leak).
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)
    logger.info("WebSocket connected for user %s", user_id)
    try:
        while True:
            # Keep the connection open; the client's payloads are ignored.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.warning(
            "WebSocket error for user %s", user_id, exc_info=True
        )
    finally:
        await manager.disconnect(user_id, websocket)
        logger.info("WebSocket disconnected for user %s", user_id)
