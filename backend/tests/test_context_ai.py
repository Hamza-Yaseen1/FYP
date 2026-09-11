"""Context fetch/injection + single-call + enrichment tests (Day 25 US1 -
tasks T009 + T010).

Provider interaction is mocked; the collection is an in-memory fake - never
motor under asyncio.run (see test_orchestrator.py for the same convention).
"""

import asyncio
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from services.ai.context import (
    apply_context_updates,
    build_context_block,
    fetch_thread_context,
    validate_context_updates,
)
from services.ai.orchestrate import process_message
from services.ai.providers.base import AIAnalysisResult
from test_threads import _FakeMessages, _doc

T0 = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)

MARKER = "CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION"


# ── T009: context fetch + injection ─────────────────────────────────────


def test_fetch_thread_context_at_most_5_excluding_self(monkeypatch):
    thread_id = str(ObjectId())
    docs = [
        _doc(
            user_id="u1",
            threadId=thread_id,
            received_at=T0 + timedelta(minutes=i),
            content=f"msg-{i}",
        )
        for i in range(7)
    ]
    other_thread = _doc(
        user_id="u1",
        threadId=str(ObjectId()),
        received_at=T0 + timedelta(minutes=99),
        content="other-thread",
    )
    other_user = _doc(
        user_id="u2",
        threadId=thread_id,
        received_at=T0 + timedelta(minutes=50),
        content="other-user",
    )
    exclude_id = str(docs[6]["_id"])

    fake = _FakeMessages([*docs, other_thread, other_user])
    monkeypatch.setattr("services.ai.context.messages_collection", fake)

    result = asyncio.run(
        fetch_thread_context("u1", thread_id, exclude_message_id=exclude_id)
    )

    assert len(result) == 5
    ids = {str(d["_id"]) for d in result}
    assert all(d["threadId"] == thread_id for d in result)
    assert all(d["user_id"] == "u1" for d in result)
    assert exclude_id not in ids
    assert str(docs[0]["_id"]) not in ids
    assert "other-thread" not in ids
    assert "other-user" not in ids
    times = [d["received_at"] for d in result]
    assert times == sorted(times, reverse=True)
    assert all(d["handle"] == str(d["_id"])[-7:] for d in result)


def test_build_context_block_empty_is_none():
    assert build_context_block([]) is None
    assert build_context_block(None) is None


def test_build_context_block_renders_lines_and_is_brace_safe():
    msgs = [
        {
            "handle": "abc1234",
            "sender": "ali",
            "content": "Can you send {the report}?",
            "received_at": T0,
        }
    ]
    block = build_context_block(msgs)
    assert block is not None
    assert "[abc1234]" in block
    assert "ali" in block
    assert "{the report}" in block


def test_provider_prompt_shows_context_only_when_passed(monkeypatch):
    import services.ai.providers.groq as groq_module

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    captured = {}

    async def fake_complete(prompt):
        captured["prompt"] = prompt
        return {
            "priority": "normal",
            "confidence": 0.5,
            "explanation": None,
            "summary": None,
            "tasks_extracted": [],
            "deadlines": [],
            "recommended_action": "",
        }

    provider = groq_module.GroqProvider()
    monkeypatch.setattr(provider, "_complete", fake_complete)

    asyncio.run(provider.analyze("hello world"))
    assert MARKER not in captured["prompt"]

    ctx = [
        {
            "handle": "abc1234",
            "sender": "ali",
            "content": "Can you send the report?",
            "received_at": T0,
        }
    ]
    asyncio.run(provider.analyze("Need it before our meeting.", context=ctx))
    assert MARKER in captured["prompt"]


def test_provider_prompt_no_context_marker_when_empty_list(monkeypatch):
    import services.ai.providers.groq as groq_module

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    captured = {}

    async def fake_complete(prompt):
        captured["prompt"] = prompt
        return {
            "priority": "normal",
            "confidence": 0.5,
            "explanation": None,
            "summary": None,
            "tasks_extracted": [],
            "deadlines": [],
            "recommended_action": "",
        }

    provider = groq_module.GroqProvider()
    monkeypatch.setattr(provider, "_complete", fake_complete)

    asyncio.run(provider.analyze("hello world", context=[]))
    assert MARKER not in captured["prompt"]


def test_provider_prompt_without_context_byte_identical_to_day24(monkeypatch):
    """US3/SC-005: standalone prompt is byte-identical to Day 24's prompt."""
    import services.ai.providers.groq as groq_module

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    captured = {}

    async def fake_complete(prompt):
        captured["prompt"] = prompt
        return {
            "priority": "normal",
            "confidence": 0.5,
            "explanation": None,
            "summary": None,
            "tasks_extracted": [],
            "deadlines": [],
            "recommended_action": "",
        }

    provider = groq_module.GroqProvider()
    monkeypatch.setattr(provider, "_complete", fake_complete)

    content = "Can you send the report?"
    asyncio.run(provider.analyze(content))

    expected = groq_module.ANALYSIS_PROMPT.replace("{message}", content)
    assert captured["prompt"] == expected
    assert MARKER not in captured["prompt"]


