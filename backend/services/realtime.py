"""In-process WebSocket fan-out for real-time dashboard updates.

A single :class:`ConnectionManager` maps ``user_id -> set[WebSocket]`` and
broadcasts an event only to the sockets belonging to that user. It is a plain
in-process registry (no Redis / message broker): the webhook ingest, the AI
pipeline, the Gmail poller and the request handlers all run in the same event
loop, so one registry is enough for a single-process deployment.

Security: connections are keyed by the authenticated user id resolved from the
session cookie, so User A can never receive User B's events. Emitting is
best-effort — a broadcast failure must never break message ingestion or AI
persistence — so every send is bounded by a short timeout and dead sockets are
pruned instead of raising.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

# A slow/dead client must not stall ingestion, so each send is time-bounded.
SEND_TIMEOUT_SECONDS = 2.0

# Event type strings shared with the frontend.
MESSAGE_CREATED = "message.created"
MESSAGE_UPDATED = "message.updated"


class ConnectionManager:
    """Tracks live WebSocket connections, scoped per user."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[Any]] = {}

    async def connect(self, user_id: str, websocket: Any) -> None:
        self._connections.setdefault(str(user_id), set()).add(websocket)

    async def disconnect(self, user_id: str, websocket: Any) -> None:
        user_id = str(user_id)
        sockets = self._connections.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    def connection_count(self, user_id: Optional[str] = None) -> int:
        if user_id is None:
            return sum(len(sockets) for sockets in self._connections.values())
        return len(self._connections.get(str(user_id), ()))

    async def broadcast(self, user_id: str, payload: dict) -> int:
        """Send *payload* to every live socket of *user_id*.

        Returns the number of sockets the payload reached. Dead sockets are
        dropped. Never raises.
        """
        sockets = list(self._connections.get(str(user_id), ()))
        if not sockets:
            return 0

        delivered = 0
        dead: list[Any] = []
        for websocket in sockets:
            try:
                await asyncio.wait_for(
                    websocket.send_json(payload),
                    timeout=SEND_TIMEOUT_SECONDS,
                )
                delivered += 1
            except Exception:
                logger.debug(
                    "Dropping unreachable WebSocket for user %s", user_id
                )
                dead.append(websocket)

        for websocket in dead:
            await self.disconnect(user_id, websocket)

        return delivered


manager = ConnectionManager()


async def emit_message_event(
    user_id: Optional[str], event_type: str, message_id: Optional[str]
) -> int:
    """Notify a user's dashboard that a message was created/updated.

    Fire-and-forget by contract: any failure is logged and swallowed so an
    ingestion path or the AI pipeline is never affected by realtime delivery.
    """
    if not user_id or not message_id:
        return 0
    payload = {
        "type": event_type,
        "message_id": str(message_id),
        "user_id": str(user_id),
    }
    try:
        return await manager.broadcast(user_id, payload)
    except Exception:  # pragma: no cover - broadcast already guards per socket
        logger.warning(
            "Realtime emit failed (%s for %s)", event_type, message_id, exc_info=True
        )
        return 0
