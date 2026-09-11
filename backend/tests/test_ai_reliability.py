import os
from datetime import datetime, timezone

import pytest
from bson import ObjectId

TEST_SECRET = "test_app_secret"
os.environ["WHATSAPP_APP_SECRET"] = TEST_SECRET


async def _pending_analyze(content, message_id=None, user_id=None, thread_id=None):
    return {
        "priority": "normal",
        "confidence": 0.0,
        "explanation": "stubbed",
        "summary": "stubbed summary",
        "recommended_action": "",
        "recommended_actions": [],
        "tasks_extracted": [],
        "deadlines": [],
        "provider": "stub",
        "analyzed_at": None,
        "status": "pending",
    }


async def _raising_analyze(content, message_id=None, user_id=None, thread_id=None):
    raise RuntimeError("Simulated AI provider failure")


async def _completed_analyze(content, message_id=None, user_id=None, thread_id=None):
    return {
        "priority": "normal",
        "confidence": 0.8,
        "explanation": "stubbed",
        "summary": "stubbed summary after retry",
        "recommended_action": "",
        "recommended_actions": [],
        "tasks_extracted": [],
        "deadlines": [],
        "provider": "stub",
        "analyzed_at": datetime.now(timezone.utc),
        "status": "completed",
    }


def _simulate_post(client, sender="Alice", message="Test reliability message"):
    return client.post(
        "/webhooks/simulate", json={"sender": sender, "message": message}
    )


def _register(client, email):
    res = client.post(
        "/auth/register",
        json={"name": "AI User", "email": email, "password": "s3cretpass"},
    )
    assert res.status_code == 201
    return res.json()["id"]


def _insert_pending_message(sync_db, user_id, content="Pending message"):
    """Insert a message directly with ai_analysis.status = "pending"."""
    now = datetime.now(timezone.utc)
    doc = {
        "_id": ObjectId(),
        "user_id": user_id,
        "source": "simulate",
        "sender": "Pending Sender",
        "content": content,
        "message_type": "text",
        "status": "unread",
        "state": "active",
        "created_at": now,
        "updated_at": now,
        "received_at": now,
        "ai_analysis": {
            "priority": "normal",
            "confidence": 0.0,
            "explanation": "stubbed",
            "summary": "stubbed summary",
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "provider": "stub",
            "analyzed_at": None,
            "status": "pending",
        },
    }
    sync_db.messages.insert_one(doc)
    return str(doc["_id"])


class TestAIReliability:
    # ── T013: AI failure → message stored with pending ─────────────────────

    def test_message_stored_with_pending_on_ai_failure(
        self, client, sync_db, monkeypatch
    ):
        monkeypatch.setattr("services.webhook_ingest.process_message", _pending_analyze)

        uid = _register(client, "ai-fail@test.com")
        res = _simulate_post(client)
        assert res.status_code == 200

        doc = sync_db.messages.find_one({"user_id": uid, "source": "simulate"})
        assert doc is not None
        assert doc["ai_analysis"]["status"] == "pending"
        assert doc["content"] == "Test reliability message"

    # ── T014: AI raises → ingest does not crash ────────────────────────────

    def test_ai_failure_never_crashes_ingest(self, client, sync_db, monkeypatch):
        monkeypatch.setattr("services.webhook_ingest.process_message", _raising_analyze)

        uid = _register(client, "ai-crash@test.com")
        res = _simulate_post(client)
        assert res.status_code == 200

        doc = sync_db.messages.find_one({"user_id": uid, "source": "simulate"})
        assert doc is not None
        assert doc["content"] == "Test reliability message"

    # ── T015: Pending message is visible in listing ────────────────────────

    def test_pending_message_visible_in_listing(self, client, sync_db):
        uid = _register(client, "ai-visible@test.com")
        msg_id = _insert_pending_message(sync_db, uid)

        res = client.get("/messages")
        assert res.status_code == 200
        messages = res.json()["messages"]
        assert len(messages) == 1
        assert messages[0]["content"] == "Pending message"
        assert messages[0]["id"] == msg_id

    # ── T016: retry_pending completes in place (RED until T019) ─────────────
    # NOTE: retry_pending_analyses runs on the TestClient loop via
    # client.portal.call() (motor is bound to that loop) — never asyncio.run.

    def test_retry_pending_completes_in_place(self, client, sync_db, monkeypatch):
        from services.retry_pending import retry_pending_analyses

        monkeypatch.setattr(
            "services.retry_pending.process_message", _completed_analyze
        )

        uid = _register(client, "ai-retry@test.com")
        msg_id = _insert_pending_message(sync_db, uid)

        original_id = ObjectId(msg_id)
        before = sync_db.messages.find_one({"_id": original_id})
        assert before["ai_analysis"]["status"] == "pending"

        retried = client.portal.call(retry_pending_analyses)
        assert retried >= 1

        doc_after = sync_db.messages.find_one({"_id": original_id})
        assert doc_after is not None
        assert doc_after["ai_analysis"]["status"] == "completed"
        assert sync_db.messages.count_documents({"user_id": uid}) == 1

    # ── T017: retry is idempotent (RED until T019) ─────────────────────────

    def test_retry_pending_idempotent(self, client, sync_db, monkeypatch):
        from services.retry_pending import retry_pending_analyses

        monkeypatch.setattr(
            "services.retry_pending.process_message", _completed_analyze
        )

        uid = _register(client, "ai-idem@test.com")
        msg_id = _insert_pending_message(sync_db, uid)

        original_id = ObjectId(msg_id)

        client.portal.call(retry_pending_analyses)
        client.portal.call(retry_pending_analyses)

        doc_after = sync_db.messages.find_one({"_id": original_id})
        assert doc_after["ai_analysis"]["status"] == "completed"
        assert sync_db.messages.count_documents({"user_id": uid}) == 1