# ── T010: single-call + validated anchor enrichment ─────────────────────


class _CountingProvider:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    async def analyze(self, message, context=None, current_message_id=None):
        assert context is None or len(context) > 0
        self.calls += 1
        return self.result


def test_single_ai_call_and_anchor_enrichment(monkeypatch):
    a = _doc(
        user_id="u1",
        sender="ali",
        content="Can you send the report?",
        received_at=T0,
    )
    c = _doc(
        user_id="u1",
        sender="ali",
        content="It's needed before our meeting.",
        received_at=T0 + timedelta(minutes=5),
    )
    thread_id = str(a["_id"])
    a["threadId"] = thread_id
    a["conversationId"] = thread_id
    c["threadId"] = thread_id
    c["conversationId"] = thread_id

    fake = _FakeMessages([a, c])
    monkeypatch.setattr("services.ai.context.messages_collection", fake)

    result = AIAnalysisResult(
        priority="urgent",
        confidence=0.9,
        explanation="Follow-up supplies the deadline.",
        summary="Report needed before the meeting.",
        recommended_actions=["Send the report"],
        tasks_extracted=[],
        deadlines=["before our meeting"],
        context_updates=[
            {
                "target_message_id": str(a["_id"])[-7:],
                "field": "deadline",
                "value": "before our meeting",
                "source_message_id": str(c["_id"])[-7:],
                "reason": "Follow-up message supplies the deadline for the report request.",
            }
        ],
    )
    provider = _CountingProvider(result)
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: provider)

    analyzed = asyncio.run(
        process_message(
            "Need it before our meeting.",
            message_id=str(ObjectId()),
            user_id="u1",
            thread_id=thread_id,
        )
    )

    assert provider.calls == 1
    assert analyzed["routing"]["llm_call_used"] is True
    assert "context_updates" not in analyzed

    anchor_doc = next(d for d in fake.docs if d["_id"] == a["_id"])
    updates = (anchor_doc.get("ai_analysis") or {}).get("context_updates", [])
    assert len(updates) == 1
    u = updates[0]
    assert u["field"] == "deadline"
    assert u["value"] == "before our meeting"
    assert u["source_message_id"] == str(c["_id"])
    assert u["reason"] == "Follow-up message supplies the deadline for the report request."
    assert isinstance(u["applied_at"], datetime)


# ── T023-T025: US4 validation, scoping, explainability ─────────────────────


def _thread_pair():
    a = _doc(
        user_id="u1",
        sender="ali",
        content="Can you send the report?",
        received_at=T0,
    )
    c = _doc(
        user_id="u1",
        sender="ali",
        content="It's needed before our meeting.",
        received_at=T0 + timedelta(minutes=5),
    )
    a["handle"] = str(a["_id"])[-7:]
    c["handle"] = str(c["_id"])[-7:]
    return a, c


def test_validate_drops_each_invalid_candidate(monkeypatch):
    a, c = _thread_pair()
    thread = [a, c]
    current = str(c["_id"])  # target == this message => self-target

    base = {
        "target_message_id": a["handle"],
        "field": "deadline",
        "value": "before our meeting",
        "source_message_id": c["handle"],
        "reason": "x",
    }

    cases = [
        ("unknown target", {**base, "target_message_id": "zzzzzzz"}),
        ("self target", {**base, "target_message_id": c["handle"]}),
        ("disallowed field", {**base, "field": "reply_to"}),
        ("value not verbatim", {**base, "value": "before our meeting!!"}),
        ("empty value", {**base, "value": ""}),
        ("unknown source", {**base, "source_message_id": "zzzzzzz"}),
        ("non-object candidate", "not-a-dict"),
    ]
    for label, candidate in cases:
        valid = validate_context_updates([candidate], thread, current)
        assert valid == [], f"{label}: expected drop, got {valid}"

    fake = _FakeMessages([a, c])
    monkeypatch.setattr("services.ai.context.messages_collection", fake)
    applied = asyncio.run(apply_context_updates([], current, "u1"))
    assert applied == 0
    assert (a.get("ai_analysis") or {}).get("context_updates") is None


def test_apply_scoped_to_other_users_never_touches(monkeypatch):
    a, _ = _thread_pair()
    valid = [
        {
            "target_message_id": str(a["_id"]),
            "field": "deadline",
            "value": "before our meeting",
            "source_message_id": str(a["_id"]),
            "reason": "r",
        }
    ]
    fake = _FakeMessages([a])
    monkeypatch.setattr("services.ai.context.messages_collection", fake)
    applied = asyncio.run(apply_context_updates(valid, str(a["_id"]), "u2"))
    assert applied == 0
    assert (a.get("ai_analysis") or {}).get("context_updates") is None


