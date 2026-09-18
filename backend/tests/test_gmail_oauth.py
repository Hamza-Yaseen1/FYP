"""
Tests for Gmail OAuth flow (User Story 1 — Connect Gmail via Google OAuth).

Written FIRST (TDD). Must FAIL before the corresponding implementation
tasks T011-T016 are complete.

Tests cover:
- T009: Contract tests for auth-url, POST /connections gmail rejection, callback
- T010: Unit tests for state sign/verify, build_authorization_url
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest
from bson import ObjectId

from services.security import JWT_SECRET, create_access_token

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

TEST_USER_EMAIL = "gmail-test@example.com"
TEST_USER_PASSWORD = "s3cretpass"
STATE_SECRET = "test-gmail-state-secret"


def _register_and_login(client):
    """Register a test user and return their user_id string + set cookie."""
    res = client.post(
        "/auth/register",
        json={
            "name": "Gmail Tester",
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        },
    )
    assert res.status_code == 201
    user_id = res.json()["id"]
    return user_id


def _make_state(user_id: str, expires_in: int = 600) -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "purpose": "gmail_oauth",
            "jti": "fake-uuid-123",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        },
        STATE_SECRET,
        algorithm="HS256",
    )


# ──────────────────────────────────────────────────────────────
# T010: Unit tests — build_authorization_url / verify_state
# ──────────────────────────────────────────────────────────────


class TestBuildAuthorizationUrl:
    """Verify the Google consent URL is well-formed."""

    def test_includes_required_gmail_readonly_scope(self):
        from services.gmail import build_authorization_url

        url = build_authorization_url("some-user-id")
        assert "scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly" in url

    def test_includes_prompt_consent(self):
        from services.gmail import build_authorization_url

        url = build_authorization_url("some-user-id")
        assert "prompt=consent" in url

    def test_includes_access_type_offline(self):
        from services.gmail import build_authorization_url

        url = build_authorization_url("some-user-id")
        assert "access_type=offline" in url

    def test_signed_state_contains_user_id(self):
        from services.gmail import build_authorization_url, verify_state

        url = build_authorization_url("u123")
        # Extract state from URL
        state = url.split("state=")[1].split("&")[0]
        assert verify_state(state) == "u123"

    def test_includes_redirect_uri(self):
        from services.gmail import build_authorization_url

        url = build_authorization_url("u1")
        assert "redirect_uri=" in url

    def test_includes_response_type_code(self):
        from services.gmail import build_authorization_url

        url = build_authorization_url("u1")
        assert "response_type=code" in url


class TestVerifyState:
    """Verify JWT state validation (uses the real state secret from gmail service)."""

    def test_valid_state_returns_user_id(self):
        from services.gmail import verify_state, STATE_SIGNING_SECRET

        state = jwt.encode(
            {
                "sub": "user-abc",
                "purpose": "gmail_oauth",
                "jti": "id1",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            STATE_SIGNING_SECRET,
            algorithm="HS256",
        )
        assert verify_state(state) == "user-abc"

    def test_invalid_signature_returns_none(self):
        from services.gmail import verify_state, STATE_SIGNING_SECRET

        token = jwt.encode(
            {"sub": "user-abc", "purpose": "gmail_oauth", "exp": 999999999999},
            "completely-wrong-secret",
            algorithm="HS256",
        )
        assert verify_state(token) is None

    def test_wrong_purpose_returns_none(self):
        from services.gmail import verify_state, STATE_SIGNING_SECRET

        token = jwt.encode(
            {"sub": "user-abc", "purpose": "login_session", "exp": 999999999999},
            STATE_SIGNING_SECRET,
            algorithm="HS256",
        )
        assert verify_state(token) is None

    def test_expired_token_returns_none(self):
        from services.gmail import verify_state, STATE_SIGNING_SECRET

        token = jwt.encode(
            {
                "sub": "user-abc",
                "purpose": "gmail_oauth",
                "exp": 1000000000,  # long past
            },
            STATE_SIGNING_SECRET,
            algorithm="HS256",
        )
        assert verify_state(token) is None

    def test_malformed_string_returns_none(self):
        from services.gmail import verify_state

        assert verify_state("not-a-jwt-at-all") is None


# ──────────────────────────────────────────────────────────────
# T009: Contract tests — HTTP endpoints
# ──────────────────────────────────────────────────────────────


class TestGmailAuthUrlContract:
    """GET /connections/gmail/auth-url"""

    def test_requires_authentication(self, client):
        resp = client.get("/connections/gmail/auth-url")
        assert resp.status_code == 401

    def test_returns_auth_url_for_logged_in_user(self, client):
        _register_and_login(client)
        with patch(
            "routes.gmail.build_authorization_url",
            return_value="https://accounts.google.com/o/oauth2/v2/auth?mock=1",
        ):
            resp = client.get("/connections/gmail/auth-url")
            assert resp.status_code == 200
            body = resp.json()
            assert "auth_url" in body
            assert body["auth_url"].startswith("https://accounts.google.com/")

    def test_not_found_without_session(self, client):
        resp = client.get("/connections/gmail/auth-url")
        assert resp.status_code == 401


class TestGmailCallbackContract:
    """GET /connections/gmail/callback"""

    def test_redirects_to_error_on_invalid_state(self, client):
        resp = client.get(
            "/connections/gmail/callback",
            params={"code": "abc", "state": "bad-state-string"},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 307)
        assert "gmail=error" in resp.headers["location"]

    def test_redirects_to_error_when_google_returns_error(self, client):
        user_id = _register_and_login(client)
        state = _make_state(user_id)
        resp = client.get(
            "/connections/gmail/callback",
            params={"error": "access_denied", "state": state},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 307)
        assert "gmail=error" in resp.headers["location"]


class TestGoogleCallbackAliasContract:
    """GET /auth/google/callback — matches GOOGLE_REDIRECT_URI in backend/.env"""

    def test_redirects_to_error_on_invalid_state(self, client):
        resp = client.get(
            "/auth/google/callback",
            params={"code": "abc", "state": "bad-state-string"},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 307)
        assert "gmail=error" in resp.headers["location"]

    def test_redirects_to_error_when_google_returns_error(self, client):
        user_id = _register_and_login(client)
        state = _make_state(user_id)
        resp = client.get(
            "/auth/google/callback",
            params={"error": "access_denied", "state": state},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 307)
        assert "gmail=error" in resp.headers["location"]

    def test_success_redirects_connected(self, client, sync_db):
        """Full flow: valid state + code → tokens stored encrypted → redirect."""
        from services.gmail import STATE_SIGNING_SECRET
        from utils.encryption import decrypt

        user_id = _register_and_login(client)
        state = jwt.encode(
            {
                "sub": user_id,
                "purpose": "gmail_oauth",
                "jti": "flow-1",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            STATE_SIGNING_SECRET,
            algorithm="HS256",
        )

        async def _fake_exchange(code):
            return ("raw-access-token", "raw-refresh-token", 3600)

        async def _fake_email_display(token):
            return "demo@gmail.com"

        with patch("routes.gmail.exchange_code", side_effect=_fake_exchange), patch(
            "routes.gmail.get_gmail_email_display", side_effect=_fake_email_display
        ):
            resp = client.get(
                "/auth/google/callback",
                params={"code": "valid-code", "state": state},
                follow_redirects=False,
            )

        assert resp.status_code in (302, 307)
        assert "gmail=connected" in resp.headers["location"]

        # Tokens stored encrypted under the callback owner (requirement 4)
        conn = sync_db.connections.find_one({"user_id": user_id, "provider": "gmail"})
        assert conn is not None
        # Encrypted at rest — never plaintext
        assert decrypt(conn["access_token"]) == "raw-access-token"
        assert decrypt(conn["refresh_token"]) == "raw-refresh-token"
        assert conn["gmail_email"] == "demo@gmail.com"
        assert "connected" in str(conn["status"])

        # Tokens never leaked in the redirect/response (requirement 6)
        assert "raw-access-token" not in resp.text
        assert "raw-refresh-token" not in resp.text


class TestCreateConnectionGmailGuard:
    """POST /connections with provider=gmail must be rejected (T008 guard)."""

    def test_rejects_gmail_provider(self, client):
        _register_and_login(client)
        resp = client.post("/connections", json={"provider": "gmail"})
        assert resp.status_code == 400
        assert "Gmail connect flow" in resp.json()["detail"]

    def test_whatsapp_still_accepted(self, client):
        _register_and_login(client)
        resp = client.post("/connections", json={"provider": "whatsapp"})
        assert resp.status_code == 201
