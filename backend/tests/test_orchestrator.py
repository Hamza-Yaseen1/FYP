"""US1 AI Orchestrator tests: routing decisions + output gating (Day 24).

Coverage per tasks.md T004-T006:
- T004 decision-table unit tests for ``decide_routing``
- T005 >= 90% routing accuracy on a labeled 50-message set (SC-002)
- T006 ``_gate_outputs`` + task-persistence gating through ``analyze_message``
"""

import asyncio

import pytest

from services.ai.analyzer import _gate_outputs, analyze_message
from services.ai.orchestrate import process_message
from services.ai.routing import AGENT_IDS, RoutingDecision, decide_routing

# Compact signatures: (needs_analysis, needs_llm, run_summary,
# run_task_extraction, run_deadline_detection, run_recommended_action)
TRIVIAL = (True, False, True, False, False, False)
TASK = (True, True, True, True, False, True)
DEADLINE = (True, True, True, False, True, False)
FULL = (True, True, True, True, True, True)
FYI = (True, True, True, False, False, False)
EMPTY = (False, False, False, False, False, False)


def _signature(decision: RoutingDecision) -> tuple:
    return (
        decision.needs_analysis,
        decision.needs_llm,
        decision.run_summary,
        decision.run_task_extraction,
        decision.run_deadline_detection,
        decision.run_recommended_action,
    )


DECISION_TABLE = [
    pytest.param("ok", "text", TRIVIAL, id="trivial-ok"),
    pytest.param("hi", "text", TRIVIAL, id="trivial-hi"),
    pytest.param("thanks", "text", TRIVIAL, id="trivial-thanks"),
    pytest.param("Sounds good", "text", TRIVIAL, id="trivial-case-insensitive"),
    pytest.param("ok!", "text", TRIVIAL, id="trivial-punctuation-stripped"),
    pytest.param("Please call me", "text", TASK, id="task-no-deadline"),
    pytest.param("Send me the slides", "text", TASK, id="task-send"),
    pytest.param("Please review my report", "text", TASK, id="task-review"),
    pytest.param("The meeting is tomorrow", "text", DEADLINE, id="deadline-no-task"),
    pytest.param("Talk to you tonight", "text", DEADLINE, id="deadline-tonight"),
    pytest.param("Send me the slides tonight", "text", FULL, id="task-and-deadline"),
    pytest.param("Please call me tomorrow", "text", FULL, id="task-and-tomorrow"),
    pytest.param("The event is by Friday", "text", DEADLINE, id="deadline-by-friday"),
    pytest.param(
        "Just wanted to share that everything went well",
        "text",
        FYI,
        id="long-fyi-no-triggers",
    ),
    pytest.param("أرسل الملفات", "text", FULL, id="arabic-full-default"),
    pytest.param("", "text", EMPTY, id="empty"),
    pytest.param("   ", "text", EMPTY, id="whitespace-only"),
    pytest.param("hi there", "media", EMPTY, id="media-only"),
]


@pytest.mark.parametrize("content,message_type,expected", DECISION_TABLE)
def test_decide_routing_decision_table(content, message_type, expected):
    decision = decide_routing(content, message_type)
    assert _signature(decision) == expected


LABELED_MESSAGES = [
    # trivial (14)
    ("ok", "text", "trivial"),
    ("hi", "text", "trivial"),
    ("hey", "text", "trivial"),
    ("thanks", "text", "trivial"),
    ("thank you", "text", "trivial"),
    ("sounds good", "text", "trivial"),
    ("yes", "text", "trivial"),
    ("no", "text", "trivial"),
    ("okay", "text", "trivial"),
    ("yep", "text", "trivial"),
    ("sure", "text", "trivial"),
    ("got it", "text", "trivial"),
    ("mm-hmm", "text", "trivial"),
    ("hello!", "text", "trivial"),
    # task without deadline (8)
    ("Send me the slides", "text", "task"),
    ("Please call me", "text", "task"),
    ("Please review my report", "text", "task"),
    ("Submit the assignment", "text", "task"),
    ("Confirm the booking", "text", "task"),
    ("Draft a reply to Ali", "text", "task"),
    ("Fix the printer", "text", "task"),
    ("Prepare the agenda", "text", "task"),
    # deadline without task (6)
    ("The meeting is tomorrow", "text", "deadline"),
    ("Talk to you tonight", "text", "deadline"),
    ("The deadline is asap", "text", "deadline"),
    ("See you today", "text", "deadline"),
    ("Next week is the holiday", "text", "deadline"),
    ("The event is by Friday", "text", "deadline"),
    # task + deadline -> full (8)
    ("Send me the slides tonight", "text", "full"),
    ("Please call me tomorrow", "text", "full"),
    ("Review the report by Friday", "text", "full"),
    ("Submit it today", "text", "full"),
    ("Confirm the booking asap", "text", "full"),
    ("Prepare the agenda for next week", "text", "full"),
    ("Send the invoice right now", "text", "full"),
    ("Send the files by Monday", "text", "full"),
    # long FYI with no action signals (6)
    (
        "Just wanted to share that everything went well and I hope the weekend "
        "treats you kindly, best wishes",
        "text",
        "fyi",
    ),
    (
        "I think the design is looking good, thanks for all the effort on this one",
        "text",
        "fyi",
    ),
    (
        "Here is a quick note: the weather was great and we had a wonderful time",
        "text",
        "fyi",
    ),
    ("Nothing urgent, just letting you know the plan is on track", "text", "fyi"),
    ("Hope all is well and look forward to seeing everyone at the event", "text", "fyi"),
    ("The report looks complete and we can discuss it whenever", "text", "fyi"),
    # non-Latin / Arabic (5) - always full default
    ("أرسل الملفات", "text", "arabic"),
    ("يرجى مراجعة التقرير", "text", "arabic"),
    ("الاجتماع غدا", "text", "arabic"),
    ("أرسل لي العرض الليلة", "text", "arabic"),
    ("شكرا", "text", "arabic"),
    # no analyzable content (3)
    ("", "text", "empty"),
    ("   ", "text", "empty"),
    ("", "media", "empty"),
]