def test_fetch_thread_context_never_crosses_users(monkeypatch):
    thread_id = str(ObjectId())
    a_msg = _doc(user_id="u1", threadId=thread_id, received_at=T0)
    b_msg = _doc(user_id="u2", threadId=thread_id, received_at=T0 + timedelta(minutes=1))
    fake = _FakeMessages([a_msg, b_msg])
    monkeypatch.setattr("services.ai.context.messages_collection", fake)

    result = asyncio.run(fetch_thread_context("u1", thread_id))
    assert len(result) == 1
    assert all(d["user_id"] == "u1" for d in result)
    assert str(result[0]["_id"]) == str(a_msg["_id"])


def test_applied_update_is_additive_and_reason_named(monkeypatch):
    a, c = _thread_pair()
    original = {
        "priority": "normal",
        "deadlines": [],
        "tasks_extracted": [],
        "summary": "original summary",
    }
    a["ai_analysis"] = dict(original)

    valid = [
        {
            "target_message_id": str(a["_id"]),
            "field": "deadline",
            "value": "before our meeting",
            "source_message_id": str(c["_id"]),
            "reason": "Follow-up supplies the deadline for the report request.",
        }
    ]
    fake = _FakeMessages([a, c])
    monkeypatch.setattr("services.ai.context.messages_collection", fake)

    applied = asyncio.run(apply_context_updates(valid, str(c["_id"]), "u1"))
    assert applied == 1

    stored = a["ai_analysis"]
    for key, value in original.items():
        assert stored[key] == value, f"original {key} was rewritten"
    updates = stored["context_updates"]
    assert len(updates) == 1
    u = updates[0]
    assert u["field"] == "deadline"
    assert u["value"] == "before our meeting"
    assert u["source_message_id"] == str(c["_id"])
    assert u["reason"] == "Follow-up supplies the deadline for the report request."
    assert isinstance(u["applied_at"], datetime)


# ── T028: US5 isolated enrichment ──────────────────────────────────────────


def test_candidate_targeting_other_users_message_dropped():
    a, c = _thread_pair()
    other_user = _doc(
        user_id="u2",
        sender="ali",
        content="It's needed before our meeting.",
        received_at=T0 + timedelta(minutes=5),
    )
    other_user["handle"] = str(other_user["_id"])[-7:]

    thread_for_u1 = [a]  # u1's fetch never contains u2's message
    current = str(ObjectId())
    candidate = {
        "target_message_id": other_user["handle"],
        "field": "deadline",
        "value": "It's needed before our meeting.",
        "source_message_id": other_user["handle"],
        "reason": "r",
    }
    assert validate_context_updates([candidate], thread_for_u1, current) == []


def test_current_message_can_be_the_source_and_is_explainable():
    """The two-message flow: the follow-up being analyzed ('Need it before
    our meeting.') enriches the anchor, naming ITSELF as the provable
    source. The value must be verbatim in its own content."""
    a, _ = _thread_pair()
    current_id = str(ObjectId())
    current_content = "Need it before our meeting."

    candidate = {
        "target_message_id": a["handle"],
        "field": "deadline",
        "value": "before our meeting",
        "source_message_id": current_id[-7:],
        "reason": "Follow-up message supplies the deadline for the report request.",
    }
    valid = validate_context_updates(
        [candidate], [a], current_id, current_content=current_content
    )
    assert len(valid) == 1
    assert valid[0]["target_message_id"] == str(a["_id"])
    assert valid[0]["source_message_id"] == current_id

    forged = {
        **candidate,
        "source_message_id": current_id[-7:],
        "value": "before the meeting at midnight",  # not in current content
    }
    assert validate_context_updates(
        [forged], [a], current_id, current_content=current_content
    ) == []


class _RaisingProviderLinked:
    async def analyze(self, message, context=None, current_message_id=None):
        raise RuntimeError("Groq rate limit / daily token cap hit")


def test_linked_provider_failure_is_pending_and_link_intact(monkeypatch):
    """FR-012: a provider failure on a linked message degrades to the pending
    fallback; the link context is consumed without blocking, and the returned
    record carries routing with llm_call_used=True."""
    a, _ = _thread_pair()
    thread_id = str(a["_id"])
    a["threadId"] = thread_id
    a["conversationId"] = thread_id

    fake = _FakeMessages([a])
    monkeypatch.setattr("services.ai.context.messages_collection", fake)
    monkeypatch.setattr(
        "services.ai.analyzer.get_provider", lambda: _RaisingProviderLinked()
    )

    analyzed = asyncio.run(
        process_message(
            "Need it before our meeting.",
            message_id=str(ObjectId()),
            user_id="u1",
            thread_id=thread_id,
        )
    )
    assert analyzed["status"] == "pending"
    assert analyzed["routing"]["llm_call_used"] is True
    assert "context_updates" not in analyzed