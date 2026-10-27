"""JARVIS core routing — message content vs count vs delete vs chat (backend).

Integration tests for the fixed message-intelligence pipeline:

- Content questions ("show me messages about budget") list real message
  content, while count questions stay counts and sender/priority/unread
  filters combine correctly.
- Message deletion is confirmation-gated, user-scoped, and never confused with
  task deletion ("delete my task call the vendor" stays a task delete).
- Context references ("delete that one") resolve against the user's own last
  message intent and are ambiguous-safe when no filter is in context.
- The LLM intent classifiers are consulted ONLY for phrases without
  application vocabulary ("sender", "unread", …), so they can never hijack
  deterministic commands.

The autouse fixture pins ``_llm_configured`` to False in every layer so
nothing here makes a network call; the gating tests re-enable it in the
intent layer with a recording (never real) provider.
"""

from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

REGISTER_BODY = {
    "name": "Jarvis Core User",
    "email": "jarvis-core@test.com",
    "password": "passA12345",
}

AVAILABILITY_UNIQUE = "conversational AI service is currently unavailable"


def _register(client, email="jarvis-core@test.com"):
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


def _confirm(client, token, confirmed=True):
    return client.post(
        "/jarvis/chat",
        json={"message": "confirmed", "confirmation_token": token, "confirmed": confirmed},
    )


def _authed(client, email="jarvis-core@test.com"):
    uid, tok = _register(client, email)
    _switch(client, tok)
    return uid


