"""Realtime WebSocket tests (feature: real-time dashboard updates).

Covers:
- the user-scoped ConnectionManager (fan-out + isolation + dead-socket pruning),
- the payload contract of ``emit_message_event``,
- WebSocket handshake authentication (cookie session),
- end-to-end emission on ingest (``message.created`` + ``message.updated``),
- cross-user isolation at the socket level.
"""

import asyncio
from datetime import datetime, timezone

import pytest
from bson import ObjectId
from starlette.websockets import WebSocketDisconnect

from services.realtime import (
    MESSAGE_CREATED,
    MESSAGE_UPDATED,
    ConnectionManager,
    emit_message_event,
    manager,
)
from services.security import (
    create_access_token,
    create_ws_token,
    decode_token,
    decode_ws_token,
)


# ── helpers ──────────────────────────────────────────────────


class _FakeWebSocket:
    """Minimal stand-in for a Starlette WebSocket."""

    def __init__(self, fail: bool = False):
        self.sent: list = []
        self.fail = fail

    async def send_json(self, payload: dict) -> None:
        if self.fail:
            raise RuntimeError("socket is gone")
        self.sent.append(payload)


def _insert_user(sync_db, email: str) -> str:
    uid = ObjectId()
    sync_db.users.insert_one(
        {
            "_id": uid,
            "name": "WS User",
            "email": email,
            "password_hash": "x",
            "created_at": datetime.now(timezone.utc),
        }
    )
    return str(uid)


def _patch_analysis(monkeypatch):
    """Replace the AI call so tests never touch the network."""

    async def fake_process(
        content,
        message_id=None,
        user_id=None,
        message_type="text",
        thread_id=None,
    ):
        return {
            "priority": "normal",
            "confidence": 0.9,
            "explanation": None,
            "summary": "ok",
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "needs_attention": False,
            "attention_reason": "",
            "provider": "test",
            "analyzed_at": None,
            "status": "completed",
        }

    monkeypatch.setattr("services.webhook_ingest.process_message", fake_process)


# ── ConnectionManager unit tests ─────────────────────────────


class TestConnectionManager:
    def test_broadcast_only_reaches_target_user(self):
        m = ConnectionManager()
        socket_a, socket_b = _FakeWebSocket(), _FakeWebSocket()

        async def scenario():
            await m.connect("user-a", socket_a)
            await m.connect("user-b", socket_b)
            return await m.broadcast("user-a", {"type": MESSAGE_CREATED})

        delivered = asyncio.run(scenario())

        assert delivered == 1
        assert socket_a.sent == [{"type": MESSAGE_CREATED}]
        assert socket_b.sent == []

    def test_broadcast_with_no_connections_is_noop(self):
        m = ConnectionManager()
        assert asyncio.run(m.broadcast("user", {"type": MESSAGE_CREATED})) == 0

    def test_broadcast_prunes_dead_sockets(self):
        m = ConnectionManager()
        live, dead = _FakeWebSocket(), _FakeWebSocket(fail=True)

        async def scenario():
            await m.connect("user-a", live)
            await m.connect("user-a", dead)
            delivered = await m.broadcast("user-a", {"type": MESSAGE_UPDATED})
            return delivered, m.connection_count("user-a")

        delivered, remaining = asyncio.run(scenario())

        assert delivered == 1
        assert live.sent == [{"type": MESSAGE_UPDATED}]
        assert remaining == 1

    def test_disconnect_removes_only_that_socket(self):
        m = ConnectionManager()
        first, second = _FakeWebSocket(), _FakeWebSocket()

        async def scenario():
            await m.connect("user-a", first)
            await m.connect("user-a", second)
            await m.disconnect("user-a", first)
            return m.connection_count("user-a")

        assert asyncio.run(scenario()) == 1


# ── emit_message_event contract ──────────────────────────────


class TestEmitMessageEvent:
    def test_payload_shape(self):
        socket = _FakeWebSocket()

        async def scenario():
            await manager.connect("u-emit", socket)
            try:
                return await emit_message_event("u-emit", MESSAGE_CREATED, "abc123")
            finally:
                await manager.disconnect("u-emit", socket)

        delivered = asyncio.run(scenario())

        assert delivered == 1
        assert socket.sent == [
            {
                "type": "message.created",
                "message_id": "abc123",
                "user_id": "u-emit",
            }
        ]

    def test_missing_arguments_are_ignored(self):
        delivered = asyncio.run(emit_message_event("user-a", MESSAGE_CREATED, None))
        assert delivered == 0
        assert asyncio.run(emit_message_event("", MESSAGE_UPDATED, "m1")) == 0


# ── WebSocket authentication ─────────────────────────────────


class TestWebSocketAuth:
    def test_rejects_missing_cookie(self, client):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws"):
                pass

    def test_rejects_malformed_token(self, client):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                "/ws", cookies={"cai_token": "not-a-real-jwt"}
            ):
                pass

    def test_rejects_unknown_user(self, client):
        token = create_access_token(str(ObjectId()))
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws", cookies={"cai_token": token}):
                pass

    def test_accepts_authenticated_user(self, client, sync_db):
        uid = _insert_user(sync_db, "ws-auth@example.com")
        token = create_access_token(uid)
        with client.websocket_connect("/ws", cookies={"cai_token": token}) as ws:
            ws.send_text("ping")


