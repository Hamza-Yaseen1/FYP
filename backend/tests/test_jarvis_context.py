"""JARVIS conversational context - Part 4 (intelligent follow-ups) tests.

Covers the conversation layer added around the existing JARVIS parts:

- Contextually-aware follow-ups (pronouns, dates, corrections, comparisons) that
  reuse the user's previous message question without ever guessing content.
- Task-aware references ("which one is due first?", "delete that one") that
  resolve deterministically from real pending tasks and never auto-delete - a
  signed confirmation round-trip is always required for destruction.
- Context hygiene: the buffer is size-capped per user, an unrelated question
  resets the data topic, and all data stays scoped to the authenticated user.

The autouse fixture pins ``_llm_configured`` to False in every module and each
test registers a fresh email, so nothing here makes a real network call and no
context leaks across tests.
"""

from collections import deque
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from bson import ObjectId

REGISTER_BODY = {
    "name": "Jarvis Context User",
    "email": "jarvis-context@test.com",
    "password": "passA12345",
}

AVAILABILITY_UNIQUE = "conversational AI service is currently unavailable"


def _register(client, email="jarvis-context@test.com"):
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


def _authed(client, email="jarvis-context@test.com"):
    uid, tok = _register(client, email)
    _switch(client, tok)
    return uid


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


def _seed_task(sync_db, user_id, description, *, deadline=None, created_at=None):
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
                "source_message_preview": description[:80],
                "created_at": created_at or datetime.now(timezone.utc),
            }
        ).inserted_id
    )


def _start_of_today_utc():
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


@pytest.fixture(autouse=True)
def _stay_deterministic(monkeypatch):
    """Never allow real LLM calls - the deterministic paths are the point."""
    monkeypatch.setattr("services.ai.jarvis_intents._llm_configured", lambda: False)
    monkeypatch.setattr("services.ai.jarvis_agent._llm_configured", lambda: False)
    monkeypatch.setattr("services.ai.jarvis_messages._llm_configured", lambda: False)


# ---- Pure resolver / helper unit tests ---------------------------------------

def _ctx(topic="messages", intent=None, whens=()):
    return SimpleNamespace(
        last_data_topic=topic,
        last_message_intent=intent,
        ranges=deque({"when": w} for w in whens),
    )


class TestRangeUtils:
    def test_range_when_implicit_and_explicit(self):
        from services.ai.jarvis_messages import range_when

        assert range_when({"intent": "GET_TODAYS_MESSAGES", "params": {}}) == "today"
        assert range_when(
            {"intent": "GET_YESTERDAYS_MESSAGES", "params": {"when": "yesterday"}}
        ) == "yesterday"
        assert range_when(
            {"intent": "GET_MESSAGES_BY_DATE", "params": {"when": "last week"}}
        ) == "last week"
        assert range_when({"intent": "MESSAGE_COUNT", "params": {}}) is None
        assert range_when({"intent": "URGENT_MESSAGES", "params": {}}) is None

    def test_is_count_mode_inheritance(self):
        from services.ai.jarvis_messages import _is_count_mode

        assert _is_count_mode({"intent": "MESSAGE_COUNT", "params": {}}) is True
        assert _is_count_mode({"intent": "GET_TODAYS_MESSAGES", "params": {}}) is True
        assert _is_count_mode({"intent": "GET_TODAYS_MESSAGES", "params": {"list": True}}) is False
        assert _is_count_mode(
            {"intent": "GET_MESSAGES_BY_DATE", "params": {"count": True}}
        ) is True
        assert _is_count_mode({"intent": "IMPORTANT_MESSAGES", "params": {}}) is False
        assert _is_count_mode(None) is False