CATEGORY_SIGNATURE = {
    "trivial": TRIVIAL,
    "task": TASK,
    "deadline": DEADLINE,
    "full": FULL,
    "fyi": FYI,
    "arabic": FULL,
    "empty": EMPTY,
}


def test_routing_accuracy_labeled_set():
    assert len(LABELED_MESSAGES) == 50
    matches = 0
    for content, message_type, label in LABELED_MESSAGES:
        actual = _signature(decide_routing(content, message_type))
        if actual == CATEGORY_SIGNATURE[label]:
            matches += 1
    assert matches / len(LABELED_MESSAGES) >= 0.90


class _FakeResult:
    priority = "important"
    confidence = 0.7
    explanation = "test explanation"
    summary = "test summary"
    recommended_actions = ["Follow up with Ali"]
    tasks_extracted = [
        {"description": "Do a thing", "deadline": "tomorrow", "priority_indicator": None, "requires_action": True}
    ]
    deadlines = ["tomorrow"]


class _FakeProvider:
    def __init__(self):
        self.calls = 0

    async def analyze(self, message, context=None):
        self.calls += 1
        return _FakeResult()


class _RecordingTasksCollection:
    """Async stand-in for the motor tasks collection.

    The orchestrator tests run under asyncio.run, but the real motor client
    binds to the TestClient's event loop; awaiting it from a throwaway
    asyncio.run loop raises "Future attached to a different loop". Recording
    the inserts keeps these tests loop-agnostic while still asserting what
    matters (the write happens exactly as selected).
    """

    def __init__(self):
        self.inserted = []

    async def insert_many(self, docs):
        self.inserted.extend(docs)


def _decision(
    needs_analysis=True,
    needs_llm=True,
    run_summary=True,
    run_task_extraction=True,
    run_deadline_detection=True,
    run_recommended_action=True,
):
    return RoutingDecision(
        needs_analysis=needs_analysis,
        needs_llm=needs_llm,
        run_summary=run_summary,
        run_task_extraction=run_task_extraction,
        run_deadline_detection=run_deadline_detection,
        run_recommended_action=run_recommended_action,
        reason="test",
        triggers=[],
    )


def test_gate_outputs_zeros_skipped_agents():
    analysis = {
        "summary": "test summary",
        "tasks_extracted": [{"description": "Do a thing"}],
        "deadlines": ["tomorrow"],
        "recommended_action": "Follow up",
        "recommended_actions": ["Follow up"],
    }
    routing = _decision(run_task_extraction=False, run_deadline_detection=False, run_recommended_action=False)

    gated = _gate_outputs(analysis, routing)

    assert gated["tasks_extracted"] == []
    assert gated["deadlines"] == []
    assert gated["recommended_action"] == ""
    assert gated["recommended_actions"] == []
    assert gated["summary"] == "test summary"


def test_gate_outputs_keeps_selected_agents():
    analysis = {
        "summary": "test summary",
        "tasks_extracted": [{"description": "Do a thing"}],
        "deadlines": ["tomorrow"],
        "recommended_action": "Follow up",
        "recommended_actions": ["Follow up"],
    }
    routing = _decision(run_summary=False)

    gated = _gate_outputs(analysis, routing)

    assert gated["tasks_extracted"] == [{"description": "Do a thing"}]
    assert gated["deadlines"] == ["tomorrow"]
    assert gated["recommended_action"] == "Follow up"
    assert gated["summary"] is None


