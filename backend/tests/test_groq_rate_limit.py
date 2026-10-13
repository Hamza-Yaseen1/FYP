"""Groq provider rate-limit/retry + concurrency + compact-output policy.

Unit tests against a FAKE async Groq client — no network, no API key needed.
These verify the 429 fix contract:
- output budget is reduced and reasoning is disabled (reasoning_effort="none")
- retries are bounded, Retry-After-aware, and capped so the pipeline never
  blocks for tens of seconds
- non-retryable failures fail fast (no hammering)
- concurrent Groq calls are capped
- the API key never appears in logs
"""

import asyncio
import json
import logging
import types

import httpx
import pytest
from groq import (
    APITimeoutError,
    BadRequestError,
    RateLimitError,
)

import services.ai.providers.groq as groq_module
from services.ai.providers.groq import GroqProvider


@pytest.fixture(autouse=True)
def _fake_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_do_not_leak_me")
    monkeypatch.setattr(
        groq_module,
        "_rate_limit_state",
        {"loop": None, "semaphore": None},
    )
    monkeypatch.setattr(groq_module, "_probe_lock_state", {"loop": None, "lock": None})
    groq_module.reset_breaker_for_tests()


def _make_429(headers=None, message="output tokens per minute (OTPM): limit exceeded"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers=headers or {})
    return RateLimitError(message, response=resp, body={"error": {"message": message}})


def _make_http_error(status: int, message: str = "boom"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(status, request=req, headers={})
    return BadRequestError(message, response=resp, body={})


def _json_response(payload: dict):
    message = types.SimpleNamespace(content=json.dumps(payload))
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


class _FakeClient:
    """Drops in for ``AsyncGroq`` so ``_complete`` never touches the network."""

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


# ── Output budget / reasoning policy ───────────────────────────────────────


def test_compact_output_policy_defaults():
    assert groq_module.MAX_OUTPUT_TOKENS <= 400
    assert groq_module.MAX_OUTPUT_TOKENS > 0


def test_completion_params_are_compact(monkeypatch):
    monkeypatch.setattr(groq_module, "MAX_OUTPUT_TOKENS", 400)
    captured = {}

    async def handler(kwargs):
        captured.update(kwargs)
        return _json_response({"priority": "low", "confidence": 0.8})

    result = asyncio.run(_provider(handler)._complete("analyze this message"))

    assert result["priority"] == "low"
    assert captured["model"] == groq_module.MODEL_NAME
    assert captured["max_tokens"] == 400
    assert captured["reasoning_effort"] == "none"
    assert captured["response_format"] == {"type": "json_object"}


def test_prompt_explicitly_asks_for_concise_json_only():
    prompt = groq_module.ANALYSIS_PROMPT
    assert "Return ONLY ONE compact JSON object" in prompt
    assert "reasoning, chain-of-thought" in prompt
    assert "{message}" in prompt


# ── Retry / 429 handling ────────────────────────────────────────────────────


def test_retry_wait_respects_and_caps_retry_after(monkeypatch):
    monkeypatch.setattr(groq_module, "INITIAL_RETRY_DELAY", 0.5)
    monkeypatch.setattr(groq_module, "MAX_RETRY_WAIT", 3)

    long_wait = _make_429(headers={"retry-after": "25"})
    assert groq_module._retry_wait(long_wait, 0) == 3.0

    short_wait = _make_429(headers={"retry-after": "1"})
    assert groq_module._retry_wait(short_wait, 0) == 1.0

    no_header = _make_429(headers={})
    assert groq_module._retry_wait(no_header, 1) == 1.0


def test_retry_succeeds_after_transient_429(monkeypatch):
    monkeypatch.setattr(groq_module, "RETRY_ATTEMPTS", 3)
    monkeypatch.setattr(groq_module, "INITIAL_RETRY_DELAY", 0.01)
    monkeypatch.setattr(groq_module, "MAX_RETRY_WAIT", 0.1)
    calls = []

    async def handler(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise _make_429(headers={"retry-after": "5"})
        return _json_response({"priority": "urgent"})

    result = asyncio.run(_provider(handler)._complete("m"))

    assert result["priority"] == "urgent"
    assert len(calls) == 2


def test_retry_exhausted_raises_rate_limit(monkeypatch):
    monkeypatch.setattr(groq_module, "RETRY_ATTEMPTS", 2)
    monkeypatch.setattr(groq_module, "INITIAL_RETRY_DELAY", 0.01)
    monkeypatch.setattr(groq_module, "MAX_RETRY_WAIT", 0.1)
    calls = []

    async def handler(kwargs):
        calls.append(1)
        raise _make_429(headers={"retry-after": "5"})

    with pytest.raises(RateLimitError):
        asyncio.run(_provider(handler)._complete("m"))
    assert len(calls) == 2


def test_non_retryable_400_fails_fast(monkeypatch):
    monkeypatch.setattr(groq_module, "RETRY_ATTEMPTS", 3)
    calls = []

    async def handler(kwargs):
        calls.append(1)
        raise _make_http_error(400)

    with pytest.raises(BadRequestError):
        asyncio.run(_provider(handler)._complete("m"))
    assert len(calls) == 1


def test_timeout_is_retryable():
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    assert groq_module._is_retryable(APITimeoutError(request=req)) is True
    assert groq_module._is_retryable(_make_429()) is True
    assert groq_module._is_retryable(_make_http_error(400)) is False
    assert groq_module._is_retryable(ValueError("boom")) is False


def test_tpd_429_is_not_retryable():
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(429, request=req, headers={})
    tpd = RateLimitError(
        "tokens per day (TPD): Limit 20000; Used 19000; Requested 1000",
        response=resp,
        body={"error": {
            "message": "tokens per day (TPD): Limit 20000; Used 19000; Requested 1000",
            "type": "tokens_per_day",
        }},
    )
    assert groq_module._is_tpd_quota(tpd) is True
    assert groq_module._is_retryable(tpd) is False


# ── Concurrency cap ─────────────────────────────────────────────────────────


def test_concurrent_calls_are_capped(monkeypatch):
    monkeypatch.setattr(groq_module, "MAX_CONCURRENT_GROQ_CALLS", 2)
    active = 0
    peak = 0

    async def handler(kwargs):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.02)
        active -= 1
        return _json_response({"priority": "normal"})

    async def run():
        provider = _provider(handler)
        await asyncio.gather(*[provider._complete("m") for _ in range(8)])
        return peak

    assert asyncio.run(run()) <= 2


# ── No API key in logs ──────────────────────────────────────────────────────


def test_init_logs_never_contain_api_key(caplog, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_SUPER_SECRET_VALUE_123")
    caplog.set_level(logging.INFO, logger="services.ai.providers.groq")

    GroqProvider()

    for record in caplog.records:
        message = record.getMessage()
        assert "gsk_SUPER_SECRET_VALUE_123" not in message
        assert "gsk_" not in message