class TestContextResolverUnit:
    def _resolve(self, message, ctx):
        from services.ai.jarvis_messages import resolve_context_follow_up

        return resolve_context_follow_up(message, ctx)

    def test_locked_out_without_message_topic(self):
        assert self._resolve("what about yesterday?", _ctx(topic=None)) is None
        assert self._resolve("summarize them", _ctx(topic="tasks")) is None
        assert self._resolve("which ones?", _ctx(topic=None)) is None

    def test_date_follow_up_inherits_count_style(self):
        intent = self._resolve(
            "what about yesterday?", _ctx(intent={"intent": "GET_TODAYS_MESSAGES", "params": {}})
        )
        assert intent["intent"] == "GET_YESTERDAYS_MESSAGES"
        assert intent["params"]["count"] is True

    def test_date_follow_up_inherits_list_style(self):
        intent = self._resolve(
            "what about yesterday?",
            _ctx(intent={"intent": "GET_TODAYS_MESSAGES", "params": {"list": True}}),
        )
        assert intent["intent"] == "GET_YESTERDAYS_MESSAGES"
        assert intent["params"]["count"] is False

    def test_compare_needs_two_distinct_spans(self):
        intent = self._resolve("which day had more?", _ctx(whens=["today"]))
        assert intent["intent"] == "COMPARE_RANGES"
        assert intent["params"]["when"] == ["today"]
        intent = self._resolve("which day had more?", _ctx(whens=["today", "yesterday"]))
        assert intent["intent"] == "COMPARE_RANGES"
        assert intent["params"]["when"] == ["today", "yesterday"]

    def test_compare_uses_last_two_spans(self):
        intent = self._resolve("compare them", _ctx(whens=["today", "yesterday", "monday"]))
        assert intent["intent"] == "COMPARE_RANGES"
        assert intent["params"]["when"] == ["yesterday", "monday"]


class TestTaskResolutionUnit:
    def test_earliest_due_task_ranking(self):
        from services.ai.jarvis_agent import _earliest_due_task

        tasks = [
            {"description": "no deadline"},
            {"description": "next week", "deadline": "next week"},
            {"description": "tomorrow", "deadline": "tomorrow"},
            {"description": "today", "deadline": "today"},
        ]
        chosen = _earliest_due_task(tasks)
        assert chosen["description"] == "today"

    def test_select_ref_task_ambiguous_bare_reference(self):
        from services.ai.jarvis_agent import _select_ref_task

        tasks = [{"description": "A"}, {"description": "B"}]
        assert _select_ref_task(tasks, "Delete that one.") is None
        assert _select_ref_task(tasks, "Delete the first one.") is tasks[0]
        assert _select_ref_task(tasks, "Delete the second one.") is tasks[1]
        assert _select_ref_task([tasks[0]], "Delete that one.") is tasks[0]

    def test_context_history_is_size_capped(self):
        from services.ai.jarvis_agent import _ConversationContext

        ctx = _ConversationContext()
        for i in range(12):
            ctx.history.append({"role": "user", "text": f"turn {i}"})
        assert len(ctx.history) == 8
        assert ctx.history[-1]["text"] == "turn 11"


# ---- Manual Test 2: count question -> date follow-up -> comparison --------------

