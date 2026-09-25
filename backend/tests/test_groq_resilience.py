"""Groq resilience: circuit breaker, TPD vs transient 429, graceful fallback.

The showcase contract verified here (fake clients only — no network):
- a DAILY quota (TPD) 429 is NEVER retried; it opens the circuit breaker so the
  app stops hammering an exhausted API.
- while the breaker is OPEN no Groq request is attempted: calls raise
  ``GroqUnavailableError`` instantly and callers fall back deterministically.
- after the cooldown a SINGLE probe request closes the breaker on success or
  re-opens it on another quota error. Only one probe may cross at a time.
- a TRANSIENT 429 (OTPM) is retried at most once with a sub-second wait and
  never opens the breaker.
- the exempt layers (JARVIS deterministic answers, retry sweep) keep working
  with ZERO Groq contact while the breaker is open.
- JARVIS spends at most one classifier + one chat call on an unknown phrase.
"""

import asyncio
import json
import logging
import time
import types

import httpx
import pytest
from groq import RateLimitError

import services.ai.providers.groq as groq_module
from services.ai.providers.groq import GroqProvider, GroqUnavailableError


@pytest.fixture(autouse=True)
def _reset_circuit(monkeypatch):
    """Fresh breaker + limiter per test so nothing leaks across tests."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_resilience_do_not_leak")
    monkeypatch.setattr(
        groq_module, "_rate_limit_state", {"loop": None, "semaphore": None}
    )
    monkeypatch.setattr(groq_module, "_probe_lock_state", {"loop": None, "lock": None})
    groq_module.reset_breaker_for_tests()
    yield
    groq_module.reset_breaker_for_tests()


def _make_429(message="output tokens per minute (OTPM): limit exceeded"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers={})
    return RateLimitError(
        message,
        response=resp,
        body={"error": {"message": message, "type": "rate_limit_exceeded"}},
    )


def _make_tpd_429():
    message = "tokens per day (TPD): Limit 20000; Used 19000; Requested 1000"
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers={})
    return RateLimitError(
        message,
        response=resp,
        body={"error": {"message": message, "type": "tokens_per_day"}},
    )


def _json_response(payload: dict):
    message = types.SimpleNamespace(content=json.dumps(payload))
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


class _FakeClient:
    def __init__(self, handler):
        self.chat = _FakeChat(handler)


class _FakeChat:
    def __init__(self, handler):
        self.completions = _FakeCompletions(handler)


class _FakeCompletions:
    def __init__(self, handler):
        self._handler = handler

    async def create(self, **kwargs):
        return await self._handler(kwargs)


def _provider(handler) -> GroqProvider:
    provider = GroqProvider()
    provider.client = _FakeClient(handler)
    return provider


def _expire_cooldown():
    groq_module._CIRCUIT["unavailable_until"] = time.monotonic() - 0.1


# ── TPD / transient split ───────────────────────────────────────────────────


def test_tpd_429_is_not_retried_and_opens_breaker(monkeypatch):
    monkeypatch.setattr(groq_module, "RETRY_ATTEMPTS", 3)
    calls = []

    async def handler(kwargs):
        calls.append(1)
        raise _make_tpd_429()

    with pytest.raises(RateLimitError):
        asyncio.run(_provider(handler)._complete("m"))

    assert len(calls) == 1
    assert groq_module.breaker_state() == "open"
    assert groq_module.is_groq_available() is False


def test_transient_429_retries_once_without_opening_breaker(monkeypatch):
    monkeypatch.setattr(groq_module, "RETRY_ATTEMPTS", 2)
    monkeypatch.setattr(groq_module, "INITIAL_RETRY_DELAY", 0.01)
    monkeypatch.setattr(groq_module, "MAX_RETRY_WAIT", 0.05)
    calls = []

    async def handler(kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise _make_429()
        return _json_response({"priority": "normal"})

    result = asyncio.run(_provider(handler)._complete("m"))

    assert result["priority"] == "normal"
    assert len(calls) == 2
    assert groq_module.breaker_state() == "closed"
    assert groq_module.is_groq_available() is True


def test_apply_circuit_rules_ignores_transient_and_generic_errors():
    groq_module._apply_circuit_rules(_make_429())
    assert groq_module.breaker_state() == "closed"
    groq_module._apply_circuit_rules(ValueError("boom"))
    assert groq_module.breaker_state() == "closed"


# ── Open breaker behavior ───────────────────────────────────────────────────


def test_open_breaker_raises_fast_without_network():
    groq_module.open_breaker("tokens_per_day")
    calls = []

    async def handler(kwargs):
        calls.append(1)
        return _json_response({"priority": "low"})

    with pytest.raises(GroqUnavailableError):
        asyncio.run(_provider(handler)._complete("m"))
    assert calls == []


def test_chat_degrades_to_empty_dict_during_cooldown():
    groq_module.open_breaker("tokens_per_day")
    calls = []

    async def handler(kwargs):
        calls.append(1)
        return _json_response({"priority": "low"})

    result = asyncio.run(_provider(handler).chat("hello"))
    assert result == {}
    assert calls == []


# ── Half-open probe ─────────────────────────────────────────────────────────


def test_probe_success_closes_breaker_after_cooldown(monkeypatch):
    groq_module.open_breaker("tokens_per_day")
    _expire_cooldown()
    assert groq_module.breaker_state() == "half_open"

    async def handler(kwargs):
        return _json_response({"priority": "urgent"})

    result = asyncio.run(_provider(handler)._complete("m"))

    assert result["priority"] == "urgent"
    assert groq_module.breaker_state() == "closed"


def test_probe_tpd_reopens_breaker():
    groq_module.open_breaker("tokens_per_day")
    _expire_cooldown()
    calls = []

    async def handler(kwargs):
        calls.append(1)
        raise _make_tpd_429()

    with pytest.raises(RateLimitError):
        asyncio.run(_provider(handler)._complete("m"))

    assert groq_module.breaker_state() == "open"
    assert len(calls) == 1


def test_only_single_probe_crosses_half_open():
    groq_module.open_breaker("tokens_per_day")
    _expire_cooldown()
    calls = []

    async def handler(kwargs):
        calls.append(1)
        raise _make_tpd_429()

    async def run():
        provider = _provider(handler)
        return await asyncio.gather(
            *[provider._complete("m"), provider._complete("m")],
            return_exceptions=True,
        )

    results = asyncio.run(run())

    assert len(calls) == 1
    for r in results:
        assert isinstance(r, (RateLimitError, GroqUnavailableError))
    assert groq_module.breaker_state() == "open"


# ── Exempt layers (JARVIS deterministic answers, retry sweep) ──────────────


def test_jarvis_llm_gates_honor_breaker_with_key_present():
    from services.ai.jarvis_actions import _llm_configured as actions_ok
    from services.ai.jarvis_agent import _llm_configured as agent_ok
    from services.ai.jarvis_intents import _llm_configured as intents_ok
    from services.ai.jarvis_messages import _llm_configured as messages_ok

    assert intents_ok() is True
    assert agent_ok() is True
    assert messages_ok() is True
    assert actions_ok() is True

    groq_module.open_breaker("tokens_per_day")

    assert intents_ok() is False
    assert agent_ok() is False
    assert messages_ok() is False
    assert actions_ok() is False


def test_llm_intent_does_not_consult_provider_during_cooldown(monkeypatch):
    from services.ai.jarvis_intents import llm_intent

    groq_module.open_breaker("tokens_per_day")
    calls = []

    class _BoomProvider:
        async def chat(self, prompt):
            calls.append(1)
            raise AssertionError("provider must not be called during cooldown")

    monkeypatch.setattr("services.ai.jarvis_intents.GroqProvider", _BoomProvider)

    assert asyncio.run(llm_intent("bring me the numbers please")) is None
    assert calls == []


def test_retry_pending_sweep_skips_during_cooldown(monkeypatch):
    import services.retry_pending

    groq_module.open_breaker("tokens_per_day")

    class _BoomCollection:
        def find(self, *args, **kwargs):
            raise AssertionError("sweep must not touch the DB during cooldown")

    monkeypatch.setattr(
        "services.retry_pending.messages_collection", _BoomCollection()
    )

    assert asyncio.run(services.retry_pending.retry_pending_analyses()) == 0


def test_process_message_skips_pipeline_during_cooldown(monkeypatch):
    """OPEN breaker → pending fallback WITHOUT touching analyze_message or the
    provider (no GroqProvider init, no context fetch, no LLM attempt)."""
    from services.ai.orchestrate import process_message

    groq_module.open_breaker("tokens_per_day")
    calls = []

    class _BoomProvider:
        def __init__(self):
            calls.append("init")
            raise AssertionError("GroqProvider must not be built during cooldown")

    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: _BoomProvider())

    result = asyncio.run(
        process_message(
            "Send me the slides tonight", message_id="msg-cd", user_id="user-test"
        )
    )

    assert calls == []
    assert result["status"] == "pending"
    assert result["provider"] == "groq"
    assert result["priority"] == "normal"
    assert result["tasks_extracted"] == []
    assert result["deadlines"] == []
    assert result["routing"]["llm_call_used"] is True


def test_process_message_cooldown_emits_no_noisy_logs(caplog, monkeypatch):
    """During cooldown neither 'GroqProvider initialized', 'Starting AI
    analysis', nor 'AI analysis deferred' should appear per message."""
    from services.ai.orchestrate import process_message

    groq_module.open_breaker("tokens_per_day")
    monkeypatch.setattr(
        "services.ai.analyzer.get_provider",
        lambda: (_ for _ in ()).throw(AssertionError("must not init")),
    )

    with caplog.at_level(logging.INFO):
        asyncio.run(
            process_message(
                "Send me the slides tonight", message_id="msg-log", user_id="user-test"
            )
        )

    lines = [r.getMessage() for r in caplog.records]
    assert not any("GroqProvider initialized" in l for l in lines)
    assert not any("Starting AI analysis" in l for l in lines)
    assert not any("AI analysis deferred" in l for l in lines)


