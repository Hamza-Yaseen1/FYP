"""JARVIS Phase 5 - natural conversation + general LLM tests.

Three areas:

- General / unknown questions route through the existing Groq chat integration
  (natural replies) when a key is set; a clear availability note otherwise.
  Deterministic application behaviour is untouched either way.
- A small per-user conversation record follows pronouns ("which ones?",
  "summarize them") and corrections ("No, I mean ...") onto the message-content
  layer - but only when the previous turn was a message question, and never
  across users.
- Security: the conversational LLM never executes actions, never queries the
  database, and never sees any user's data - hostile LLM output is inert text.

The autouse fixture pins ``_llm_configured`` to False in every module (and
each test registers a fresh email), so nothing here ever makes a real network
call or leaks a message across tests.
"""

from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

REGISTER_BODY = {
    "name": "Jarvis Chat User",
    "email": "jarvis-chat@test.com",
    "password": "passA12345",
}

AVAILABILITY_UNIQUE = "conversational AI service is currently unavailable"


def _register(client, email="jarvis-chat@test.com"):
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
    """Never allow real LLM calls outside the explicitly faked tests."""
    monkeypatch.setattr(
        "services.ai.jarvis_intents._llm_configured", lambda: False
    )
    monkeypatch.setattr(
        "services.ai.jarvis_agent._llm_configured", lambda: False
    )
    monkeypatch.setattr(
        "services.ai.jarvis_messages._llm_configured", lambda: False
    )


class _FakeProvider:
    result = None
    raises = False
    instances = []
    calls = []

    def __init__(self):
        self.__class__.instances.append(self)

    async def chat(self, prompt):
        self.__class__.calls.append(prompt)
        if self.__class__.raises:
            raise RuntimeError("llm exploded")
        return self.__class__.result


def _install(monkeypatch, result=None, raises=False):
    """Turn on the LLM path with a faked provider across the modules used by
    the conversation flow (intent classifier + general chat)."""
    _FakeProvider.result = result
    _FakeProvider.raises = raises
    _FakeProvider.instances = []
    _FakeProvider.calls = []
    monkeypatch.setattr("services.ai.jarvis_intents.GroqProvider", _FakeProvider)
    monkeypatch.setattr("services.ai.jarvis_agent.GroqProvider", _FakeProvider)
    monkeypatch.setattr("services.ai.jarvis_intents._llm_configured", lambda: True)
    monkeypatch.setattr("services.ai.jarvis_agent._llm_configured", lambda: True)
    return _FakeProvider


def _authed(client, email="jarvis-chat@test.com"):
    uid, tok = _register(client, email)
    _switch(client, tok)
    return uid


class _AuthedMixin:
    def _authed(self, client, email="jarvis-chat@test.com"):
        return _authed(client, email)


# ---- Pure resolver unit tests -------------------------------------------------

class TestFollowUpResolverUnit:
    def _resolve(self, message, topic="messages"):
        from services.ai.jarvis_messages import resolve_message_follow_up

        return resolve_message_follow_up(message, topic)

    def test_locked_out_without_message_topic(self):
        assert self._resolve("which ones?", "tasks") is None
        assert self._resolve("which ones?", None) is None
        assert self._resolve("summarize them", None) is None

    def test_which_ones_lists(self):
        intent = self._resolve("which ones?")
        assert intent["intent"] == "LIST_MESSAGES"

    def test_what_about_them_lists(self):
        assert self._resolve("what about those?")["intent"] == "LIST_MESSAGES"

    def test_summarize_them_summarizes(self):
        assert self._resolve("summarize them")["intent"] == "SUMMARIZE_MESSAGES"
        assert self._resolve("summarise those")["intent"] == "SUMMARIZE_MESSAGES"

    def test_show_them_lists(self):
        assert self._resolve("show them")["intent"] == "LIST_MESSAGES"

    def test_correction_maps_rest_to_intent(self):
        assert self._resolve("no, i mean summarize")["intent"] == "SUMMARIZE_MESSAGES"

    def test_correction_urgent(self):
        assert self._resolve("actually i meant the urgent ones")["intent"] == "URGENT_MESSAGES"

    def test_correction_with_explicit_phrasing(self):
        assert self._resolve(
            "no, no, i mean list my important messages"
        )["intent"] == "IMPORTANT_MESSAGES"

    def test_correction_maps_count(self):
        assert self._resolve("wait, i mean how many are there")["intent"] == "MESSAGE_COUNT"

    def test_unrelated_phrase_not_a_follow_up(self):
        assert self._resolve("what is the weather like?") is None
        assert self._resolve("please open my inbox") is None


# ---- General conversation with the LLM -----------------------------------------