class TestCountFollowUpChain:
    def _seed(self, sync_db, uid):
        start_today = _start_of_today_utc()
        yesterday = start_today - timedelta(minutes=1)
        _seed_message_at(sync_db, uid, start_today + timedelta(hours=6), sender="Today A")
        _seed_message_at(
            sync_db, uid, start_today + timedelta(hours=7),
            sender="Today B", priority="important",
        )
        _seed_message_at(sync_db, uid, yesterday, sender="Yday Sender")

    def test_what_about_yesterday_inherits_count(self, client, sync_db):
        uid = _authed(client)
        self._seed(sync_db, uid)

        step1 = _chat(client, "How many messages did I get today?").json()
        assert "You received 2 messages today" in step1["reply"]

        step2 = _chat(client, "What about yesterday?").json()
        assert "You received 1 message yesterday" in step2["reply"]
        assert "main messages are" not in step2["reply"]

        step3 = _chat(client, "Which day had more?").json()
        assert "There were more messages today than yesterday" in step3["reply"]
        assert "2 compared to 1" in step3["reply"]
        assert step3["action"] is None

    def test_compare_when_counts_are_equal(self, client, sync_db):
        uid = _authed(client)
        start_today = _start_of_today_utc()
        _seed_message_at(sync_db, uid, start_today + timedelta(hours=6), sender="Today A")
        _seed_message_at(
            sync_db, uid, start_today - timedelta(minutes=1), sender="Yday A"
        )

        _chat(client, "How many messages did I get today?")
        _chat(client, "What about yesterday?")
        data = _chat(client, "Compare them.").json()
        assert "same number of messages today and yesterday" in data["reply"]
        assert "1 each" in data["reply"]

    def test_compare_without_two_spans_is_graceful(self, client, sync_db):
        uid = _authed(client)
        _seed_message_at(sync_db, uid, _start_of_today_utc() + timedelta(hours=6), sender="A")

        _chat(client, "How many messages did I get today?")
        data = _chat(client, "Which day had more?").json()
        assert "two time periods" in data["reply"]


# ---- Manual Test 1: priority listing -> urgent subset -> summarize --------------

class TestSummaryFollowUpChain:
    def test_show_important_then_urgent_then_summarize(self, client, sync_db):
        uid = _authed(client)
        start_today = _start_of_today_utc()
        _seed_message_at(
            sync_db, uid, start_today + timedelta(hours=6),
            sender="Important Sender", content="Please review the plan", priority="important",
        )
        _seed_message_at(
            sync_db, uid, start_today + timedelta(hours=7),
            sender="Urgent Sender", content="Need the numbers now", priority="urgent",
        )

        step1 = _chat(client, "Show my important messages.").json()
        assert "1 important message" in step1["reply"]
        assert "Urgent Sender" not in step1["reply"]
        assert "Important Sender" in step1["reply"]

        step2 = _chat(client, "Which ones are urgent?").json()
        assert "1 urgent message" in step2["reply"]
        assert "[urgent]" in step2["reply"]

        step3 = _chat(client, "Summarize them.").json()
        assert "Here's what your recent messages cover" in step3["reply"]
        assert step3["action"] is None


# ---- Manual Test 4: correction - "No, I mean yesterday." --------------------------

class TestCorrectionFollowUp:
    def seed(self, sync_db, uid):
        start_today = _start_of_today_utc()
        _seed_message_at(sync_db, uid, start_today + timedelta(hours=6), sender="Today A")
        _seed_message_at(sync_db, uid, start_today - timedelta(minutes=1),
                         sender="Yday Sender", content="Yesterday's digest")

    def test_no_i_mean_yesterday(self, client, sync_db):
        uid = _authed(client)
        self.seed(sync_db, uid)

        step1 = _chat(client, "Show today's messages.").json()
        assert "You received 1 message today" in step1["reply"]

        step2 = _chat(client, "No, I mean yesterday.").json()
        assert "1 message yesterday" in step2["reply"]
        assert "Yday Sender" in step2["reply"]
        assert step2["action"] is None

    def test_correction_selects_content_summary_after_priority(self, client, sync_db):
        uid = _authed(client)
        self.seed(sync_db, uid)

        _chat(client, "Show my important messages.")
        data = _chat(client, "No, I mean summarize them.").json()
        assert "Here's what your recent messages cover" in data["reply"]


# ---- Manual Test 3: task-aware due-first -------------------------------------------

