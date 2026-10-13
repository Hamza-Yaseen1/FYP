"""JARVIS Phase 1 — endpoint, routing, data, isolation, and failure tests.

Routing is deterministic (no LLM) in the test environment because
``GROQ_API_KEY`` is not configured, so replies are fully assertable. The two
provider-path tests monkeypatch ``_llm_configured`` and ``GroqProvider`` so no
real network call ever happens.
"""

import os
from datetime import datetime, timezone

import pytest
from bson import ObjectId


@pytest.fixture(autouse=True)
def _stay_deterministic(monkeypatch):
    """Never allow real LLM calls outside the explicitly faked tests.

    ``conftest`` loads the real ``backend/.env`` (which contains an actual
    ``GROQ_API_KEY``), and the provider now implements ``chat()``, so the
    deterministic conversation tests must pin ``_llm_configured`` off.
    """
    monkeypatch.setattr(
        "services.ai.jarvis_intents._llm_configured", lambda: False
    )
    monkeypatch.setattr(
        "services.ai.jarvis_agent._llm_configured", lambda: False
    )
    monkeypatch.setattr(
        "services.ai.jarvis_messages._llm_configured", lambda: False
    )


REGISTER_BODY = {
    "name": "Jarvis User",
    "email": "jarvis@test.com",
    "password": "passA12345",
}


def _register(client, email="jarvis@test.com"):
    body = {**REGISTER_BODY, "email": email}
    res = client.post("/auth/register", json=body)
    assert res.status_code == 201
    return res.json()["id"], res.cookies.get("cai_token")


def _switch(client, token):
    client.cookies.clear()
    if token:
        client.cookies.set("cai_token", token)


def _chat(client, message):
    return client.post("/jarvis/chat", json={"message": message})


def _seed_message(
    sync_db,
    user_id,
    *,
    status="unread",
    sender="Sender",
    content="A message",
    priority=None,
    needs_attention=False,
):
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "sender": sender,
        "content": content,
        "source": "simulated",
        "status": status,
        "state": "active",
        "messageId": str(ObjectId()),
        "created_at": now,
        "updated_at": now,
        "received_at": now,
    }
    if priority or needs_attention:
        doc["ai_analysis"] = {
            "priority": priority or "normal",
            "needs_attention": needs_attention,
            "status": "completed",
        }
    return str(sync_db.messages.insert_one(doc).inserted_id)


def _seed_task(sync_db, user_id, description, status="pending", deadline=None):
    now = datetime.now(timezone.utc)
    return str(
        sync_db.tasks.insert_one(
            {
                "user_id": user_id,
                "description": description,
                "deadline": deadline,
                "priority_indicator": None,
                "requires_action": True,
                "status": status,
                "source_message_id": str(ObjectId()),
                "source_message_preview": description[:80],
                "created_at": now,
            }
        ).inserted_id
    )


class TestJarvisAuth:
    def test_requires_authentication(self, client):
        client.cookies.clear()
        res = _chat(client, "open my inbox")
        assert res.status_code == 401

    def test_empty_message_returns_400(self, client):
        _, tok = _register(client, "jarvis-empty@test.com")
        _switch(client, tok)
        for empty in ("", "   ", "\n\t"):
            res = _chat(client, empty)
            assert res.status_code == 400
            assert "empty" in res.json()["detail"].lower()