def test_closed_breaker_process_message_still_analyzes(monkeypatch):
    """"The fast-path guard must NOT swallow analysis when the breaker is CLOSED."""
    from services.ai.orchestrate import process_message

    class _FakeProvider:
        async def analyze(self, *args, **kwargs):
            from services.ai.providers.base import AIAnalysisResult

            return AIAnalysisResult(
                priority="urgent",
                confidence=0.9,
                explanation="fake",
                summary="fake summary",
                recommended_actions=["Respond"],
                tasks_extracted=[],
                deadlines=[],
                context_updates=[],
            )

    monkeypatch.setattr("services.ai.analyzer.get_provider", lambda: _FakeProvider())

    result = asyncio.run(
        process_message(
            "Send me the slides tonight", message_id="msg-ok", user_id="user-test"
        )
    )

    assert result["status"] == "completed"
    assert result["priority"] == "urgent"
    assert result["routing"]["llm_call_used"] is True


def test_summarize_uses_digest_during_cooldown(monkeypatch):
    from services.ai.jarvis_messages import _llm_configured

    assert _llm_configured() is True
    groq_module.open_breaker("tokens_per_day")
    assert _llm_configured() is False


# ── API key hygiene ─────────────────────────────────────────────────────────


def test_key_never_logged_when_breaker_opens(caplog):
    caplog.set_level(logging.DEBUG, logger="services.ai.providers.groq")

    async def handler(kwargs):
        raise _make_tpd_429()

    with pytest.raises(RateLimitError):
        asyncio.run(_provider(handler)._complete("m"))

    assert caplog.records
    for record in caplog.records:
        assert "gsk_resilience_do_not_leak" not in record.getMessage()
        assert "gsk_" not in record.getMessage()


