"""Groq oversized-request (HTTP 413) handling.

An over-budget request is NOT a quota problem: waiting cannot fix it. The
provider must (a) shorten the prompt so it fits, retrying ONCE on the small
fallback model, and (b) surface a TERMINAL ``MessageTooLargeError`` if even the
shortened prompt is too big, so the message is not retried forever.

Unit tests against a FAKE async Groq client — no network, no API key needed.
"""

import asyncio
import json
import types

import httpx
import pytest
from groq import BadRequestError, NotFoundError

import services.ai.providers.groq as groq_module
from services.ai.providers.groq import (
    FALLBACK_MODEL,
    MODEL_NAME,
    GroqProvider,
    MessageTooLargeError,
)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_payload_do_not_leak")
    monkeypatch.setattr(
        groq_module, "_rate_limit_state", {"loop": None, "semaphore": None}
    )
    monkeypatch.setattr(groq_module, "_probe_lock_state", {"loop": None, "lock": None})
    groq_module.reset_breaker_for_tests()
    yield
    groq_module.reset_breaker_for_tests()


def _make_413(message="Request too large for model on tokens per minute (TPM)"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(413, request=req, headers={})
    return BadRequestError(
        message, response=resp, body={"error": {"message": message}}
    )


def _make_400(message="bad json"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(400, request=req, headers={})
    return BadRequestError(message, response=resp, body={})


def _make_404(message="The model does not exist or you do not have access"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(404, request=req, headers={})
    return NotFoundError(message, response=resp, body={"error": {"message": message}})


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


def test_413_falls_back_to_smaller_model_with_shorter_prompt():
    calls = []

    async def handler(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise _make_413()
        return _json_response({"priority": "urgent", "confidence": 0.9})

    result = asyncio.run(_provider(handler).analyze("x" * 40000))

    assert result.priority == "urgent"
    assert len(calls) == 2
    assert calls[0]["model"] == MODEL_NAME
    assert calls[1]["model"] == FALLBACK_MODEL
    first_prompt = calls[0]["messages"][0]["content"]
    second_prompt = calls[1]["messages"][0]["content"]
    assert len(second_prompt) < len(first_prompt)


def test_413_on_both_attempts_is_terminal():
    calls = []

    async def handler(kwargs):
        calls.append(kwargs)
        raise _make_413()

    with pytest.raises(MessageTooLargeError):
        asyncio.run(_provider(handler).analyze("x" * 40000))

    # Exactly two attempts: primary once, shortened fallback once — never more.
    assert len(calls) == 2
    assert calls[1]["model"] == FALLBACK_MODEL


def test_default_fallback_model_is_available_and_differs_from_primary():
    # ``llama-3.1-8b-instant`` is NOT available on every Groq account (404);
    # the default must be a broadly-available small model.
    assert FALLBACK_MODEL == "openai/gpt-oss-20b"
    assert FALLBACK_MODEL != MODEL_NAME


def test_reasoning_effort_is_model_aware():
    # qwen accepts "none" (no thinking); gpt-oss rejects it with HTTP 400.
    assert groq_module._reasoning_effort_for("qwen/qwen3.8-27b") == "none"
    assert groq_module._reasoning_effort_for("openai/gpt-oss-20b") == "low"
    assert groq_module._reasoning_effort_for("openai/gpt-oss-120b") == "low"


def test_fallback_attempt_uses_low_reasoning_effort():
    calls = []

    async def handler(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise _make_413()
        return _json_response({"priority": "urgent", "confidence": 0.9})

    asyncio.run(_provider(handler).analyze("x" * 40000))

    assert calls[0]["reasoning_effort"] == "none"
    assert calls[1]["model"] == FALLBACK_MODEL
    assert calls[1]["reasoning_effort"] == "low"


def test_413_then_fallback_model_not_found_is_terminal():
    """A 404 on the fallback model must NOT be re-pended forever: after the
    primary 413 and a failed rescue there is nothing left to retry."""
    calls = []

    async def handler(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise _make_413()
        raise _make_404()

    with pytest.raises(MessageTooLargeError):
        asyncio.run(_provider(handler).analyze("x" * 40000))

    assert len(calls) == 2
    assert calls[1]["model"] == FALLBACK_MODEL


def test_413_does_not_open_circuit_breaker():
    async def handler(kwargs):
        raise _make_413()

    with pytest.raises(MessageTooLargeError):
        asyncio.run(_provider(handler).analyze("x" * 40000))

    assert groq_module.breaker_state() != "open"
    assert groq_module.is_groq_available() is True


def test_plain_400_is_not_treated_as_too_large():
    calls = []

    async def handler(kwargs):
        calls.append(kwargs)
        raise _make_400()

    with pytest.raises(BadRequestError):
        asyncio.run(_provider(handler).analyze("short message"))

    # No fallback retry for a non-413 client error.
    assert len(calls) == 1


def test_oversized_message_is_budgeted_before_the_call():
    captured = {}

    async def handler(kwargs):
        captured["prompt"] = kwargs["messages"][0]["content"]
        return _json_response({"priority": "normal"})

    asyncio.run(_provider(handler).analyze("Subject: big\n\n" + "body " * 8000))

    assert groq_module.estimate_tokens(captured["prompt"]) <= (
        groq_module.MAX_PROMPT_TOKENS
    )
    assert "Subject: big" in captured["prompt"]