class TestJarvisNavigation:
    def _authed(self, client):
        _, tok = _register(client, "jarvis-nav@test.com")
        _switch(client, tok)

    def test_open_inbox(self, client):
        self._authed(client)
        res = _chat(client, "open my inbox")
        assert res.status_code == 200
        data = res.json()
        assert data["action"] == {"type": "navigation", "target": "/inbox"}
        assert "inbox" in data["reply"].lower()

    def test_open_tasks(self, client):
        self._authed(client)
        res = _chat(client, "open my tasks")
        assert res.status_code == 200
        assert res.json()["action"]["target"] == "/tasks"

    def test_show_me_attention(self, client):
        self._authed(client)
        res = _chat(client, "show me attention")
        assert res.status_code == 200
        assert res.json()["action"]["target"] == "/attention"

    def test_open_connections(self, client):
        self._authed(client)
        res = _chat(client, "open my connections")
        assert res.status_code == 200
        assert res.json()["action"]["target"] == "/connections"

    def test_go_to_dashboard(self, client):
        self._authed(client)
        res = _chat(client, "go to the dashboard")
        assert res.status_code == 200
        assert res.json()["action"]["target"] == "/dashboard"

    def test_open_settings(self, client):
        self._authed(client)
        res = _chat(client, "open settings")
        assert res.status_code == 200
        assert res.json()["action"]["target"] == "/settings"

    def test_bare_inbox_implies_navigation(self, client):
        self._authed(client)
        res = _chat(client, "inbox")
        assert res.status_code == 200
        assert res.json()["action"]["target"] == "/inbox"

    def test_navigation_never_uses_llm(self, client):
        self._authed(client)
        res = _chat(client, "open my inbox")
        assert res.json()["used_ai"] is False

    @pytest.mark.parametrize(
        "message,target",
        [
            ("navigate to inbox", "/inbox"),
            ("take me to my tasks", "/tasks"),
            ("open the attention page", "/attention"),
            ("launch connections", "/connections"),
            ("show me the dashboard", "/dashboard"),
            ("visit analytics", "/analytics"),
            ("go into settings", "/settings"),
        ],
    )
    def test_synonym_navigation(self, client, message, target):
        self._authed(client)
        res = _chat(client, message)
        assert res.status_code == 200
        assert res.json()["action"]["target"] == target


class TestJarvisInformation:
    def _authed(self, client, email="jarvis-info@test.com"):
        uid, tok = _register(client, email)
        _switch(client, tok)
        return uid, tok

    def test_unread_messages_count(self, client, sync_db):
        uid, _ = self._authed(client)
        _seed_message(sync_db, uid, status="unread")
        _seed_message(sync_db, uid, status="unread")
        _seed_message(sync_db, uid, status="read")

        res = _chat(client, "how many unread messages do I have?")
        assert res.status_code == 200
        data = res.json()
        assert data["action"] is None
        assert "2" in data["reply"]
        assert data["used_ai"] is False

    def test_zero_unread(self, client, sync_db):
        uid, _ = self._authed(client)
        _seed_message(sync_db, uid, status="read")
        res = _chat(client, "do I have any unread messages?")
        assert res.status_code == 200
        assert "no unread" in res.json()["reply"]

    def test_pending_tasks(self, client, sync_db):
        uid, _ = self._authed(client)
        _seed_task(sync_db, uid, "Review the quarterly report", deadline="Friday")
        _seed_task(sync_db, uid, "Call the vendor")
        _seed_task(sync_db, uid, "Done task", status="completed")

        res = _chat(client, "what are my pending tasks?")
        assert res.status_code == 200
        reply = res.json()["reply"]
        assert "2" in reply
        assert "Review the quarterly report" in reply
        assert "Call the vendor" in reply
        assert "Done task" not in reply

    def test_no_pending_tasks(self, client, sync_db):
        uid, _ = self._authed(client)
        _seed_task(sync_db, uid, "Done task", status="completed")
        res = _chat(client, "what are my pending tasks?")
        assert res.status_code == 200
        assert "no pending tasks" in res.json()["reply"]

    def test_attention_items(self, client, sync_db):
        uid, _ = self._authed(client)
        _seed_message(
            sync_db, uid, sender="Alpha Sender", needs_attention=True
        )
        _seed_message(
            sync_db, uid, sender="Beta Sender",
            needs_attention=True, status="read",
        )
        _seed_message(sync_db, uid, sender="Calm Sender", needs_attention=False)

        res = _chat(client, "what needs my attention?")
        assert res.status_code == 200
        reply = res.json()["reply"]
        assert "2" in reply
        assert "Alpha Sender" in reply
        assert "Calm Sender" not in reply

    def test_dashboard_summary(self, client, sync_db):
        uid, _ = self._authed(client)
        _seed_message(sync_db, uid, status="unread")
        _seed_message(sync_db, uid, status="read", priority="urgent")
        _seed_message(sync_db, uid, status="read", needs_attention=True)
        _seed_task(sync_db, uid, "Pending task")

        res = _chat(client, "give me my dashboard summary")
        assert res.status_code == 200
        reply = res.json()["reply"]
        assert "3 total messages" in reply
        assert "1 unread" in reply
        assert "1 urgent" in reply
        assert "1 pending tasks" in reply
        assert "1 item needing attention" in reply


