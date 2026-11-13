import asyncio
import logging

import httpx
import pytest

from services import password_reset

TOKEN = "test-reset-token-abc123"
API_KEY = "xkeysib-test-key"


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class _FakeAsyncClient:
    """Minimal stand-in for httpx.AsyncClient."""

    status_code = 201
    error = None
    calls = 0
    last_request = None
    last_kwargs = None

    def __init__(self, *args, **kwargs):
        type(self).last_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, url, headers=None, json=None):
        if type(self).error is not None:
            raise type(self).error
        type(self).calls += 1
        type(self).last_request = {
            "url": url,
            "headers": headers,
            "json": json,
        }
        return _FakeResponse(type(self).status_code)


def install_fake_client(monkeypatch, status_code=201, error=None):
    _FakeAsyncClient.status_code = status_code
    _FakeAsyncClient.error = error
    _FakeAsyncClient.calls = 0
    _FakeAsyncClient.last_request = None
    _FakeAsyncClient.last_kwargs = None
    monkeypatch.setattr(password_reset.httpx, "AsyncClient", _FakeAsyncClient)
    return _FakeAsyncClient


@pytest.fixture
def brevo_env(monkeypatch):
    monkeypatch.setenv("BREVO_API_KEY", API_KEY)
    monkeypatch.setenv("EMAIL_FROM", "sender@example.com")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    return monkeypatch


def send_reset():
    return asyncio.run(
        password_reset.send_password_reset_email(
            "user@example.com", "Ali", TOKEN
        )
    )


class TestBrevoRequest:
    def test_posts_reset_email_to_brevo(self, brevo_env):
        fake = install_fake_client(brevo_env)

        assert send_reset() is True
        assert fake.calls == 1

        request = fake.last_request
        assert request["url"] == "https://api.brevo.com/v3/smtp/email"
        assert request["headers"]["api-key"] == API_KEY
        assert request["headers"]["Content-Type"] == "application/json"

        body = request["json"]
        assert body["sender"]["email"] == "sender@example.com"
        assert body["to"] == [{"email": "user@example.com"}]
        assert body["subject"] == "Reset your password"

        link = f"http://localhost:3000/reset-password?token={TOKEN}"
        assert link in body["htmlContent"]
        assert link in body["textContent"]
        assert TOKEN in body["textContent"]

    def test_request_is_given_a_timeout(self, brevo_env):
        fake = install_fake_client(brevo_env)
        send_reset()
        assert fake.last_kwargs["timeout"] == password_reset.BREVO_TIMEOUT_SECONDS

    def test_4xx_response_returns_false(self, brevo_env):
        install_fake_client(brevo_env, status_code=400)
        assert send_reset() is False

    def test_5xx_response_returns_false(self, brevo_env):
        install_fake_client(brevo_env, status_code=500)
        assert send_reset() is False

    def test_timeout_returns_false(self, brevo_env):
        install_fake_client(
            brevo_env, error=httpx.TimeoutException("timed out")
        )
        assert send_reset() is False

    def test_network_error_returns_false(self, brevo_env):
        install_fake_client(
            brevo_env, error=httpx.ConnectError("connection refused")
        )
        assert send_reset() is False


class TestBrevoConfig:
    def test_missing_api_key_skips_request(self, monkeypatch):
        monkeypatch.delenv("BREVO_API_KEY", raising=False)
        monkeypatch.setenv("EMAIL_FROM", "sender@example.com")
        fake = install_fake_client(monkeypatch)

        assert send_reset() is False
        assert fake.calls == 0

    def test_missing_sender_skips_request(self, monkeypatch):
        monkeypatch.setenv("BREVO_API_KEY", API_KEY)
        monkeypatch.delenv("EMAIL_FROM", raising=False)
        fake = install_fake_client(monkeypatch)

        assert send_reset() is False
        assert fake.calls == 0

    def test_token_and_api_key_are_never_logged(self, brevo_env, caplog):
        install_fake_client(brevo_env, status_code=401)

        with caplog.at_level(logging.ERROR):
            assert send_reset() is False

        assert TOKEN not in caplog.text
        assert API_KEY not in caplog.text

    def test_missing_key_does_not_log_token(self, monkeypatch, caplog):
        monkeypatch.delenv("BREVO_API_KEY", raising=False)
        monkeypatch.setenv("EMAIL_FROM", "sender@example.com")

        with caplog.at_level(logging.ERROR):
            assert send_reset() is False

        assert TOKEN not in caplog.text