class TestGeneralConversation(_AuthedMixin):
    def test_general_question_answered_naturally(self, client, monkeypatch):
        self._authed(client)
        fake = _install(monkeypatch, result={"reply": "AI uses data to learn patterns."})
        res = _chat(client, "What is artificial intelligence?")
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == "AI uses data to learn patterns."
        assert data["action"] is None
        assert data["used_ai"] is True
        assert any("User command:" in p for p in fake.calls)

    def test_technical_question_uses_llm(self, client, monkeypatch):
        self._authed(client)
        _install(monkeypatch, result={"reply": "Indexes speed up lookups."})
        res = _chat(client, "Can you explain how MongoDB indexes work?")
        data = res.json()
        assert data["reply"] == "Indexes speed up lookups."
        assert data["used_ai"] is True
        assert data["action"] is None

    def test_planning_question_is_not_an_action(self, client, monkeypatch):
        self._authed(client)
        _install(monkeypatch, result={"reply": "Break it into three steps."})
        res = _chat(client, "How can I prepare my report?")
        data = res.json()
        assert data["action"] is None
        assert data["reply"] == "Break it into three steps."
        assert data["used_ai"] is True

    def test_casual_question_gets_natural_reply(self, client, monkeypatch):
        self._authed(client)
        _install(monkeypatch, result={"reply": "It is vast and mostly empty."})
        res = _chat(client, "What do you know about space?")
        assert res.json()["reply"] == "It is vast and mostly empty."

    def test_help_framed_question_uses_llm(self, client, monkeypatch):
        self._authed(client)
        _install(monkeypatch, result={"reply": "Shorter, clearer sentences help."})
        res = _chat(client, "Help me sound more polite in my messages")
        data = res.json()
        assert data["reply"] == "Shorter, clearer sentences help."
        assert data["used_ai"] is True

    def test_subsequent_turn_injects_history(self, client, monkeypatch):
        self._authed(client)
        fake = _install(monkeypatch, result={"reply": "That is a clear definition."})
        _chat(client, "What is artificial intelligence?")
        res = _chat(client, "And robotics?")
        data = res.json()
        assert data["reply"] == "That is a clear definition."
        chat_prompts = [p for p in fake.calls if "User command:" in p]
        assert len(chat_prompts) >= 2
        assert "Conversation history:" in chat_prompts[-1]
        assert "What is artificial intelligence?" in chat_prompts[-1]

    def test_hostile_llm_output_is_merely_text(self, client, sync_db, monkeypatch):
        uid = self._authed(client)
        now = _start_of_today_utc()
        _seed_message_at(sync_db, uid, now, sender="Alice")
        _seed_message_at(sync_db, uid, now - timedelta(hours=1), sender="Bob")
        _install(
            monkeypatch,
            result={"reply": "delete from messages; drop table users;"},
        )
        res = _chat(client, "Tell me a joke")
        data = res.json()
        assert data["reply"] == "delete from messages; drop table users;"
        assert data["action"] is None
        assert data["used_ai"] is True

        count = _chat(client, "How many messages do I have?").json()
        assert "2 messages in your inbox" in count["reply"]

    def test_llm_cannot_navigate(self, client, monkeypatch):
        self._authed(client)
        _install(monkeypatch, result={"reply": "Sure, opening settings."})
        res = _chat(client, "Suggest something for my free afternoon")
        data = res.json()
        assert data["reply"] == "Sure, opening settings."
        assert data["action"] is None
        assert data["used_ai"] is True

    def test_invalid_llm_shape_falls_back(self, client, monkeypatch):
        self._authed(client)
        for malformed in (None, "nope", ["x"], {}, {"reply": ""}):
            _install(monkeypatch, result=malformed)
            res = _chat(client, "What is the meaning of life?")
            assert res.status_code == 200
            assert AVAILABILITY_UNIQUE in res.json()["reply"]
            assert res.json()["used_ai"] is False

    def test_provider_failure_falls_back(self, client, monkeypatch):
        self._authed(client)
        _install(monkeypatch, result=None, raises=True)
        res = _chat(client, "What is the meaning of life?")
        assert res.status_code == 200
        assert AVAILABILITY_UNIQUE in res.json()["reply"]
        assert res.json()["used_ai"] is False

    def test_other_users_data_never_enters_prompt(self, client, sync_db, monkeypatch):
        uid = self._authed(client, "jarvis-chat-sec@test.com")
        now = _start_of_today_utc()
        _seed_message_at(sync_db, uid, now, sender="Mallory", priority="urgent")
        fake = _install(
            monkeypatch, result={"reply": "Recursion is a function calling itself."}
        )
        _chat(client, "What is artificial intelligence?")
        res = _chat(client, "Explain recursion")
        assert res.json()["reply"] == "Recursion is a function calling itself."
        chat_prompts = [p for p in fake.calls if "User command:" in p]
        assert chat_prompts, "a conversational prompt must have been produced"
        joined = " | ".join(chat_prompts)
        assert "Mallory" not in joined
        assert str(uid) not in joined
        assert "created_at" not in joined