def _start_today():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _seed_message_at(
    sync_db,
    user_id,
    when,
    *,
    status="unread",
    sender="Sender",
    subject=None,
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
    if subject:
        doc["subject"] = subject
    if priority:
        doc["ai_analysis"] = {"priority": priority, "needs_attention": True}
    return str(sync_db.messages.insert_one(doc).inserted_id)


def _seed_task(sync_db, user_id, description, *, deadline=None):
    now = datetime.now(timezone.utc)
    return str(
        sync_db.tasks.insert_one(
            {
                "user_id": user_id,
                "description": description,
                "deadline": deadline,
                "priority_indicator": None,
                "requires_action": True,
                "status": "pending",
                "source_message_id": str(ObjectId()),
                "source_message_preview": description,
                "created_at": now,
            }
        ).inserted_id
    )


@pytest.fixture(autouse=True)
def _no_llm(monkeypatch):
    for module in (
        "services.ai.jarvis_messages",
        "services.ai.jarvis_intents",
        "services.ai.jarvis_actions",
        "services.ai.jarvis_agent",
    ):
        monkeypatch.setattr(f"{module}._llm_configured", lambda: False)
    yield


# ── A. Message content vs count vs filters ─────────────────────────────────

class TestMessageRouting:
    def test_show_messages_from_sender_is_not_owned_elsewhere(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="Quarterly numbers due")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Other", content="Standup notes")

        res = _chat(client, "only show me messages from boss")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        assert "from boss" in data["reply"]
        assert "Quarterly numbers due" in data["reply"]
        assert "Standup notes" not in data["reply"]

    def test_sender_from_date_phrasing_lists_content(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="Budget breakdown")

        res = _chat(client, "what messages came from boss?")
        data = res.json()
        assert data["action"] is None
        assert "from boss" in data["reply"]
        assert "Budget breakdown" in data["reply"]

    def test_keyword_topic_lists_real_content(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Finance", content="Budget breakdown for next quarter")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Sales", content="Lunch plans")

        res = _chat(client, "show me messages about budget")
        data = res.json()
        assert data["action"] is None
        assert 'about "budget"' in data["reply"]
        assert "Budget breakdown" in data["reply"]
        assert "Lunch plans" not in data["reply"]

    def test_count_with_sender_stays_a_count(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="One")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Boss", content="Two", status="read")

        res = _chat(client, "how many messages from boss do I have?")
        data = res.json()
        assert data["action"] is None
        assert "You received 2 messages from boss." in data["reply"]
        assert "1 unread" in data["reply"]

    def test_unread_sender_filter_combines(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="ASAP ship it")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Boss", content="Just an FYI", status="read")

        res = _chat(client, "what unread messages came from boss?")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        assert "from boss unread" in data["reply"]
        assert "ASAP ship it" in data["reply"]
        assert "Just an FYI" not in data["reply"]

    def test_yesterday_listing_shows_real_content(self, client, sync_db):
        uid = _authed(client)
        yesterday = _start_today() - timedelta(days=1) + timedelta(hours=10)
        _seed_message_at(sync_db, uid, yesterday,
                         sender="Yday Sender", content="Yesterday's digest")

        res = _chat(client, "show me yesterday's messages")
        data = res.json()
        assert data["action"] is None
        assert "yesterday" in data["reply"]
        assert "Yday Sender" in data["reply"]

    def test_this_week_span_routes_to_date_not_sender(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Week Sender", content="Weekly report")

        res = _chat(client, "show me the messages from this week")
        data = res.json()
        assert data["action"] is None
        assert "Week Sender" in data["reply"]

    def test_read_messages_returns_actual_content(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", subject="Launch", content="Plan the launch party")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Ops", content="Ship v2 today")

        res = _chat(client, "read my messages")
        data = res.json()
        assert data["action"] is None
        assert "Plan the launch party" in data["reply"]
        assert "Ship v2 today" in data["reply"]
        assert "Boss" in data["reply"]

    def test_read_messages_empty(self, client, sync_db):
        _authed(client)
        res = _chat(client, "read my messages")
        assert "You have no messages to read." in res.json()["reply"]

    def test_summarize_inbox_wording(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Finance", content="Budget breakdown before Friday")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Ops", content="Deployment window is set")

        res = _chat(client, "give me a summary of my inbox")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        assert "Here's what your recent messages cover" in data["reply"]

    def test_important_question_answers_from_flags(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="Needs sign off", priority="important")

        res = _chat(client, "which ones are important?")
        data = res.json()
        assert data["action"] is None
        assert "1 important message" in data["reply"]
        assert "Needs sign off" in data["reply"]


# ── B. Message deletion (confirmation-gated, user-scoped) ─────────────────

class TestMessageDelete:
    def _confirm_pending(self, data, pending_type):
        assert data["action"] is not None
        assert data["action"]["type"] == "request_confirmation"
        assert data["action"]["detail"]["pending_type"] == pending_type
        return data["action"]["confirmation_token"]

    def test_delete_all_confirmation_and_confirm(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        for i in range(3):
            _seed_message_at(sync_db, uid, _start + timedelta(hours=i + 1))

        res = _chat(client, "delete all my messages")
        data = res.json()
        assert "Do you want me to delete all your messages (3 messages)?" in data["reply"]
        token = self._confirm_pending(data, "delete_messages")

        res = _confirm(client, token)
        data = res.json()
        assert "Done. I deleted 3 messages." in data["reply"]
        assert data["action"]["type"] == "delete_messages"
        assert data["action"]["detail"]["count"] == 3
        assert sync_db.messages.count_documents({"user_id": uid}) == 0

    def test_delete_all_with_nothing(self, client, sync_db):
        _authed(client)
        res = _chat(client, "delete all my messages")
        assert "couldn't find any messages" in res.json()["reply"]
        assert res.json()["action"] is None

    def test_delete_urgent_leaves_normal(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="URGENT", priority="urgent")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Ops", content="Normal note")

        res = _chat(client, "delete my urgent messages")
        data = res.json()
        assert "Do you want me to delete all urgent messages (1 message)?" in data["reply"]
        token = self._confirm_pending(data, "delete_messages")

        res2 = _confirm(client, token)
        assert "Done. I deleted 1 message." in res2.json()["reply"]
        assert sync_db.messages.count_documents({"user_id": uid}) == 1
        assert sync_db.messages.count_documents(
            {"user_id": uid, "content": "Normal note"}
        ) == 1

    def test_delete_sender_confirm(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="One")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Boss", content="Two")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=8),
                         sender="Other", content="Keep me")

        res = _chat(client, "delete all messages from boss")
        data = res.json()
        assert "Do you want me to delete all messages from boss (2 messages)?" in data["reply"]
        token = self._confirm_pending(data, "delete_messages")

        _confirm(client, token)
        assert sync_db.messages.count_documents({"user_id": uid, "sender": "Boss"}) == 0
        assert sync_db.messages.count_documents({"user_id": uid, "sender": "Other"}) == 1

    def test_delete_yesterday_keeps_today(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start - timedelta(days=1) + timedelta(hours=9),
                         sender="Old", content="Yesterday")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="New", content="Today")

        res = _chat(client, "delete yesterday's messages")
        data = res.json()
        assert "Do you want me to delete all messages from yesterday (1 message)?" in data["reply"]
        token = self._confirm_pending(data, "delete_messages")

        _confirm(client, token)
        assert sync_db.messages.count_documents({"user_id": uid, "content": "Yesterday"}) == 0
        assert sync_db.messages.count_documents({"user_id": uid, "content": "Today"}) == 1

    def test_delete_all_is_user_scoped(self, client, sync_db):
        uid_a = _authed(client, "jarvis-core-a@test.com")
        _start = _start_today()
        _seed_message_at(sync_db, uid_a, _start + timedelta(hours=6), sender="A")

        uid_b, tok_b = _register(client, "jarvis-core-b@test.com")
        _seed_message_at(sync_db, uid_b, _start + timedelta(hours=6), sender="B")
        _switch(client, tok_b)

        res = _chat(client, "delete all my messages")
        data = res.json()
        token = self._confirm_pending(data, "delete_messages")
        _confirm(client, token)

        assert sync_db.messages.count_documents({"user_id": uid_b}) == 0
        assert sync_db.messages.count_documents({"user_id": uid_a}) == 1

    def test_delete_task_phrase_never_touches_messages(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6), sender="Ops")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7), sender="Ops")
        _seed_task(sync_db, uid, "call the vendor")

        res = _chat(client, "delete my task call the vendor")
        data = res.json()
        token = self._confirm_pending(data, "delete_task")
        _confirm(client, token)

        assert sync_db.tasks.count_documents({"user_id": uid}) == 0
        assert sync_db.messages.count_documents({"user_id": uid}) == 2

    def test_context_delete_ambiguous_stays_intact(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6), sender="A")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7), sender="B")

        _chat(client, "show me messages")
        res = _chat(client, "delete that one")
        data = res.json()
        assert data["action"] is None
        assert "Which message do you mean?" in data["reply"]
        assert sync_db.messages.count_documents({"user_id": uid}) == 2

    def test_context_delete_after_sender_filter(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6),
                         sender="Boss", content="Delete me")
        _seed_message_at(sync_db, uid, _start + timedelta(hours=7),
                         sender="Other", content="Keep me")

        _chat(client, "only show me messages from boss")
        res = _chat(client, "delete that one")
        data = res.json()
        assert "Do you want me to delete that message?" in data["reply"]
        token = self._confirm_pending(data, "delete_messages")
        _confirm(client, token)

        assert sync_db.messages.count_documents({"user_id": uid, "sender": "Boss"}) == 0
        assert sync_db.messages.count_documents({"user_id": uid, "sender": "Other"}) == 1

    def test_context_delete_requires_message_context(self, client, sync_db):
        uid = _authed(client)
        _start = _start_today()
        _seed_message_at(sync_db, uid, _start + timedelta(hours=6), sender="Ops")
        _seed_task(sync_db, uid, "first task")

        _chat(client, "show my tasks")
        res = _chat(client, "delete that one")
        data = res.json()
        assert data["action"]["type"] == "request_confirmation"
        assert data["action"]["detail"]["pending_type"] == "delete_task"
        assert sync_db.messages.count_documents({"user_id": uid}) == 1


