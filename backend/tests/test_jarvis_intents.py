"""JARVIS Phase 3 — natural-language intent tests.

Three areas:

- ``detect_intent``: pure mapping of natural phrasings (and the legacy Phase 1
  phrases it must keep byte-identical) — no DB, no LLM.
- Real-data today's-messages counting via the endpoint (UTC calendar day,
  user-scoped, boundary-tested).
- The optional LLM intent classifier: whitelist-only labels, graceful
  degradation, and the security rule that a hostile label can never do
  anything beyond falling back to general chat.

The deterministic tests force ``jarvis_intents._llm_configured`` to False so
nothing here ever makes a real network call, even on a machine that has
``GROQ_API_KEY`` set.
"""

from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

REGISTER_BODY = {
    "name": "Jarvis Intent User",
    "email": "jarvis-intent@test.com",
    "password": "passA12345",
}


def _register(client, email="jarvis-intent@test.com"):
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


def _seed_message_at(
    sync_db,
    user_id,
    when,
    *,
    status="unread",
    sender="Sender",
    content="A message",
    priority=None,
):
    doc = {
        "user_id": user_id,
        "sender": sender,
        "content": content,
        "source": "simulated",
        "status": status,
        "state": "active",
        "messageId": str(ObjectId()),
        "created_at": when,
        "updated_at": when,
        "received_at": when,
    }
    if priority:
        doc["ai_analysis"] = {"priority": priority, "needs_attention": True}
    return str(sync_db.messages.insert_one(doc).inserted_id)


def _start_of_today_utc():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


@pytest.fixture(autouse=True)
def _stay_deterministic(monkeypatch):
    """Never allow real LLM calls in these tests."""
    monkeypatch.setattr(
        "services.ai.jarvis_intents._llm_configured", lambda: False
    )
    monkeypatch.setattr(
        "services.ai.jarvis_agent._llm_configured", lambda: False
    )


class TestDetectIntentUnit:
    """Pure intent classification without any DB or HTTP."""

    def _intent(self, message):
        from services.ai.jarvis_intents import detect_intent

        detection = detect_intent(message)
        return detection["intent"] if detection else None

    def _target(self, message):
        from services.ai.jarvis_intents import detect_intent

        detection = detect_intent(message)
        return detection["params"]["target"] if detection else None

    @pytest.mark.parametrize(
        "message",
        [
            "What's the message today?",
            "How many messages do I have today?",
            "What messages came in today?",
            "Do I have any new messages today?",
        ],
    )
    def test_todays_messages_phrasings(self, message):
        assert self._intent(message) == "GET_TODAYS_MESSAGES"

    @pytest.mark.parametrize(
        "message",
        [
            "Do I have any new messages?",
            "Show me my unread messages.",
            "How many unread messages do I have?",
            "Any messages waiting for me?",
        ],
    )
    def test_unread_phrasings(self, message):
        assert self._intent(message) == "GET_UNREAD_MESSAGES"

    @pytest.mark.parametrize(
        "message",
        [
            "What are my pending tasks?",
            "How many tasks are still pending?",
            "What's on my to-do list?",
            "Do I have any pending work?",
        ],
    )
    def test_pending_tasks_phrasings(self, message):
        assert self._intent(message) == "GET_PENDING_TASKS"

    @pytest.mark.parametrize(
        "message",
        [
            "What needs my attention?",
            "What should I work on?",
            "What's on my plate?",
            "What's waiting for me?",
        ],
    )
    def test_attention_phrasings(self, message):
        assert self._intent(message) == "GET_ATTENTION"

    @pytest.mark.parametrize(
        "message",
        [
            "Give me my dashboard summary.",
            "Give me the big picture.",
            "What's the rundown?",
            "How's everything going?",
        ],
    )
    def test_dashboard_phrasings(self, message):
        assert self._intent(message) == "GET_DASHBOARD_SUMMARY"

    @pytest.mark.parametrize(
        "message,target",
        [
            ("Take me to my inbox.", "/inbox"),
            ("Open my tasks.", "/tasks"),
            ("I want to see my attention items.", "/attention"),
            ("View my tasks.", "/tasks"),
            ("Show me my attention items.", "/attention"),
            ("Go to analytics.", "/analytics"),
            ("Can you open my inbox?", "/inbox"),
        ],
    )
    def test_natural_navigation(self, message, target):
        assert self._intent(message) == "NAVIGATE"
        assert self._target(message) == target

    @pytest.mark.parametrize(
        "message",
        [
            "hello jarvis",
            "help",
            "what can you do?",
            "do the hokey pokey and turn myself around",
            "what time is it?",
        ],
    )
    def test_leaves_chat_alone(self, message):
        assert self._intent(message) is None

    @pytest.mark.parametrize(
        "message,intent,target",
        [
            ("open my inbox", "NAVIGATE", "/inbox"),
            ("take me to tasks", "NAVIGATE", "/tasks"),
            ("show me attention", "NAVIGATE", "/attention"),
        ],
    )
    def test_legacy_navigation_parity(self, message, intent, target):
        assert self._intent(message) == intent
        assert self._target(message) == target

    @pytest.mark.parametrize(
        "message,intent",
        [
            ("how many unread messages", "GET_UNREAD_MESSAGES"),
            ("what needs my attention", "GET_ATTENTION"),
            ("what are my pending tasks", "GET_PENDING_TASKS"),
            ("give me my dashboard summary", "GET_DASHBOARD_SUMMARY"),
        ],
    )
    def test_legacy_information_parity(self, message, intent):
        assert self._intent(message) == intent


