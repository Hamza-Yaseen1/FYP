"""JARVIS Phase 4 — message intelligence tests (backend).

Three areas:

- ``detect_message_intent``: pure mapping of natural message phrasings to the
  eight Phase 4 intents, plus the ownership rules that keep every phrase
  Phases 1-3 own returning ``None`` (so their replies stay byte-identical).
- Real-data endpoint tests: message counts, today/yesterday/date-span listings
  (UTC calendar day), actual message content, important/urgent lists, and the
  user-scoping rules — all via the ``/jarvis/chat`` route.
- Summarization: Groq is consulted ONLY for ``SUMMARIZE_MESSAGES`` and only
  ever receives a digest; on no-key / malformed / failure it degrades to the
  deterministic digest reply.

The deterministic tests force ``jarvis_messages._llm_configured`` (and the
agent/intent layers) to False so nothing here ever makes a real network call,
even on a machine that has ``GROQ_API_KEY`` set.
"""

from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

REGISTER_BODY = {
    "name": "Jarvis Message User",
    "email": "jarvis-message@test.com",
    "password": "passA12345",
}

_WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _register(client, email="jarvis-message@test.com"):
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
    subject=None,
    content="A message",
    priority=None,
    when=None,
):
    at = when or datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "sender": sender,
        "content": content,
        "source": "simulated",
        "status": status,
        "state": "active",
        "messageId": str(ObjectId()),
        "created_at": at,
        "updated_at": at,
        "received_at": at,
    }
    if subject:
        doc["subject"] = subject
    if priority:
        doc["ai_analysis"] = {"priority": priority, "needs_attention": True}
    return str(sync_db.messages.insert_one(doc).inserted_id)


def _start_of_today_utc():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _most_recent_weekday_start(weekday: str) -> datetime:
    """Most recent previous occurrence of a weekday, as a UTC day start.

    Mirrors the module's own offset math so weekday tests never depend on the
    real calendar date.
    """
    today = _start_of_today_utc()
    offset = (today.weekday() - _WEEKDAY_INDEX[weekday]) % 7
    if offset == 0:
        offset = 7
    return today - timedelta(days=offset)


@pytest.fixture(autouse=True)
def _stay_deterministic(monkeypatch):
    """Never allow real LLM calls in these tests."""
    monkeypatch.setattr(
        "services.ai.jarvis_messages._llm_configured", lambda: False
    )
    monkeypatch.setattr(
        "services.ai.jarvis_intents._llm_configured", lambda: False
    )
    monkeypatch.setattr(
        "services.ai.jarvis_agent._llm_configured", lambda: False
    )


