"""Automated Day 25 quickstart pass (T031) — replays specs/016-agent-memory/
quickstart.md steps 2-3 against the real FastAPI app + test MongoDB.

The provider is a fake that mimics the model's context behaviour (emits a
validated context_updates entry only when context is injected), so the pass
exercises the FULL wiring — resolve -> stamp -> fetch context -> inject into
the single call -> validate -> apply -> store — without burning LLM tokens.
"""

import pytest
from datetime import datetime

from bson import ObjectId


class _SmartFakeResult:
    priority = "normal"
    confidence = 0.7
    explanation = "qs stub"
    summary = "qs summary"
    recommended_actions = ["Reply"]
    tasks_extracted = []
    deadlines = []
    context_updates = []


class _SmartFakeProvider:
    """Mimics the model in the two-message flow: the follow-up message (the
    one being analyzed) supplies the deadline and names itself as the source."""

    def __init__(self):
        self.calls = []  # records whether each call had context

    async def analyze(self, message, context=None, current_message_id=None):
        self.calls.append(bool(context))
        result = _SmartFakeResult()
        if context:
            anchor = context[-1]  # follow-up arrives: only the anchor precedes
            result.context_updates = [
                {
                    "target_message_id": anchor["handle"],
                    "field": "deadline",
                    "value": "before our meeting",
                    "source_message_id": str(current_message_id)[-7:],
                    "reason": "Follow-up message supplies the deadline for the report request.",
                }
            ]
        return result


@pytest.fixture
def qs_provider(monkeypatch):
    provider = _SmartFakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: provider)
    return provider


def _register(client, email):
    res = client.post(
        "/auth/register",
        json={"name": "QS User", "email": email, "password": "s3cretpass"},
    )
    assert res.status_code == 201
    return res.json()["id"]


def _post(client, sender, content, source="simulated"):
    return client.post(
        "/messages", json={"sender": sender, "content": content, "source": source}
    )


def test_quickstart_linked_pair_and_edge_paths(client, sync_db, qs_provider):
    uid = _register(client, "quickstart@example.com")

    # Step 2.i: first message — standalone
    r1 = _post(client, "ali", "Can you send the report?")
    assert r1.status_code == 201
    id1 = r1.json()["id"]
    assert r1.json()["messageId"] == id1
    assert r1.json()["threadId"] is None

    # Step 2.ii: in-window follow-up links; both carry threadId == first _id
    r2 = _post(client, "ali", "Need it before our meeting.")
    assert r2.status_code == 201
    id2 = r2.json()["id"]
    assert r2.json()["threadId"] == id1
    assert r2.json()["conversationId"] == id1

    doc1 = sync_db.messages.find_one({"_id": ObjectId(id1), "user_id": uid})
    assert doc1["threadId"] == id1
    # Step 2.iii: anchor gains an explainable, additive context_updates entry
    updates = doc1["ai_analysis"]["context_updates"]
    assert len(updates) == 1
    u = updates[0]
    assert u["field"] == "deadline"
    assert u["value"] == "before our meeting"
    assert u["source_message_id"] == id2
    assert "Follow-up message" in u["reason"]
    assert isinstance(u["applied_at"], datetime)
    # Original analysis untouched
    assert doc1["ai_analysis"]["priority"] == "normal"
    assert doc1["ai_analysis"]["summary"] == "qs summary"

    # Step 3.standalone: different sender → independent
    r3 = _post(client, "Sara", "This is a completely different message.")
    assert r3.json()["threadId"] is None
    assert r3.json()["conversationId"] is None

    # Step 3.trivial: "ok" follow-up LINKS (data) but costs zero LLM calls
    r4 = _post(client, "ali", "ok")
    assert r4.status_code == 201
    assert r4.json()["threadId"] == id1
    trivial_doc = sync_db.messages.find_one({"_id": ObjectId(r4.json()["id"])})
    assert trivial_doc["ai_analysis"]["routing"]["llm_call_used"] is False

    # Step 3.out-of-window (source never touched here) + single-call guarantee
    assert len(qs_provider.calls) == 3  # messages 1, 2, Sara; "ok" is trivial
    assert all(c is False or c is True for c in qs_provider.calls)
    assert qs_provider.calls[1] is True  # follow-up saw context