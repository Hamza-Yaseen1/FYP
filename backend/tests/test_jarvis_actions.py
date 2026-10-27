"""JARVIS Phase 2 — real agent action tests.

Covers create / complete / delete / list tasks, message search (sender +
keyword), summarize unread, important-message lists, attention analysis,
reply drafting, the confirmation door (create/delete require a signed token
round-trip), ownership/isolation, ambiguous commands, and graceful failures.

Like Phase 1, routing is deterministic in the test environment (no
``GROQ_API_KEY``): every reply is fully assertable except the two draft-reply
cases that monkeypatch the provider.
"""

from datetime import datetime, timezone

import pytest
from bson import ObjectId


@pytest.fixture(autouse=True)
def _stay_deterministic(monkeypatch):
    """Pin LLM availability off so deterministic replies are assertable.

    ``conftest`` loads the real ``backend/.env`` (which contains an actual
    ``GROQ_API_KEY``), and acting intent/draft paths consult ``_llm_configured``,
    so tests that assert deterministic drafts must opt out of the LLM.
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
    monkeypatch.setattr(
        "services.ai.jarvis_actions._llm_configured", lambda: False
    )


REGISTER_BODY = {
    "name": "Jarvis Action User",
    "email": "jarvis-action@test.com",
    "password": "passA12345",
}


def _register(client, email="jarvis-action@test.com"):
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


def _seed_message(
    sync_db,
    user_id,
    *,
    status="unread",
    sender="Sender",
    content="A message",
    subject=None,
    priority=None,
    needs_attention=False,
    explanation=None,
    summary=None,
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
    if subject:
        doc["subject"] = subject
    if priority or needs_attention or explanation or summary:
        ai = {
            "priority": priority or "normal",
            "needs_attention": needs_attention,
            "status": "completed",
        }
        if explanation:
            ai["explanation"] = explanation
        if summary:
            ai["summary"] = summary
        doc["ai_analysis"] = ai
    return str(sync_db.messages.insert_one(doc).inserted_id)


def _seed_task(sync_db, user_id, description, status="pending", deadline=None, priority=None):
    now = datetime.now(timezone.utc)
    return str(
        sync_db.tasks.insert_one(
            {
                "user_id": user_id,
                "description": description,
                "deadline": deadline,
                "priority_indicator": priority,
                "requires_action": True,
                "status": status,
                "source_message_id": str(ObjectId()),
                "source_message_preview": description[:80],
                "created_at": now,
                "updated_at": now,
            }
        ).inserted_id
    )


def _get_task(sync_db, task_id):
    return sync_db.tasks.find_one({"_id": ObjectId(task_id)})


@pytest.fixture()
def authed_client(client):
    _, tok = _register(client)
    _switch(client, tok)
    return client


# ── Create task ─────────────────────────────────────────────────────────────

class TestCreateTask:
    def test_create_task_requires_confirmation_then_creates(self, authed_client, sync_db):
        res = _chat(authed_client, "create a task to submit my FYP report tomorrow")
        assert res.status_code == 200
        data = res.json()
        assert data["action"]["type"] == "request_confirmation"
        assert data["action"]["detail"]["pending_type"] == "create_task"
        token = data["action"]["confirmation_token"]
        assert token
        assert "submit my fyp report" in data["reply"].lower()
        assert sync_db.tasks.count_documents({}) == 0

        res = _confirm(authed_client, token)
        assert res.status_code == 200
        reply = res.json()["reply"]
        assert "created" in reply.lower()
        assert res.json()["action"]["type"] == "create_task"

        tasks = list(sync_db.tasks.find({}))
        assert len(tasks) == 1
        assert tasks[0]["description"] == "submit my fyp report"
        assert tasks[0]["deadline"] == "tomorrow"
        assert tasks[0]["status"] == "pending"

    def test_create_task_parses_priority_and_deadline(self, authed_client, sync_db):
        res = _chat(
            authed_client,
            "create a high priority task to finish documentation by Friday",
        )
        data = res.json()
        assert data["action"]["type"] == "request_confirmation"
        summary = data["action"]["detail"]["summary"].lower()
        assert "finish documentation" in summary
        assert "important" in summary
        assert "friday" in summary

        _confirm(authed_client, data["action"]["confirmation_token"])
        task = sync_db.tasks.find_one({})
        assert task["description"] == "finish documentation"
        assert task["deadline"] == "friday"
        assert task["priority_indicator"] == "important"

    def test_create_task_called_form(self, authed_client, sync_db):
        data = _chat(authed_client, "add a task called finish documentation").json()
        assert data["action"]["type"] == "request_confirmation"
        _confirm(authed_client, data["action"]["confirmation_token"])
        task = sync_db.tasks.find_one({})
        assert task["description"] == "finish documentation"
        assert task["deadline"] is None
        assert task["priority_indicator"] is None

    def test_create_task_missing_title_asks_for_clarification(self, authed_client, sync_db):
        data = _chat(authed_client, "create a task").json()
        assert data["action"] is None
        assert "title" in data["reply"].lower()
        assert sync_db.tasks.count_documents({}) == 0

    def test_confirm_cancel_does_not_create(self, authed_client, sync_db):
        data = _chat(authed_client, "create a task called stay canceled").json()
        token = data["action"]["confirmation_token"]
        res = _confirm(authed_client, token, confirmed=False)
        assert res.status_code == 200
        assert "not made any changes" in res.json()["reply"]
        assert sync_db.tasks.count_documents({}) == 0

    def test_confirm_with_invalid_token_is_safe(self, authed_client, sync_db):
        res = _confirm(authed_client, "not-a-real-token")
        assert res.status_code == 200
        assert "expired or is invalid" in res.json()["reply"]
        assert sync_db.tasks.count_documents({}) == 0

    def test_confirmation_token_cannot_be_used_by_another_user(self, client, sync_db):
        uid_a, tok_a = _register(client, "jarvis-action-owner-a@test.com")
        uid_b, tok_b = _register(client, "jarvis-action-owner-b@test.com")

        _switch(client, tok_a)
        data = _chat(client, "create a task called shared-confirm").json()
        token = data["action"]["confirmation_token"]

        _switch(client, tok_b)
        res = _confirm(client, token)
        assert res.status_code == 200
        assert "expired or is invalid" in res.json()["reply"]
        assert sync_db.tasks.count_documents({}) == 0

        _switch(client, tok_a)
        _confirm(client, token)
        assert sync_db.tasks.count_documents({"user_id": uid_a, "description": "shared-confirm"}) == 1

    def test_confirm_endpoint_allows_empty_message_with_token(self, authed_client, sync_db):
        data = _chat(authed_client, "create a task called blank-message").json()
        token = data["action"]["confirmation_token"]
        res = authed_client.post(
            "/jarvis/chat",
            json={"message": "", "confirmation_token": token, "confirmed": True},
        )
        assert res.status_code == 200
        assert "created" in res.json()["reply"].lower()
        assert sync_db.tasks.count_documents({"description": "blank-message"}) == 1


# ── Complete task ───────────────────────────────────────────────────────────

class TestCompleteTask:
    def test_complete_task_by_name_direct(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Call the vendor", deadline="Friday")

        res = _chat(authed_client, "complete my task call the vendor")
        assert res.status_code == 200
        data = res.json()
        assert data["action"]["type"] == "complete_task"
        assert "now completed" in data["reply"]
        assert (sync_db.tasks.find_one({}) or {}).get("status") == "completed"

    def test_mark_task_as_completed_form(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Submit report")

        res = _chat(authed_client, "mark my task submit report as completed")
        assert res.status_code == 200
        assert res.json()["action"]["type"] == "complete_task"
        assert (sync_db.tasks.find_one({}) or {}).get("status") == "completed"

    def test_complete_task_not_found(self, authed_client, sync_db):
        res = _chat(authed_client, "complete my task does not exist")
        assert res.status_code == 200
        data = res.json()
        assert data["action"] is None
        assert "couldn't find" in data["reply"]

    def test_complete_task_ambiguous_lists_matches(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Prepare the report")
        _seed_task(sync_db, uid, "Prepare the deck")

        res = _chat(authed_client, "complete my task prepare")
        data = res.json()
        assert data["action"] is None
        assert "few tasks" in data["reply"]
        assert sync_db.tasks.count_documents({"status": {"$ne": "completed"}}) == 2

    def test_complete_task_missing_name_clarifies(self, authed_client):
        data = _chat(authed_client, "complete my task").json()
        assert data["action"] is None
        assert "which task" in data["reply"].lower()

    def test_completed_task_not_completable_again(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Already done", status="completed")
        data = _chat(authed_client, "complete my task already done").json()
        assert "couldn't find" in data["reply"]


# ── Delete task (confirmation-gated) ────────────────────────────────────────

class TestDeleteTask:
    def test_delete_requires_confirmation_then_deletes(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Call the vendor")

        res = _chat(authed_client, "delete my task call the vendor")
        assert res.status_code == 200
        data = res.json()
        assert data["action"]["type"] == "request_confirmation"
        assert "delete" in data["reply"].lower()
        assert sync_db.tasks.count_documents({}) == 1

        res = _confirm(authed_client, data["action"]["confirmation_token"])
        assert res.status_code == 200
        assert "deleted" in res.json()["reply"].lower()
        assert res.json()["action"]["type"] == "delete_task"
        assert sync_db.tasks.count_documents({}) == 0

    def test_delete_cancel_keeps_task(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Keep me")

        data = _chat(authed_client, "delete my task keep me").json()
        token = data["action"]["confirmation_token"]
        res = _confirm(authed_client, token, confirmed=False)
        assert "not made any changes" in res.json()["reply"]
        assert sync_db.tasks.count_documents({}) == 1

    def test_delete_task_not_found(self, authed_client):
        res = _chat(authed_client, "delete my task not here anywhere")
        assert res.status_code == 200
        data = res.json()
        assert data["action"] is None
        assert "couldn't find" in data["reply"]

    def test_delete_ambiguous_lists_matches(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Prepare the report")
        _seed_task(sync_db, uid, "Prepare the deck")
        data = _chat(authed_client, "delete my task prepare").json()
        assert data["action"] is None
        assert "few tasks" in data["reply"]


# ── Task ownership isolation ────────────────────────────────────────────────

class TestTaskOwnership:
    def test_cannot_complete_or_delete_another_users_task(self, client, sync_db):
        uid_a, tok_a = _register(client, "jarvis-owner-a3@test.com")
        uid_b, tok_b = _register(client, "jarvis-owner-b3@test.com")
        task_id = _seed_task(sync_db, uid_a, "Alice's private task")

        _switch(client, tok_b)
        res = _chat(client, "complete my task alice's private task")
        assert "couldn't find" in res.json()["reply"]
        res = _chat(client, "delete my task alice's private task")
        assert "couldn't find" in res.json()["reply"]
        assert _get_task(sync_db, task_id)["status"] != "completed"

        _switch(client, tok_a)
        data = _chat(client, "delete my task alice's private task").json()
        assert data["action"]["type"] == "request_confirmation"
        _confirm(client, data["action"]["confirmation_token"])
        assert sync_db.tasks.count_documents({}) == 0


# ── Message actions ─────────────────────────────────────────────────────────

class TestMessageSearch:
    def test_find_messages_from_sender(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Ali Manager", content="Send the deck", subject="Deck")
        _seed_message(sync_db, uid, sender="Bo", content="Unrelated")

        data = _chat(authed_client, "find messages from Ali").json()
        assert data["action"]["type"] == "search_messages"
        assert data["action"]["detail"]["count"] == 1
        assert "ali manager" in data["reply"].lower()
        assert "bo" not in data["reply"].lower()

    def test_sender_search_stays_with_owner(self, client, sync_db):
        uid_a, tok_a = _register(client, "jarvis-msg-owner-a@test.com")
        uid_b, tok_b = _register(client, "jarvis-msg-owner-b@test.com")
        _seed_message(sync_db, uid_a, sender="Ghost", content="Secret handshake")
        _seed_message(sync_db, uid_b, sender="Ghost", content="Nice day")

        _switch(client, tok_a)
        data = _chat(client, "find messages from Ghost").json()
        assert "secret handshake" in data["reply"].lower()
        assert "nice day" not in data["reply"].lower()

        _switch(client, tok_b)
        data = _chat(client, "find messages from Ghost").json()
        assert "nice day" in data["reply"].lower()
        assert "secret handshake" not in data["reply"].lower()

    def test_search_by_keyword(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, content="Can we meet at 10 for the standup?", subject="Meeting")
        _seed_message(sync_db, uid, content="Lunch menu attached")

        data = _chat(authed_client, "search my messages for meeting").json()
        assert data["action"]["type"] == "search_messages"
        assert data["action"]["detail"]["count"] >= 1
        assert "meeting" in data["reply"].lower()

    def test_search_by_keyword_no_results(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, content="hello")
        res = _chat(authed_client, "search my messages for zzzzz")
        assert res.status_code == 200
        data = res.json()
        assert data["action"]["detail"]["count"] == 0
        assert "no messages" in data["reply"].lower()

    def test_keyword_search_cannot_see_other_users(self, client, sync_db):
        uid_a, tok_a = _register(client, "jarvis-keyword-a@test.com")
        uid_b, tok_b = _register(client, "jarvis-keyword-b@test.com")
        _seed_message(sync_db, uid_a, content="nuclear launch codes on the desk")

        _switch(client, tok_b)
        data = _chat(client, "search my messages for nuclear").json()
        assert "no messages" in data["reply"].lower()


class TestMessageSummaries:
    def test_summarize_unread(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Ali", content="Submit the report", summary="Report submission reminder")
        _seed_message(sync_db, uid, sender="Bo", content="Lunch?", status="read")

        data = _chat(authed_client, "summarize my unread messages").json()
        assert data["action"]["type"] == "summarize_messages"
        assert data["action"]["detail"]["count"] == 1
        assert "1 unread" in data["reply"].lower()

    def test_summarize_unread_empty(self, authed_client, sync_db):
        data = _chat(authed_client, "summarize my unread messages").json()
        assert data["action"]["type"] == "summarize_messages"
        assert "no unread" in data["reply"].lower()


class TestImportantMessages:
    def test_show_important_messages(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Boss", subject="Review", priority="important")
        _seed_message(sync_db, uid, sender="VIP", subject="Now", priority="urgent")
        _seed_message(sync_db, uid, sender="Bo", subject="Chat", priority="normal")

        data = _chat(authed_client, "show my important messages").json()
        assert data["action"]["type"] == "get_data"
        assert data["action"]["detail"]["count"] == 1
        assert "boss" in data["reply"].lower()
        assert "vip" not in data["reply"].lower()
        assert "chat" not in data["reply"].lower()

    def test_important_messages_isolation(self, client, sync_db):
        uid_a, tok_a = _register(client, "jarvis-imp-a@test.com")
        uid_b, tok_b = _register(client, "jarvis-imp-b@test.com")
        _seed_message(sync_db, uid_a, sender="VIP", priority="urgent")

        _switch(client, tok_b)
        data = _chat(client, "show my important messages").json()
        assert data["action"]["detail"]["count"] == 0


class TestCompletedTaskList:
    def test_show_completed_tasks(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_task(sync_db, uid, "Done task", status="completed")
        _seed_task(sync_db, uid, "Pending task", status="pending")

        data = _chat(authed_client, "show my completed tasks").json()
        assert data["action"]["type"] == "get_data"
        assert data["action"]["detail"]["list"] == "completed_tasks"
        assert "1 completed task" in data["reply"].lower()
        assert "done task" in data["reply"].lower()
        assert "pending task" not in data["reply"].lower()

    def test_no_completed_tasks(self, authed_client):
        data = _chat(authed_client, "show my completed tasks").json()
        assert data["action"]["detail"]["count"] == 0


# ── Attention analysis ──────────────────────────────────────────────────────

class TestAttentionAnalysis:
    def test_attention_ranking(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Calm", content="Later", priority="normal")
        _seed_message(sync_db, uid, sender="Boss", content="Now", priority="urgent")
        _seed_message(sync_db, uid, sender="Team", content="Watch this", needs_attention=True)

        data = _chat(authed_client, "which messages should I handle first?").json()
        assert data["action"]["type"] == "analyze_attention"
        assert data["action"]["detail"]["count"] == 2
        assert "boss" in " ".join(data["reply"].lower().split())

    def test_explain_importance_uses_real_data(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(
            sync_db,
            uid,
            sender="Dean",
            content="Deadline moved to tomorrow",
            priority="urgent",
            explanation="Deadline is within 24 hours",
            summary="Deadline moved",
        )

        data = _chat(authed_client, "why is this message important?").json()
        assert data["action"]["type"] == "analyze_attention"
        assert "deadline is within 24 hours" in data["reply"].lower()
        assert "flagged as urgent" in data["reply"].lower()

    def test_explain_importance_nothing_flagged(self, authed_client):
        data = _chat(authed_client, "why is this message important?").json()
        assert "nothing is currently flagged" in data["reply"].lower()


# ── Reply drafting ──────────────────────────────────────────────────────────

class TestDraftReply:
    def test_draft_reply_to_sender_deterministic(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Ali", content="Please send the report ASAP", subject="Report")

        res = _chat(
            authed_client,
            "draft a reply to Ali saying I will send it tomorrow",
        )
        assert res.status_code == 200
        data = res.json()
        assert data["action"]["type"] == "draft_reply"
        assert data["action"]["detail"]["draft"]
        assert "i will send it tomorrow" in data["action"]["detail"]["draft"].lower()
        assert "draft" in data["reply"].lower()
        assert data["used_ai"] is False

    def test_draft_reply_to_latest_unread(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Bo", content="Are we on for Monday?")

        data = _chat(authed_client, "reply to this message").json()
        assert data["action"]["type"] == "draft_reply"
        assert "bo" in data["action"]["detail"]["sender"].lower()
        assert data["action"]["detail"]["draft"]

    def test_draft_reply_no_unread(self, authed_client):
        res = _chat(authed_client, "draft a reply to this message")
        assert res.status_code == 200
        data = res.json()
        assert data["action"] is None
        assert "no unread messages" in data["reply"].lower()

    def test_draft_reply_unknown_sender(self, authed_client, sync_db):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Known", content="hi")
        data = _chat(authed_client, "draft a reply to NobodyImportant").json()
        assert data["action"] is None
        assert "couldn't find" in data["reply"].lower()

    def test_draft_reply_groq_path(self, authed_client, sync_db, monkeypatch):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Ali", content="Send the report", subject="Report")
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.setattr(
            "services.ai.jarvis_actions._llm_configured", lambda: True
        )
        monkeypatch.setattr("services.ai.providers.groq.GroqProvider", _FakeGroqProvider)

        data = _chat(authed_client, "write a professional reply to Ali").json()
        assert data["used_ai"] is True
        assert data["action"]["type"] == "draft_reply"
        assert "professional draft" in data["action"]["detail"]["draft"].lower()

    def test_draft_reply_groq_failure_falls_back(self, authed_client, sync_db, monkeypatch):
        uid = _resolve_owner(authed_client)
        _seed_message(sync_db, uid, sender="Ali", content="Send the report", subject="Report")
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.setattr(
            "services.ai.jarvis_actions._llm_configured", lambda: True
        )

        class _BoomProvider:
            async def chat(self, prompt):
                raise RuntimeError("groq timeout")

        monkeypatch.setattr("services.ai.providers.groq.GroqProvider", _BoomProvider)

        data = _chat(authed_client, "draft a reply to Ali").json()
        assert data["used_ai"] is False
        assert data["action"]["type"] == "draft_reply"
        assert data["action"]["detail"]["draft"]


# ── Guards / regression ─────────────────────────────────────────────────────

class TestGuards:
    def test_unknown_chat_still_falls_back_gracefully(self, authed_client):
        data = _chat(authed_client, "tell me a joke about hamsters").json()
        assert data["action"] is None
        assert "conversational AI service is currently unavailable" in data["reply"]

    def test_empty_message_without_token_returns_400(self, authed_client):
        res = _chat(authed_client, "")
        assert res.status_code == 400
        assert "empty" in res.json()["detail"].lower()

    def test_requires_authentication(self, client):
        client.cookies.clear()
        res = _chat(client, "create a task called hack")
        assert res.status_code == 401


# ── Helpers ─────────────────────────────────────────────────────────────────

def _resolve_owner(client):
    """Return the current cookie-user's id (owner id from the session)."""
    token = client.cookies.get("cai_token")
    from services.security import decode_token

    return decode_token(token)