class TestDetectMessageIntentUnit:
    """Pure Phase 4 classification without any DB or HTTP."""

    def _intent(self, message):
        from services.ai.jarvis_messages import detect_message_intent

        detection = detect_message_intent(message)
        return detection["intent"] if detection else None

    def _params(self, message):
        from services.ai.jarvis_messages import detect_message_intent

        detection = detect_message_intent(message)
        return detection["params"] if detection else {}

    @pytest.mark.parametrize(
        "message",
        [
            "how many messages do I have?",
            "how many messages are in my inbox?",
            "how many emails do I have?",
            "how many messages did I receive?",
            "how many mails are in my inbox?",
        ],
    )
    def test_count_phrasings(self, message):
        assert self._intent(message) == "MESSAGE_COUNT"

    @pytest.mark.parametrize(
        "message",
        [
            "what messages came in today?",
            "show me today's messages",
            "what did I receive today?",
            "what messages arrived today?",
            "display today's emails",
            "what messages did I get today?",
        ],
    )
    def test_today_listing_phrasings(self, message):
        assert self._intent(message) == "GET_TODAYS_MESSAGES"
        assert self._params(message) == {"list": True}

    @pytest.mark.parametrize(
        "message",
        [
            "what messages did I get yesterday?",
            "show me yesterday's messages",
            "what came in yesterday?",
            "tell me what's the message yesterday",
            "what about yesterday?",
        ],
    )
    def test_yesterday_listing_phrasings(self, message):
        assert self._intent(message) == "GET_YESTERDAYS_MESSAGES"

    @pytest.mark.parametrize(
        "message,when",
        [
            ("how many messages did I get yesterday?", "yesterday"),
            ("how many messages on Tuesday?", "tuesday"),
            ("how many messages last week?", "last week"),
            ("how many messages last month?", "last month"),
        ],
    )
    def test_count_mode_flags(self, message, when):
        assert self._params(message) == {"when": when, "count": True}

    @pytest.mark.parametrize(
        "message,when",
        [
            ("what messages on monday?", "monday"),
            ("show me the messages from this week", "this week"),
            ("what messages came in last week?", "last week"),
            ("show me the messages from this month", "this month"),
            ("what messages came in last month?", "last month"),
            ("what emails on friday?", "friday"),
        ],
    )
    def test_by_date_span_phrasings(self, message, when):
        assert self._intent(message) == "GET_MESSAGES_BY_DATE"
        assert self._params(message) == {"when": when, "count": False}

    @pytest.mark.parametrize(
        "message",
        [
            "show me my messages",
            "list all my emails",
            "which messages do I have?",
            "pull up my messages",
            "display my emails",
        ],
    )
    def test_list_phrasings(self, message):
        assert self._intent(message) == "LIST_MESSAGES"

    @pytest.mark.parametrize(
        "message",
        [
            "summarize my messages",
            "summarise my inbox",
            "can you summarize my emails?",
            "what are the main messages in my inbox?",
            "what are the main messages in my 120 messages?",
            "give me a summary of my inbox",
        ],
    )
    def test_summarize_phrasings(self, message):
        assert self._intent(message) == "SUMMARIZE_MESSAGES"

    @pytest.mark.parametrize(
        "message",
        [
            "which messages are important?",
            "are there any important messages?",
            "what's important in my inbox?",
            "should i know from my inbox?",
            "any messages I need to respond to?",
            "do I have messages I have to respond to?",
        ],
    )
    def test_important_phrasings(self, message):
        assert self._intent(message) == "IMPORTANT_MESSAGES"

    @pytest.mark.parametrize(
        "message",
        [
            "which messages are urgent?",
            "are there any urgent messages?",
            "show me the urgent ones",
        ],
    )
    def test_urgent_phrasings(self, message):
        assert self._intent(message) == "URGENT_MESSAGES"

    @pytest.mark.parametrize(
        "message",
        [
            "how many unread messages do I have?",
            "show my unread messages",
            "summarize my unread messages",
            "show my important messages",
            "show my urgent messages",
            "what are the important messages?",
            "why is this message important?",
            "why are urgent messages marked?",
            "what needs my attention?",
            "what should i work on first?",
            "what are my pending tasks?",
            "give me my dashboard summary",
            "draft a reply to this message",
            "search my messages for meeting",
            "find messages from Ali",
            "show me messages from Ali",
            "open my inbox",
            "take me to my tasks",
            "show me attention",
            "hello jarvis",
            "help",
            "what can you do?",
        ],
    )
    def test_owned_elsewhere_returns_none(self, message):
        assert self._intent(message) is None

    def test_empty_and_unknown_return_none(self):
        assert self._intent("") is None
        assert self._intent("do the hokey pokey") is None