# ── C. Classifier gating: app vocabulary never reaches the LLM labels ──────

class TestClassifierGating:
    def _recording_provider(self, monkeypatch):
        calls = []

        class _RecordingProvider:
            async def chat(self, prompt):
                calls.append(prompt)
                return {"intent": "GENERAL_CHAT", "params": {}}

        monkeypatch.setattr("services.ai.jarvis_intents.GroqProvider", _RecordingProvider)
        monkeypatch.setattr("services.ai.jarvis_intents._llm_configured", lambda: True)
        return calls

    def test_non_app_phrase_consults_classifier(self, client, monkeypatch):
        _authed(client)
        calls = self._recording_provider(monkeypatch)
        res = _chat(client, "what is the square root of 100?")
        data = res.json()
        assert calls, "non-app phrase should reach the intent classifier"
        assert "User request:" in calls[0]
        assert AVAILABILITY_UNIQUE in data["reply"]

    def test_app_phrase_never_consults_classifier(self, client, monkeypatch):
        _authed(client)
        calls = self._recording_provider(monkeypatch)
        res = _chat(client, "what is the sender column for?")
        data = res.json()
        assert calls == [], "app-vocabulary phrases must never reach the classifier"
        assert AVAILABILITY_UNIQUE in data["reply"]

    def test_unread_meaning_question_not_classified(self, client, monkeypatch):
        _authed(client)
        calls = self._recording_provider(monkeypatch)
        res = _chat(client, "what does the deadline column mean?")
        data = res.json()
        assert calls == []
        assert AVAILABILITY_UNIQUE in data["reply"]