class _FakeGroqProvider:
    async def chat(self, prompt):
        return {"draft": "This is a professional draft for the recipient."}


# ── Pure unit checks (no DB, no HTTP) ───────────────────────────────────────

class TestDetectActionUnit:
    def test_detect_action_phrasing(self):
        from services.ai.jarvis_actions import detect_action

        assert detect_action("create a task to submit my FYP report tomorrow")["type"] == "create_task"
        assert detect_action("add a task called finish documentation")["type"] == "create_task"
        assert detect_action("complete my task call the vendor")["type"] == "complete_task"
        assert detect_action("mark my task x as completed")["type"] == "complete_task"
        assert detect_action("delete my task x")["type"] == "delete_task"
        assert detect_action("show my completed tasks")["type"] == "list_completed_tasks"
        assert detect_action("search my messages for meeting")["type"] == "search_messages"
        assert detect_action("find messages from Ali")["type"] == "search_messages"
        assert detect_action("summarize my unread messages")["type"] == "summarize_messages"
        assert detect_action("show my important messages")["type"] == "list_important_messages"
        assert detect_action("which messages should I handle first")["type"] == "analyze_attention"
        assert detect_action("why is this message important")["type"] == "explain_attention"
        assert detect_action("draft a reply to this message")["type"] == "draft_reply"

    def test_detect_action_leaves_phase1_alone(self):
        from services.ai.jarvis_actions import detect_action

        for phrase in (
            "open my inbox",
            "what needs my attention?",
            "what are my pending tasks?",
            "how many unread messages do I have?",
            "give me my dashboard summary",
            "hello jarvis",
            "help",
            "inbox",
            "show me attention",
        ):
            assert detect_action(phrase) is None, phrase