class TestNaturalInformationEndpoint:
    def _authed(self, client, email="jarvis-intent-info@test.com"):
        uid, tok = _register(client, email)
        _switch(client, tok)
        return uid

    def test_do_i_have_any_new_messages(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message_at(sync_db, uid, now)
        _seed_message_at(sync_db, uid, now)
        _seed_message_at(sync_db, uid, now, status="read")

        res = _chat(client, "Do I have any new messages?")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        assert "2" in data["reply"]

    def test_show_me_my_unread_messages(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message_at(sync_db, uid, now)
        res = _chat(client, "Show me my unread messages.")
        assert "1" in res.json()["reply"]

    def test_what_should_i_work_on(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message_at(sync_db, uid, now, sender="Alpha Sender", priority="urgent")
        _seed_message_at(sync_db, uid, now, sender="Calm Sender")

        res = _chat(client, "What should I work on?")
        reply = res.json()["reply"]
        assert "Alpha Sender" in reply
        assert "Calm Sender" not in reply

    def test_how_many_tasks_are_still_pending(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        for i, desc in enumerate(("Review Q3", "Call vendor")):
            sync_db.tasks.insert_one(
                {
                    "user_id": uid,
                    "description": desc,
                    "deadline": None,
                    "priority_indicator": None,
                    "requires_action": True,
                    "status": "pending",
                    "source_message_id": str(ObjectId()),
                    "source_message_preview": desc,
                    "created_at": now,
                }
            )
        res = _chat(client, "How many tasks are still pending?")
        reply = res.json()["reply"]
        assert "2" in reply
        assert "Review Q3" in reply

    def test_whats_on_my_plate_uses_attention(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message_at(sync_db, uid, now, sender="Plate Sender", priority="urgent")
        res = _chat(client, "What's on my plate?")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        assert "Plate Sender" in data["reply"]


class TestTodayMessagesEndpoint:
    def _authed(self, client, email="jarvis-today@test.com"):
        uid, tok = _register(client, email)
        _switch(client, tok)
        return uid

    def test_counts_todays_messages(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message_at(sync_db, uid, now, priority="important")
        _seed_message_at(sync_db, uid, now)
        _seed_message_at(sync_db, uid, now, status="read")
        _seed_message_at(sync_db, uid, now - timedelta(days=1))  # yesterday

        res = _chat(client, "How many messages do I have today?")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        reply = data["reply"]
        assert "You received 3 messages today." in reply
        assert "2 unread" in reply
        assert "1 important" in reply

    def test_no_messages_today(self, client, sync_db):
        uid = self._authed(client)
        _seed_message_at(sync_db, uid, datetime.now(timezone.utc) - timedelta(days=1))
        res = _chat(client, "What's the message today?")
        assert "no messages today" in res.json()["reply"]

    def test_start_of_day_boundary_counts(self, client, sync_db):
        uid = self._authed(client)
        _seed_message_at(sync_db, uid, _start_of_today_utc())
        res = _chat(client, "How many messages do I have today?")
        assert "You received 1 message today." in res.json()["reply"]

    def test_yesterday_just_after_midnight_excluded(self, client, sync_db):
        uid = self._authed(client)
        boundary = _start_of_today_utc() - timedelta(seconds=1)
        _seed_message_at(sync_db, uid, boundary)
        res = _chat(client, "How many messages do I have today?")
        assert "no messages today" in res.json()["reply"]

    def test_isolation_other_users_messages_not_counted(self, client, sync_db):
        uid_a = self._authed(client, "jarvis-today-a@test.com")
        uid_b, _ = _register(client, "jarvis-today-b@test.com")
        now = datetime.now(timezone.utc)
        _seed_message_at(sync_db, uid_a, now)
        _seed_message_at(sync_db, uid_a, now)
        _seed_message_at(sync_db, uid_b, now)
        _seed_message_at(sync_db, uid_b, now, status="read")

        res = _chat(client, "How many messages do I have today?")
        assert "2 messages today" in res.json()["reply"]


class TestNaturalNavigationEndpoint:
    def _authed(self, client, email="jarvis-natnav@test.com"):
        _, tok = _register(client, email)
        _switch(client, tok)

    @pytest.mark.parametrize(
        "message,target",
        [
            ("Take me to my inbox.", "/inbox"),
            ("Open my tasks.", "/tasks"),
            ("I want to see my attention items.", "/attention"),
            ("View my tasks.", "/tasks"),
            ("Go to analytics.", "/analytics"),
            ("Can you open my inbox?", "/inbox"),
        ],
    )
    def test_natural_navigation_pushes(self, client, message, target):
        self._authed(client)
        res = _chat(client, message)
        assert res.status_code == 200
        data = res.json()
        assert data["action"] == {"type": "navigation", "target": target}
        assert data["used_ai"] is False


class TestLlmIntentClassifier:
    """Whitelist-only LLM labels with a faked provider (no network)."""

    def _authed(self, client, email="jarvis-llm@test.com"):
        uid, tok = _register(client, email)
        _switch(client, tok)
        return uid

    def _install(self, monkeypatch, result=None, raises=False):
        class _FakeProvider:
            def __init__(self):
                _FakeProvider.instances.append(self)
                _FakeProvider.calls = []

            async def chat(self, prompt):
                if raises:
                    raise RuntimeError("intent classifier exploded")
                _FakeProvider.calls.append(prompt)
                return result

        _FakeProvider.instances = []
        _FakeProvider.calls = []
        monkeypatch.setattr(
            "services.ai.jarvis_intents.GroqProvider", _FakeProvider
        )
        monkeypatch.setattr(
            "services.ai.jarvis_intents._llm_configured", lambda: True
        )
        return _FakeProvider

    def test_valid_info_label_is_used(self, client, sync_db, monkeypatch):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message_at(sync_db, uid, now)
        _seed_message_at(sync_db, uid, now, status="read")
        _seed_message_at(sync_db, uid, now - timedelta(days=1))  # yesterday
        fake = self._install(
            monkeypatch, result={"intent": "GET_TODAYS_MESSAGES"}
        )

        res = _chat(client, "Bring me the numbers please")
        data = res.json()
        assert fake.instances, "provider should have been called"
        assert "You received 2 messages today." in data["reply"]
        assert data["used_ai"] is False

    def test_general_chat_label_falls_back(self, client, monkeypatch):
        self._authed(client)
        self._install(monkeypatch, result={"intent": "GENERAL_CHAT"})
        res = _chat(client, "Tell me a joke about sandwiches")
        assert "conversational AI service is currently unavailable" in res.json()["reply"]

    def test_hostile_label_is_rejected(self, client, monkeypatch):
        self._authed(client)
        self._install(
            monkeypatch,
            result={"intent": "DROP DATABASE messages"},
        )
        res = _chat(client, "Bring me the numbers please")
        assert "conversational AI service is currently unavailable" in res.json()["reply"]
        assert res.json()["action"] is None
        assert res.json()["used_ai"] is False

    def test_malformed_output_is_rejected(self, client, monkeypatch):
        self._authed(client)
        for malformed in (None, "GET_TODAYS_MESSAGES", ["nope"], {}):
            self._install(monkeypatch, result=malformed)
            res = _chat(client, "Bring me the numbers please")
            assert "conversational AI service is currently unavailable" in res.json()["reply"]

    def test_provider_failure_falls_back(self, client, monkeypatch):
        self._authed(client)
        self._install(monkeypatch, raises=True)
        res = _chat(client, "Bring me the numbers please")
        assert res.status_code == 200
        assert "conversational AI service is currently unavailable" in res.json()["reply"]
        assert res.json()["used_ai"] is False

    def test_classifier_not_consulted_for_greeting(self, client, monkeypatch):
        self._authed(client)
        fake = self._install(
            monkeypatch, result={"intent": "GET_TODAYS_MESSAGES"}
        )
        res = _chat(client, "hello jarvis")
        assert "at your service" in res.json()["reply"].lower()
        assert fake.instances == []

    def test_without_key_provider_never_called(self, client, monkeypatch):
        self._authed(client)
        calls = []

        class _BoomProvider:
            async def chat(self, prompt):
                calls.append(prompt)
                raise AssertionError("must not be called without a key")

        monkeypatch.setattr(
            "services.ai.jarvis_intents.GroqProvider", _BoomProvider
        )
        monkeypatch.setattr(
            "services.ai.jarvis_intents._llm_configured", lambda: False
        )
        res = _chat(client, "Bring me the numbers please")
        assert "conversational AI service is currently unavailable" in res.json()["reply"]
        assert calls == []