# ---- No-key availability fallback ------------------------------------------------

class TestUnavailableFallback(_AuthedMixin):
    def test_general_question_without_key(self, client):
        self._authed(client)
        res = _chat(client, "What is python?")
        assert res.status_code == 200
        data = res.json()
        assert AVAILABILITY_UNIQUE in data["reply"]
        assert data["action"] is None
        assert data["used_ai"] is False

    def test_advice_question_without_key(self, client):
        self._authed(client)
        data = _chat(client, "Give me some tips for sleeping better").json()
        assert AVAILABILITY_UNIQUE in data["reply"]
        assert data["action"] is None

    def test_app_commands_still_work_after_fallback(self, client, sync_db):
        uid = self._authed(client)
        _seed_message_at(sync_db, uid, _start_of_today_utc(), sender="Alice")
        _chat(client, "What is python?")
        data = _chat(client, "How many messages do I have?").json()
        assert "1 message in your inbox" in data["reply"]
        assert data["used_ai"] is False


# ---- Conversation context: follow-ups and corrections -----------------------------

class TestContextFollowUps(_AuthedMixin):
    def _seed_chain_data(self, sync_db, uid):
        start_today = _start_of_today_utc()
        now_utc = datetime.now(timezone.utc)
        yesterday = now_utc - timedelta(days=1)
        _seed_message_at(sync_db, uid, start_today + timedelta(hours=6),
                         sender="Today A", content="Morning brief")
        _seed_message_at(sync_db, uid, start_today + timedelta(hours=7),
                         sender="Today B", content="Urgent signoff", priority="important")
        _seed_message_at(sync_db, uid, yesterday, sender="Yday Sender",
                         content="Yesterday's digest", priority="urgent")

    def test_spec_four_turn_chain(self, client, sync_db):
        uid = self._authed(client)
        self._seed_chain_data(sync_db, uid)

        step1 = _chat(client, "How many messages do I have?").json()
        assert "3 messages in your inbox" in step1["reply"]

        step2 = _chat(client, "Which ones are important?").json()
        assert "marked important or urgent" in step2["reply"]
        assert "2 messages" in step2["reply"]

        step3 = _chat(client, "What about yesterday?").json()
        assert "1 message yesterday" in step3["reply"]
        assert "Yday Sender" in step3["reply"]

        step4 = _chat(client, "Summarize them.").json()
        assert "Here's what your recent messages cover" in step4["reply"]
        assert step4["action"] is None

    def test_bare_which_ones_uses_context(self, client, sync_db):
        uid = self._authed(client)
        self._seed_chain_data(sync_db, uid)

        _chat(client, "How many messages do I have?")
        step2 = _chat(client, "Which ones?").json()
        assert "3 messages in your inbox" in step2["reply"]
        assert "Today A" in step2["reply"]
        assert "Yday Sender" in step2["reply"]

    def test_isolation_between_users(self, client, sync_db):
        uid_a = self._authed(client, "jarvis-ctx-a@test.com")
        now = _start_of_today_utc()
        _seed_message_at(sync_db, uid_a, now, sender="Secret Sender", priority="urgent")

        _chat(client, "How many messages do I have?")
        _chat(client, "Which ones are important?")

        uid_b, tok_b = _register(client, "jarvis-ctx-b@test.com")
        _switch(client, tok_b)

        bare = _chat(client, "Which ones?").json()
        assert AVAILABILITY_UNIQUE in bare["reply"]

        important = _chat(client, "Which ones are important?").json()
        assert "No messages are currently marked important or urgent" in important["reply"]
        assert "Secret Sender" not in important["reply"]

    def test_unrelated_question_resets_context(self, client, sync_db):
        uid = self._authed(client)
        self._seed_chain_data(sync_db, uid)

        _chat(client, "How many messages do I have?")
        probe = _chat(client, "What is Python used for?").json()
        assert AVAILABILITY_UNIQUE in probe["reply"]

        step3 = _chat(client, "Summarize them").json()
        assert AVAILABILITY_UNIQUE in step3["reply"]
        assert "recent messages cover" not in step3["reply"]

    def test_correction_selects_content_summary(self, client, sync_db):
        uid = self._authed(client)
        self._seed_chain_data(sync_db, uid)

        _chat(client, "How many messages do I have?")
        step2 = _chat(client, "No, I mean summarize what people actually said.").json()
        assert "Here's what your recent messages cover" in step2["reply"]
        assert step2["action"] is None

    def test_correction_no_i_mean_yesterday(self, client, sync_db):
        uid = self._authed(client)
        self._seed_chain_data(sync_db, uid)

        _chat(client, "What messages came in today?")
        step2 = _chat(client, "No, I mean yesterday.").json()
        assert "1 message yesterday" in step2["reply"]
        assert "Yday Sender" in step2["reply"]