def test_analyze_message_gates_outputs_and_attention(monkeypatch, sync_db):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)
    routing = _decision(run_task_extraction=False, run_deadline_detection=False, run_recommended_action=False)

    result = asyncio.run(
        analyze_message("Send me the slides", message_id="msg-gated", user_id="user-test", run_tasks=False, routing=routing)
    )

    assert fake.calls == 1
    assert result["tasks_extracted"] == []
    assert result["deadlines"] == []
    assert result["recommended_action"] == ""
    assert result["recommended_actions"] == []
    assert result["summary"] == "test summary"
    assert result["needs_attention"] is False
    assert result["attention_reason"] == ""
    assert sync_db["tasks"].count_documents({}) == 0


def test_analyze_message_no_task_persistence_when_skipped(monkeypatch, sync_db):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)
    routing = _decision(run_task_extraction=False)

    asyncio.run(
        analyze_message("Send me the slides", message_id="msg-skip", user_id="user-test", run_tasks=False, routing=routing)
    )

    assert sync_db["tasks"].count_documents({}) == 0


def test_analyze_message_persists_tasks_when_selected(client, sync_db, monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)

    client.post(
        "/auth/register",
        json={"name": "Persist User", "email": "persist@example.com", "password": "s3cretpass"},
    )
    res = client.post(
        "/messages",
        json={"sender": "Ali", "content": "Send me the slides tonight", "source": "simulated"},
    )
    assert res.status_code == 201

    assert sync_db["tasks"].count_documents({}) == 1


def test_process_message_single_provider_call(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)
    monkeypatch.setattr(
        "services.ai.analyzer.tasks_collection", _RecordingTasksCollection()
    )

    result = asyncio.run(
        process_message("Send me the slides tonight", message_id="msg-orch", user_id="user-test")
    )

    assert fake.calls == 1
    assert result["routing"]["llm_call_used"] is True
    assert result["routing"]["agents_run"] == AGENT_IDS
    assert result["routing"]["skip_reason"] == "full"


def test_process_message_records_agents_run_and_skipped(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)

    result = asyncio.run(
        process_message("The meeting is tomorrow", message_id="msg-dead", user_id="user-test")
    )

    assert fake.calls == 1
    assert result["routing"]["agents_run"] == ["priority", "summary", "deadline_detection"]
    assert result["routing"]["agents_skipped"] == ["task_extraction", "recommended_action"]
    assert result["routing"]["skip_reason"] == "deadline"


def test_process_message_no_llm_for_empty_content(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)

    result = asyncio.run(
        process_message("   ", message_id="msg-empty", user_id="user-test")
    )

    assert fake.calls == 0
    assert result["routing"]["llm_call_used"] is False
    assert result["routing"]["skip_reason"] == "no analyzable content"


def test_trivial_message_zero_ai_calls(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)

    for content in ("ok", "hi", "thanks"):
        result = asyncio.run(
            process_message(content, message_id=None, user_id="user-test")
        )

        assert fake.calls == 0
        assert result["routing"]["llm_call_used"] is False
        assert result["routing"]["skip_reason"] == "trivial"
        assert result["priority"] == "normal"
        assert result["tasks_extracted"] == []
        assert result["deadlines"] == []
        assert result["status"] == "completed"
        assert result["provider"] == "rule-based"


def test_no_content_skipped_stub(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)

    cases = [("", "text"), ("   ", "text"), ("", "media")]
    for content, message_type in cases:
        result = asyncio.run(
            process_message(
                content, message_id=None, user_id="user-test", message_type=message_type
            )
        )

        assert fake.calls == 0
        assert result["status"] == "skipped"
        assert result["priority"] == "normal"
        assert result["routing"]["skip_reason"] == "no analyzable content"
        assert result["routing"]["llm_call_used"] is False
        assert result["routing"]["agents_run"] == []
        assert result["routing"]["agents_skipped"] == []


def test_routing_record_complete(monkeypatch):
    fake = _FakeProvider()
    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: fake)
    monkeypatch.setattr(
        "services.ai.analyzer.tasks_collection", _RecordingTasksCollection()
    )

    analyzed = asyncio.run(
        process_message("Send me the slides tonight", message_id="msg-routing", user_id="user-test")
    )
    routing = analyzed["routing"]
    assert set(routing["agents_run"]) | set(routing["agents_skipped"]) == set(AGENT_IDS)
    assert "priority" in routing["agents_run"]
    assert routing["skip_reason"] == "full"
    assert routing["triggers"]
    assert routing["decided_at"] is not None

    for content, message_type, reason in (
        ("ok", "text", "trivial"),
        ("   ", "text", "no analyzable content"),
    ):
        result = asyncio.run(
            process_message(content, message_id=None, user_id="user-test", message_type=message_type)
        )
        record = result["routing"]
        assert record["skip_reason"] == reason
        assert record["llm_call_used"] is False
        for key in (
            "agents_run",
            "agents_skipped",
            "skip_reason",
            "triggers",
            "llm_call_used",
            "decided_at",
        ):
            assert key in record