class TestJarvisIsolation:
    def _authed(self, client, email):
        _, tok = _register(client, email)
        _switch(client, tok)

    def test_data_stays_with_owner(self, client, sync_db):
        uid_a, tok_a = _register(client, "jarvis-iso-a@test.com")
        uid_b, tok_b = _register(client, "jarvis-iso-b@test.com")

        _seed_message(sync_db, uid_a, status="unread", sender="Alpha Sender",
                      needs_attention=True)
        _seed_message(sync_db, uid_a, status="unread")
        _seed_message(sync_db, uid_b, status="unread", sender="Beta Sender",
                      needs_attention=True)
        _seed_task(sync_db, uid_b, "Beta's private task")

        # User A
        _switch(client, tok_a)
        unread_a = _chat(client, "how many unread messages do I have?").json()
        attention_a = _chat(client, "what needs my attention?").json()
        assert "2" in unread_a["reply"]
        assert "Alpha Sender" in attention_a["reply"]
        assert "Beta Sender" not in attention_a["reply"]

        # User B
        _switch(client, tok_b)
        unread_b = _chat(client, "how many unread messages do I have?").json()
        attention_b = _chat(client, "what needs my attention?").json()
        tasks_b = _chat(client, "what are my pending tasks?").json()
        assert "1" in unread_b["reply"]
        assert "Beta Sender" in attention_b["reply"]
        assert "Alpha Sender" not in attention_b["reply"]
        assert "Beta's private task" in tasks_b["reply"]


class TestJarvisConversation:
    def _authed(self, client, email="jarvis-chat@test.com"):
        _, tok = _register(client, email)
        _switch(client, tok)

    def test_greeting(self, client):
        self._authed(client)
        res = _chat(client, "hello jarvis")
        assert res.status_code == 200
        data = res.json()
        assert data["action"] is None
        assert data["reply"]
        assert "at your service" in data["reply"].lower()

    def test_help_lists_capabilities(self, client):
        self._authed(client)
        for command in ("help", "what can you do?", "how can you help me"):
            res = _chat(client, command)
            assert res.status_code == 200
            reply = res.json()["reply"]
            assert "open your inbox" in reply
            assert "unread messages" in reply

    def test_unknown_command_is_graceful(self, client):
        self._authed(client)
        res = _chat(client, "do the hokey pokey and turn myself around")
        assert res.status_code == 200
        data = res.json()
        assert data["action"] is None
        assert "conversational AI service is currently unavailable" in data["reply"]
        assert data["used_ai"] is False


class TestJarvisProviderHandling:
    def _authed(self, client, email="jarvis-provider@test.com"):
        _, tok = _register(client, email)
        _switch(client, tok)

    def test_groq_success_reply_is_used(self, client, monkeypatch):
        self._authed(client)
        monkeypatch.setattr("services.ai.jarvis_agent._llm_configured", lambda: True)

        class _GoodProvider:
            async def chat(self, prompt):
                return {"reply": "All systems nominal, sir."}

        monkeypatch.setattr("services.ai.jarvis_agent.GroqProvider", _GoodProvider)

        res = _chat(client, "hello jarvis")
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == "All systems nominal, sir."
        assert data["used_ai"] is True

    def test_groq_failure_falls_back_gracefully(self, client, monkeypatch):
        self._authed(client)
        monkeypatch.setattr("services.ai.jarvis_agent._llm_configured", lambda: True)

        class _BoomProvider:
            async def chat(self, prompt):
                raise RuntimeError("groq is on fire")

        monkeypatch.setattr("services.ai.jarvis_agent.GroqProvider", _BoomProvider)

        res = _chat(client, "hello jarvis")
        assert res.status_code == 200
        data = res.json()
        assert data["reply"]
        assert data["used_ai"] is False
        assert "at your service" in data["reply"].lower()


class TestJarvisRoutingUnit:
    """Pure route_classification checks (no DB, no HTTP)."""

    def test_routing_unit(self):
        from services.ai.jarvis_agent import route_command

        assert route_command("open my inbox")["target"] == "/inbox"
        assert route_command("take me to tasks")["target"] == "/tasks"
        assert route_command("what needs my attention")["info"] == "attention"
        assert route_command("how many unread messages")["info"] == "unread"
        assert route_command("what are my pending tasks")["info"] == "tasks"
        assert route_command("give me my dashboard summary")["info"] == "dashboard"
        assert route_command("hello")["topic"] == "greeting"
        assert route_command("help")["topic"] == "help"
        assert route_command("blah blah")["topic"] == "unknown"