class TestTaskDueFirst:
    def _seed(self, sync_db, uid):
        now = datetime.now(timezone.utc)
        base = now - timedelta(minutes=30)
        _seed_task(sync_db, uid, "Low priority thing", deadline="next week",
                   created_at=base + timedelta(minutes=0))
        _seed_task(sync_db, uid, "Medium thing", deadline="tomorrow",
                   created_at=base + timedelta(minutes=1))
        _seed_task(sync_db, uid, "Due Today Task", deadline="today",
                   created_at=base + timedelta(minutes=2))

    def test_which_one_is_due_first(self, client, sync_db):
        uid = _authed(client)
        self._seed(sync_db, uid)

        step1 = _chat(client, "Show my pending tasks.").json()
        assert step1["action"]["type"] == "navigation"

        step2 = _chat(client, "Which one is due first?").json()
        assert step2["reply"].startswith('You should start with "Due Today Task"')
        assert "by today" in step2["reply"]
        assert step2["action"] is None

    def test_due_first_with_no_pending_tasks_is_safe(self, client, sync_db):
        _authed(client)
        data = _chat(client, "Which one is due first?").json()
        assert "nothing is due first" in data["reply"]
        assert data["action"] is None


# ---- Manual Test 6: "Delete that one." -----------------------------------------------

class TestDeleteThatOne:
    def test_single_task_confirms_then_deletes(self, client, sync_db):
        uid = _authed(client)
        _seed_task(sync_db, uid, "Only Task")

        _chat(client, "Show my tasks.")
        step2 = _chat(client, "Delete that one.").json()
        assert step2["reply"] == 'Do you want me to delete the task "Only Task"?'
        assert step2["action"]["type"] == "request_confirmation"
        assert step2["action"]["detail"]["pending_type"] == "delete_task"
        token = step2["action"]["confirmation_token"]

        confirmed = _confirm(client, token).json()
        assert confirmed["reply"] == 'Deleted the task "Only Task".'
        assert sync_db.tasks.count_documents({"user_id": uid}) == 0

    def test_ambiguous_reference_clarifies_then_ordinal_confirms(self, client, sync_db):
        uid = _authed(client)
        now = datetime.now(timezone.utc)
        _seed_task(sync_db, uid, "Task A", created_at=now - timedelta(minutes=2))
        _seed_task(sync_db, uid, "Task B", created_at=now - timedelta(minutes=1))

        _chat(client, "Show my tasks.")
        step2 = _chat(client, "Delete that one.").json()
        assert "Which task do you mean?" in step2["reply"]
        assert "Task A" in step2["reply"] and "Task B" in step2["reply"]
        assert step2["action"] is None

        step3 = _chat(client, "Delete the first one.").json()
        assert step3["action"]["type"] == "request_confirmation"
        assert "Task B" in step3["reply"]

        confirmed = _confirm(client, step3["action"]["confirmation_token"]).json()
        assert confirmed["reply"] == 'Deleted the task "Task B".'
        remaining = list(sync_db.tasks.find({"user_id": uid, "status": "pending"}))
        assert len(remaining) == 1
        assert remaining[0]["description"] == "Task A"

    def test_cancel_keeps_task(self, client, sync_db):
        uid = _authed(client)
        _seed_task(sync_db, uid, "Only Task")

        _chat(client, "Show my tasks.")
        step2 = _chat(client, "Delete that one.").json()
        cancelled = _confirm(client, step2["action"]["confirmation_token"], confirmed=False).json()
        assert "I have not made any changes" in cancelled["reply"]
        assert sync_db.tasks.count_documents({"user_id": uid}) == 1

    def test_delete_ref_without_any_task_is_safe(self, client, sync_db):
        _authed(client)
        data = _chat(client, "Delete that one.").json()
        assert "task in context" in data["reply"]
        assert data["action"] is None
        assert sync_db.tasks.count_documents({}) == 0


# ---- Security: context and confirmations never cross users ---------------------------