class TestMessageIntentEndpoint:
    def _authed(self, client, email="jarvis-msg-ep@test.com"):
        uid, tok = _register(client, email)
        _switch(client, tok)
        return uid

    def test_message_count(self, client, sync_db):
        uid = self._authed(client)
        _seed_message(sync_db, uid)
        _seed_message(sync_db, uid)
        _seed_message(sync_db, uid, status="read")

        res = _chat(client, "how many messages do I have?")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        assert "You have 3 messages in your inbox." in data["reply"]
        assert "2 are unread." in data["reply"]

    def test_message_count_zero(self, client):
        self._authed(client)
        res = _chat(client, "how many messages do I have?")
        assert res.json()["reply"] == "You have no messages in your inbox."

    def test_today_listing_shows_content(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(
            sync_db, uid, sender="Boss", subject="Review", content="Read this now",
            priority="important", when=now,
        )
        _seed_message(
            sync_db, uid, sender="Calm", subject="Lunch", content="Tomorrow?", when=now,
        )
        _seed_message(sync_db, uid, when=now - timedelta(days=1))  # yesterday

        res = _chat(client, "what messages came in today?")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        reply = data["reply"]
        assert "You received 2 messages today." in reply
        assert "Boss" in reply and "Review" in reply
        assert "Calm" in reply
        assert "1 important" in reply
        assert "1. " in reply  # actual listed content

    def test_today_listing_zero_keeps_phase3_wording(self, client, sync_db):
        uid = self._authed(client)
        _seed_message(sync_db, uid, when=datetime.now(timezone.utc) - timedelta(days=1))
        res = _chat(client, "what messages came in today?")
        assert "You have no messages today." in res.json()["reply"]

    def test_yesterday_listing(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(sync_db, uid, sender="Old", subject="Report", when=now - timedelta(days=1))
        _seed_message(sync_db, uid, sender="Old2", when=now - timedelta(days=1))
        _seed_message(sync_db, uid, sender="Today Guy", when=now)

        res = _chat(client, "show me yesterday's messages")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        reply = data["reply"]
        assert "You received 2 messages yesterday." in reply
        assert "Old" in reply and "Report" in reply
        assert "Today Guy" not in reply

    def test_yesterday_count(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(sync_db, uid, when=now - timedelta(days=1))
        _seed_message(sync_db, uid, status="read", when=now - timedelta(days=1))
        _seed_message(sync_db, uid, when=now)

        res = _chat(client, "how many messages did I get yesterday?")
        reply = res.json()["reply"]
        assert "You received 2 messages yesterday." in reply
        assert "1 unread" in reply

    def test_tell_me_whats_the_message_yesterday(self, client, sync_db):
        """The original unsupported phrasing now lists yesterday's messages."""
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(sync_db, uid, sender="Earlier", content="Notes", when=now - timedelta(days=1))
        res = _chat(client, "tell me what's the message yesterday")
        reply = res.json()["reply"]
        assert "You received 1 message yesterday." in reply
        assert "Earlier" in reply
        assert "Notes" in reply

    def test_weekday_listing(self, client, sync_db):
        uid = self._authed(client)
        monday = _most_recent_weekday_start("monday")
        _seed_message(sync_db, uid, sender="Mon Sender", subject="Kickoff", when=monday)
        _seed_message(sync_db, uid, sender="Mon Two", when=monday)
        _seed_message(sync_db, uid, when=monday + timedelta(days=1))  # tuesday

        res = _chat(client, "what messages on monday?")
        reply = res.json()["reply"]
        assert "You received 2 messages on monday." in reply
        assert "Mon Sender" in reply and "Kickoff" in reply
        assert "Mon Two" in reply

    def test_last_month_count(self, client, sync_db):
        uid = self._authed(client)
        today = _start_of_today_utc()
        last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        _seed_message(sync_db, uid, when=last_month)
        _seed_message(sync_db, uid, when=last_month + timedelta(days=3))
        _seed_message(sync_db, uid, when=today)

        res = _chat(client, "how many messages last month?")
        reply = res.json()["reply"]
        assert "You received 2 messages last month." in reply

    def test_list_messages_shows_actual_content(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(sync_db, uid, sender="Boss", subject="Review", content="Ship it", when=now)
        _seed_message(sync_db, uid, sender="Calm", status="read", when=now)

        res = _chat(client, "show me my messages")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        reply = data["reply"]
        assert "You have 2 messages in your inbox." in reply
        assert "Boss" in reply and "Review" in reply and "Ship it" in reply
        assert "1 unread" in reply

    def test_important_messages(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(sync_db, uid, sender="VIP", subject="Urgent", priority="urgent", when=now)
        _seed_message(sync_db, uid, sender="Boss", subject="Watch", priority="important", when=now)
        _seed_message(sync_db, uid, sender="Noise", subject="Newsletter", priority="normal", when=now)

        res = _chat(client, "which messages are important?")
        reply = res.json()["reply"]
        assert "2 messages marked important or urgent" in reply
        assert "VIP" in reply
        assert "Boss" in reply
        assert "Noise" not in reply

    def test_urgent_messages(self, client, sync_db):
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(sync_db, uid, sender="VIP", priority="urgent", when=now)
        _seed_message(sync_db, uid, sender="Boss", priority="important", when=now)
        _seed_message(sync_db, uid, sender="Noise", priority="normal", when=now)

        res = _chat(client, "which messages are urgent?")
        reply = res.json()["reply"]
        assert "1 urgent message:" in reply
        assert "VIP" in reply
        assert "Boss" not in reply
        assert "Noise" not in reply

    def test_priority_empty(self, client):
        self._authed(client)
        res = _chat(client, "which messages are urgent?")
        assert "No messages are currently marked urgent." in res.json()["reply"]
        res = _chat(client, "which messages are important?")
        assert "No messages are currently marked important or urgent." in res.json()["reply"]

    def test_isolation_other_users_messages_invisible(self, client, sync_db):
        uid_a = self._authed(client, "jarvis-msg-a@test.com")
        _seed_message(sync_db, uid_a, status="unread")
        _seed_message(sync_db, uid_a, sender="Loud", priority="urgent")

        uid_b, tok_b = _register(client, "jarvis-msg-b@test.com")
        _seed_message(sync_db, uid_b, sender="Private", priority="urgent")

        _switch(client, tok_b)
        count_b = _chat(client, "how many messages do I have?").json()
        urgent_b = _chat(client, "which messages are urgent?").json()
        list_b = _chat(client, "show me my messages").json()
        assert "1 message in your inbox" in count_b["reply"]
        assert "Private" in urgent_b["reply"]
        assert "Loud" not in urgent_b["reply"]
        assert "Loud" not in list_b["reply"]
        assert "Private" in list_b["reply"]

    def test_main_messages_in_120_messages(self, client, sync_db):
        """The previously-unsupported summarization phrasing now answers."""
        uid = self._authed(client)
        now = datetime.now(timezone.utc)
        _seed_message(sync_db, uid, sender="Alice", content="Project update", when=now)
        _seed_message(sync_db, uid, sender="Bob", content="Lunch plan", when=now)

        res = _chat(client, "what are the main messages in my 120 messages?")
        reply = res.json()["reply"]
        assert "Here's what your recent messages cover:" in reply
        assert "Alice" in reply
        assert "Bob" in reply


class TestSummarizeEndpoint:
    def _authed(self, client, email="jarvis-summary@test.com"):
        uid, tok = _register(client, email)
        _switch(client, tok)
        return uid

    def _seed_three(self, sync_db, uid):
        now = datetime.now(timezone.utc)
        _seed_message(
            sync_db, uid, sender="Alice", subject="Project", content="Deadline Friday",
            priority="important", when=now,
        )
        _seed_message(sync_db, uid, sender="Bob", content="Lunch tomorrow", when=now)
        _seed_message(sync_db, uid, sender="Carol", content="Updated the docs", when=now)

    def test_fallback_digest_without_key(self, client, sync_db):
        uid = self._authed(client)
        self._seed_three(sync_db, uid)
        res = _chat(client, "summarize my messages")
        data = res.json()
        assert data["action"] is None
        assert data["used_ai"] is False
        reply = data["reply"]
        assert "Here's what your recent messages cover:" in reply
        assert "Alice" in reply
        assert "1 is marked important or urgent" in reply

    def test_empty_no_messages(self, client):
        self._authed(client)
        res = _chat(client, "summarize my messages")
        assert res.json()["reply"] == "You have no messages to summarize."

    def _install_provider(self, monkeypatch, result=None, raises=False):
        class _FakeProvider:
            def __init__(self):
                _FakeProvider.instances.append(self)
                _FakeProvider.calls = []

            async def chat(self, prompt):
                if raises:
                    raise RuntimeError("summary exploded")
                _FakeProvider.calls.append(prompt)
                return result

        _FakeProvider.instances = []
        _FakeProvider.calls = []
        monkeypatch.setattr(
            "services.ai.jarvis_messages._llm_configured", lambda: True
        )
        monkeypatch.setattr(
            "services.ai.jarvis_messages.GroqProvider", _FakeProvider
        )
        return _FakeProvider

    def test_groq_summary_is_used(self, client, sync_db, monkeypatch):
        uid = self._authed(client)
        self._seed_three(sync_db, uid)
        fake = self._install_provider(monkeypatch, result={"summary": "AI digest"})

        res = _chat(client, "summarize my messages")
        data = res.json()
        assert fake.instances, "provider should have been called"
        assert len(fake.calls) == 1
        assert data["reply"] == "AI digest"
        assert data["used_ai"] is True

    def test_groq_summary_not_used_for_other_intents(self, client, sync_db, monkeypatch):
        uid = self._authed(client)
        self._seed_three(sync_db, uid)
        fake = self._install_provider(monkeypatch, result={"summary": "AI digest"})

        for message in (
            "how many messages do I have?",
            "show me my messages",
            "what messages came in today?",
            "which messages are urgent?",
        ):
            _chat(client, message)
        assert fake.instances == []

    def test_groq_malformed_output_falls_back(self, client, sync_db, monkeypatch):
        uid = self._authed(client)
        self._seed_three(sync_db, uid)
        for malformed in (None, "not json", ["nope"], {}, {"summary": ""}):
            self._install_provider(monkeypatch, result=malformed)
            res = _chat(client, "summarize my messages")
            assert res.status_code == 200
            assert "Here's what your recent messages cover:" in res.json()["reply"]
            assert res.json()["used_ai"] is False

    def test_groq_failure_falls_back(self, client, sync_db, monkeypatch):
        uid = self._authed(client)
        self._seed_three(sync_db, uid)
        self._install_provider(monkeypatch, raises=True)
        res = _chat(client, "summarize my messages")
        assert res.status_code == 200
        assert "Here's what your recent messages cover:" in res.json()["reply"]
        assert res.json()["used_ai"] is False
        assert res.json()["action"] is None