# ── Dev-only query-token fallback ────────────────────────────


class TestWsTokenFallback:
    def test_ws_token_endpoint_requires_auth(self, client):
        assert client.get("/ws-token").status_code == 401

    def test_ws_token_endpoint_returns_purpose_scoped_token(self, client, sync_db):
        uid = _insert_user(sync_db, "ws-token@example.com")
        session = create_access_token(uid)

        resp = client.get("/ws-token", cookies={"cai_token": session})
        assert resp.status_code == 200, resp.text
        ws_token = resp.json()["token"]

        assert decode_ws_token(ws_token) == uid
        # The short-lived WS token must never be replayable as a session.
        assert decode_token(ws_token) is None

    def test_query_token_accepted_when_enabled(self, client, sync_db, monkeypatch):
        monkeypatch.setenv("WS_ALLOW_QUERY_TOKEN", "true")
        uid = _insert_user(sync_db, "ws-query@example.com")
        ws_token = create_ws_token(uid)
        with client.websocket_connect(f"/ws?token={ws_token}") as ws:
            ws.send_text("ping")

    def test_query_token_rejected_when_disabled(self, client, sync_db, monkeypatch):
        monkeypatch.delenv("WS_ALLOW_QUERY_TOKEN", raising=False)
        uid = _insert_user(sync_db, "ws-query-off@example.com")
        ws_token = create_ws_token(uid)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws?token={ws_token}"):
                pass

    def test_query_token_rejected_for_unknown_user(self, client, sync_db, monkeypatch):
        monkeypatch.setenv("WS_ALLOW_QUERY_TOKEN", "true")
        ws_token = create_ws_token(str(ObjectId()))
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws?token={ws_token}"):
                pass

    def test_session_token_is_not_a_valid_query_token(
        self, client, sync_db, monkeypatch
    ):
        monkeypatch.setenv("WS_ALLOW_QUERY_TOKEN", "true")
        uid = _insert_user(sync_db, "ws-swap@example.com")
        session = create_access_token(uid)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws?token={session}"):
                pass

    def test_ws_token_is_not_a_valid_session_cookie(self, client, sync_db):
        uid = _insert_user(sync_db, "ws-replay@example.com")
        ws_token = create_ws_token(uid)
        resp = client.get("/auth/me", cookies={"cai_token": ws_token})
        assert resp.status_code == 401


# ── End-to-end emission ──────────────────────────────────────


class TestWebSocketEvents:
    def test_ingest_emits_created_then_updated(self, client, sync_db, monkeypatch):
        _patch_analysis(monkeypatch)
        uid = _insert_user(sync_db, "ws-events@example.com")
        token = create_access_token(uid)

        with client.websocket_connect("/ws", cookies={"cai_token": token}) as ws:
            resp = client.post(
                "/webhooks/simulate",
                json={"sender": "Boss", "message": "Please review the report"},
                cookies={"cai_token": token},
            )
            assert resp.status_code == 200, resp.text

            created = ws.receive_json()
            updated = ws.receive_json()

        assert created["type"] == MESSAGE_CREATED
        assert created["user_id"] == uid
        assert created["message_id"]

        assert updated["type"] == MESSAGE_UPDATED
        assert updated["user_id"] == uid
        assert updated["message_id"] == created["message_id"]

    def test_create_message_endpoint_emits_created(
        self, client, sync_db, monkeypatch
    ):
        _patch_analysis(monkeypatch)
        uid = _insert_user(sync_db, "ws-post@example.com")
        token = create_access_token(uid)

        with client.websocket_connect("/ws", cookies={"cai_token": token}) as ws:
            resp = client.post(
                "/messages",
                json={"sender": "Alice", "content": "hi", "source": "email"},
                cookies={"cai_token": token},
            )
            assert resp.status_code == 201, resp.text

            first = ws.receive_json()

        assert first["type"] == MESSAGE_CREATED
        assert first["user_id"] == uid

    def test_events_are_user_scoped(self, client, sync_db, monkeypatch):
        _patch_analysis(monkeypatch)
        uid_a = _insert_user(sync_db, "iso-a@example.com")
        uid_b = _insert_user(sync_db, "iso-b@example.com")
        token_a = create_access_token(uid_a)
        token_b = create_access_token(uid_b)

        with client.websocket_connect("/ws", cookies={"cai_token": token_b}) as ws_b:
            # A emits first; B's socket must never see it.
            client.post(
                "/webhooks/simulate",
                json={"sender": "A", "message": "from A"},
                cookies={"cai_token": token_a},
            )
            client.post(
                "/webhooks/simulate",
                json={"sender": "B", "message": "from B"},
                cookies={"cai_token": token_b},
            )

            first_b = ws_b.receive_json()

        assert first_b["user_id"] == uid_b