class TestSecurity:
    def test_confirmation_token_from_other_user_is_rejected(self, client, sync_db):
        uid_a = _authed(client, "jarvis-ctx-a@test.com")
        _seed_task(sync_db, uid_a, "A's Task")

        _chat(client, "Show my tasks.")
        step2 = _chat(client, "Delete that one.").json()
        token = step2["action"]["confirmation_token"]

        uid_b, tok_b = _register(client, "jarvis-ctx-b@test.com")
        _switch(client, tok_b)

        res = _confirm(client, token)
        assert res.status_code == 200
        assert "invalid" in res.json()["reply"].lower()
        assert sync_db.tasks.count_documents({"user_id": uid_a}) == 1
        assert sync_db.tasks.count_documents({"user_id": uid_b}) == 0

    def test_context_is_per_user(self, client, sync_db):
        uid_a = _authed(client, "jarvis-ctx-a@test.com")
        _seed_message_at(sync_db, uid_a, _start_of_today_utc() + timedelta(hours=6),
                         sender="Secret Sender")
        _chat(client, "Show my messages.")

        uid_b, tok_b = _register(client, "jarvis-ctx-b@test.com")
        _switch(client, tok_b)
        data = _chat(client, "Summarize them.").json()
        assert AVAILABILITY_UNIQUE in data["reply"]
        assert "Secret Sender" not in data["reply"]

    def test_task_follow_up_scoped_by_user(self, client, sync_db):
        uid_a = _authed(client, "jarvis-ctx-a@test.com")
        _seed_task(sync_db, uid_a, "A's Due Task", deadline="today")

        _chat(client, "Show my tasks.")
        data = _chat(client, "Delete that one.").json()
        assert data["action"]["type"] == "request_confirmation"

        uid_b, tok_b = _register(client, "jarvis-ctx-b@test.com")
        _switch(client, tok_b)
        _chat(client, "Show my tasks.")
        data_b = _chat(client, "Delete that one.").json()
        assert "task in context" in data_b["reply"]
        assert data_b["action"] is None


# ---- Context hygiene ----------------------------------------------------------------

class TestContextHygiene:
    def test_unrelated_question_resets_follow_ups(self, client, sync_db):
        uid = _authed(client)
        _seed_message_at(sync_db, uid, _start_of_today_utc() + timedelta(hours=6),
                         sender="Today A")

        _chat(client, "How many messages do I have?")
        probe = _chat(client, "What is Python used for?").json()
        assert AVAILABILITY_UNIQUE in probe["reply"]

        step3 = _chat(client, "Summarize them").json()
        assert AVAILABILITY_UNIQUE in step3["reply"]
        assert "recent messages cover" not in step3["reply"]

    def test_pronoun_follow_up_after_count_lists(self, client, sync_db):
        uid = _authed(client)
        start_today = _start_of_today_utc()
        _seed_message_at(sync_db, uid, start_today + timedelta(hours=6), sender="Today A")

        _chat(client, "How many messages do I have?")
        step2 = _chat(client, "Which ones?").json()
        assert "Today A" in step2["reply"]
        assert step2["action"] is None

    def test_task_actions_record_task_context(self, client, sync_db):
        uid = _authed(client)
        now = datetime.now(timezone.utc)
        _seed_task(sync_db, uid, "Alpha", deadline="today",
                   created_at=now - timedelta(minutes=1))
        _seed_task(sync_db, uid, "Beta", deadline="tomorrow",
                   created_at=now - timedelta(minutes=0))

        data = _chat(client, "What tasks are pending?").json()
        assert "2 pending tasks" in data["reply"]
        assert "Alpha" in data["reply"]

        step2 = _chat(client, "Which one is due first?").json()
        assert step2["reply"].startswith('You should start with "Alpha"')

    def test_delete_ref_after_message_context_is_not_a_task_delete(self, client, sync_db):
        uid = _authed(client)
        _seed_message_at(sync_db, uid, _start_of_today_utc() + timedelta(hours=6),
                         sender="Today A")
        _seed_task(sync_db, uid, "Background Task")

        _chat(client, "Show my messages.")
        data = _chat(client, "Delete that one.").json()
        assert data["action"] is None
        assert sync_db.tasks.count_documents({"user_id": uid}) == 1