class _RaisingProvider:
    async def analyze(self, message, context=None):
        raise RuntimeError("Groq rate limit / daily token cap hit")


def test_failure_distinct_from_skip(monkeypatch):
    monkeypatch.setattr(
        "services.ai.analyzer.get_provider", lambda: _RaisingProvider()
    )

    failed = asyncio.run(
        process_message("Send me the slides tonight", message_id="msg-fail", user_id="user-test")
    )
    assert failed["status"] == "pending"
    assert failed["routing"]["llm_call_used"] is True
    assert failed["routing"]["skip_reason"] == "full"
    assert "priority" in failed["routing"]["agents_run"]

    trivial = asyncio.run(process_message("ok", message_id=None, user_id="user-test"))
    assert trivial["status"] == "completed"
    assert trivial["routing"]["llm_call_used"] is False

    assert (failed["status"], failed["routing"]["llm_call_used"]) != (
        trivial["status"],
        trivial["routing"]["llm_call_used"],
    )


def test_get_provider_failure_still_attaches_routing(monkeypatch):
    def _no_provider():
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("services.ai.analyzer.get_provider", _no_provider)

    failed = asyncio.run(
        process_message("Send me the slides tonight", message_id="msg-noprov", user_id="user-test")
    )
    assert failed["status"] == "pending"
    assert failed["routing"]["llm_call_used"] is True
    assert failed["routing"]["skip_reason"] == "full"
def test_provider_uses_reasoning_effort_none(monkeypatch):
    """The Groq call MUST disable reasoning: Qwen 3.6 27B burns its output
    budget on a thinking block otherwise, which trips the OTPM 429 guard and
    degrades every analysis to the pending fallback (Normal 0% + Review)."""
    import types

    import services.ai.providers.groq as groq_mod

    recorded: dict = {}

    choices = [
        types.SimpleNamespace(
            message=types.SimpleNamespace(
                content='{"priority": "urgent", "confidence": 0.9, "explanation": "fast"}'
            )
        )
    ]

    class _FakeCompletions:
        async def create(self, **kwargs):
            recorded["kwargs"] = kwargs
            return types.SimpleNamespace(choices=choices)

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        def __init__(self, api_key=None):
            self.chat = _FakeChat

    monkeypatch.setattr(groq_mod, "AsyncGroq", _FakeClient)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    provider = groq_mod.GroqProvider()
    result = asyncio.run(provider._complete("hello"))

    assert recorded["kwargs"]["reasoning_effort"] == "none"
    assert recorded["kwargs"]["response_format"] == {"type": "json_object"}
    assert result["priority"] == "urgent"

def test_task_storage_failure_keeps_analysis_completed(monkeypatch):
    """A tasks_db hiccup must never demote a successful analysis to pending."""
    from services.ai.analyzer import analyze_message
    from services.ai.routing import RoutingDecision

    class _BoomTasks:
        async def insert_many(self, docs):
            raise RuntimeError("tasks db unreachable")

    monkeypatch.setattr("services.ai.analyzer.tasks_collection", _BoomTasks())

    class _FakeResult:
        priority = "urgent"
        confidence = 0.91
        explanation = "server down today"
        summary = "production server is down"
        recommended_actions = ["Fix the server today"]
        deadlines = ["today"]
        context_updates = []
        tasks_extracted = [
            {
                "description": "Fix the server",
                "deadline": "today",
                "priority_indicator": "urgent",
                "requires_action": True,
            }
        ]

    class _FakeProvider:
        async def analyze(self, message, context=None, current_message_id=None):
            return _FakeResult()

    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: _FakeProvider())

    routing = RoutingDecision(
        needs_analysis=True,
        needs_llm=True,
        run_summary=True,
        run_task_extraction=True,
        run_deadline_detection=True,
        run_recommended_action=True,
    )

    result = asyncio.run(
        analyze_message(
            "Please fix our production server today",
            message_id="msg1",
            user_id="user1",
            run_tasks=True,
            routing=routing,
        )
    )
    assert result["status"] == "completed"
    assert result["priority"] == "urgent"
    assert result["confidence"] == 0.91
    assert result["summary"] == "production server is down"
    assert result["deadlines"] == ["today"]
