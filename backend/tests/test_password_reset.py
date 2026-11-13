import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from services import password_reset

REGISTER_BODY = {
    "name": "Reset User",
    "email": "reset@example.com",
    "password": "oldpassword1",
}

FORGOT_MESSAGE = (
    "If an account with that email exists, a password reset link has been sent."
)


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch):
    """Capture outgoing reset emails instead of calling Brevo."""
    monkeypatch.setattr(password_reset, "RESET_REQUEST_COOLDOWN_SECONDS", 0)
    sent: list[dict] = []

    async def fake_send(to_email, name, token):
        sent.append({"to": to_email, "name": name, "token": token})
        return True

    monkeypatch.setattr(password_reset, "send_password_reset_email", fake_send)
    return sent


def register(client, **overrides):
    return client.post("/auth/register", json={**REGISTER_BODY, **overrides})


def request_reset(client, email="reset@example.com"):
    return client.post("/auth/forgot-password", json={"email": email})


def stored_user(sync_db, email="reset@example.com"):
    return sync_db.users.find_one({"email": email})


def as_utc(value):
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class TestForgotPassword:
    def test_known_email_returns_generic_message_and_sends_email(
        self, client, sync_db, sent_emails
    ):
        assert register(client).status_code == 201

        res = request_reset(client)

        assert res.status_code == 200
        assert res.json() == {"message": FORGOT_MESSAGE}
        assert len(sent_emails) == 1
        assert sent_emails[0]["to"] == "reset@example.com"

    def test_token_is_stored_hashed_with_30_minute_expiry(
        self, client, sync_db, sent_emails
    ):
        register(client)
        request_reset(client)

        token = sent_emails[0]["token"]
        user = stored_user(sync_db)

        assert user["reset_token_hash"] == hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()
        assert token not in str(user)

        expires_at = as_utc(user["reset_token_expires_at"])
        remaining = (expires_at - datetime.now(timezone.utc)).total_seconds()
        assert 29 * 60 < remaining <= 30 * 60

    def test_unknown_email_returns_identical_message_without_sending(
        self, client, sent_emails
    ):
        res = request_reset(client, email="nobody@example.com")

        assert res.status_code == 200
        assert res.json() == {"message": FORGOT_MESSAGE}
        assert sent_emails == []

    def test_cooldown_keeps_original_token_and_skips_second_email(
        self, client, sync_db, sent_emails, monkeypatch
    ):
        monkeypatch.setattr(password_reset, "RESET_REQUEST_COOLDOWN_SECONDS", 60)
        register(client)

        assert request_reset(client).status_code == 200
        first_hash = stored_user(sync_db)["reset_token_hash"]
        assert request_reset(client).status_code == 200

        assert len(sent_emails) == 1
        assert stored_user(sync_db)["reset_token_hash"] == first_hash

    @pytest.mark.parametrize("email", ["not-an-email", ""])
    def test_invalid_email_422(self, client, email):
        res = client.post("/auth/forgot-password", json={"email": email})
        assert res.status_code == 422


class TestResetPassword:
    def _issue(self, client, sent_emails):
        register(client)
        request_reset(client)
        return sent_emails[-1]["token"]

    def test_valid_token_updates_password_and_invalidates_token(
        self, client, sync_db, sent_emails
    ):
        token = self._issue(client, sent_emails)

        res = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "newpassword1"},
        )
        assert res.status_code == 200
        assert "reset" in res.json()["message"].lower()

        user = stored_user(sync_db)
        assert "reset_token_hash" not in user
        assert "reset_token_expires_at" not in user

        old_login = client.post(
            "/auth/login",
            json={"email": "reset@example.com", "password": "oldpassword1"},
        )
        assert old_login.status_code == 401

        new_login = client.post(
            "/auth/login",
            json={"email": "reset@example.com", "password": "newpassword1"},
        )
        assert new_login.status_code == 200
        assert "cai_token=" in new_login.headers.get("set-cookie", "")

        reuse = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "anotherpass1"},
        )
        assert reuse.status_code == 400

    def test_expired_token_rejected(self, client, sync_db, sent_emails):
        token = self._issue(client, sent_emails)
        sync_db.users.update_one(
            {"email": "reset@example.com"},
            {
                "$set": {
                    "reset_token_expires_at": datetime.now(timezone.utc)
                    - timedelta(minutes=1)
                }
            },
        )

        res = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "newpassword1"},
        )
        assert res.status_code == 400
        assert "invalid or has expired" in res.json()["detail"]

    def test_unknown_token_rejected(self, client):
        res = client.post(
            "/auth/reset-password",
            json={"token": "not-a-real-token", "password": "newpassword1"},
        )
        assert res.status_code == 400

    def test_short_password_422(self, client, sent_emails):
        token = self._issue(client, sent_emails)
        res = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "short"},
        )
        assert res.status_code == 422

    def test_missing_token_422(self, client):
        res = client.post(
            "/auth/reset-password", json={"password": "newpassword1"}
        )
        assert res.status_code == 422

    def test_reset_does_not_authenticate_the_caller(self, client, sent_emails):
        token = self._issue(client, sent_emails)
        client.cookies.clear()

        res = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "newpassword1"},
        )
        assert res.status_code == 200
        assert client.get("/auth/me").status_code == 401