# ── JARVIS endpoint end-to-end (faked providers, no network) ────────────────

_REGISTER_BODY = {
    "name": "Resilience User",
    "email": "jarvis-resilience@test.com",
    "password": "passA12345",
}


def _register(client, email="jarvis-resilience@test.com"):
    res = client.post("/auth/register", json={**_REGISTER_BODY, "email": email})
    assert res.status_code == 201
    return res.json()["id"], res.cookies.get("cai_token")


def _switch(client, token):
    client.cookies.clear()
    if token:
        client.cookies.set("cai_token", token)


def _chat(client, message):
    return client.post("/jarvis/chat", json={"message": message})


class TestJarvisEndToEnd:
    def test_ambiguous_phrase_spends_at_most_one_classifier_call(
        self, client, monkeypatch
    ):
        """One classifier + one chat = 2 LLM round-trips max, never 3."""
        uid, tok = _register(client)
        _switch(client, tok)

        class _Classifier:
            instances = []
            calls = []

            def __init__(self):
                _Classifier.instances.append(self)

            async def chat(self, prompt):
                _Classifier.calls.append(prompt)
                return {"reply": "not a whitelisted label"}

        class _Chat:
            instances = []
            calls = []

            def __init__(self):
                _Chat.instances.append(self)

            async def chat(self, prompt):
                _Chat.calls.append(prompt)
                return {"reply": "That is a good one."}

        _Classifier.instances, _Classifier.calls = [], []
        _Chat.instances, _Chat.calls = [], []
        monkeypatch.setattr("services.ai.jarvis_intents.GroqProvider", _Classifier)
        monkeypatch.setattr("services.ai.jarvis_agent.GroqProvider", _Chat)
        monkeypatch.setattr(
            "services.ai.jarvis_intents._llm_configured", lambda: True
        )
        monkeypatch.setattr("services.ai.jarvis_agent._llm_configured", lambda: True)

        res = _chat(client, "Tell me a joke about sandwiches")
        data = res.json()

        assert data["reply"] == "That is a good one."
        assert data["used_ai"] is True
        assert any("User command:" in p for p in _Chat.calls)
        assert len(_Classifier.calls) == 1
        assert "User request:" in _Classifier.calls[0]

    def test_jarvis_answers_deterministically_during_cooldown(
        self, client, monkeypatch
    ):
        """While the breaker is OPEN, JARVIS still answers instantly from data."""
        groq_module.open_breaker("tokens_per_day")
        uid, tok = _register(client, "jarvis-resilience@test.com")
        _switch(client, tok)

        class _BoomProvider:
            async def chat(self, prompt):
                raise AssertionError("must not consult Groq during cooldown")

        monkeypatch.setattr("services.ai.jarvis_intents.GroqProvider", _BoomProvider)
        monkeypatch.setattr("services.ai.jarvis_agent.GroqProvider", _BoomProvider)
        monkeypatch.setattr(
            "services.ai.jarvis_intents._llm_configured", lambda: True
        )
        monkeypatch.setattr("services.ai.jarvis_agent._llm_configured", lambda: True)

        res = _chat(client, "How many messages do I have?")
        assert res.status_code == 200
        data = res.json()
        assert data["used_ai"] is False
        assert data["action"] is None
        assert "conversational AI service is currently unavailable" not in data["reply"]

        res = _chat(client, "Show my unread messages.")
        data = res.json()
        assert data["used_ai"] is False
        assert "messages" in data["reply"].lower()