from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from bson import ObjectId

from services.security import (
    JWT_SECRET,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)

REGISTER_BODY = {
    "name": "Hamza Yaseen",
    "email": "Hamza@Example.com",
    "password": "s3cretpass",
}


def register(client, **overrides):
    body = {**REGISTER_BODY, **overrides}
    return client.post("/auth/register", json=body)


class TestRegisterContract:
    def test_register_success(self, client):
        res = register(client)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == REGISTER_BODY["name"]
        assert data["email"] == "hamza@example.com"
        assert "created_at" in data
        assert "password_hash" not in data
        assert "password" not in data

        cookie = res.headers.get("set-cookie", "")
        assert "cai_token=" in cookie
        assert "httponly" in cookie.lower()
        assert "samesite=lax" in cookie.lower()

    def test_register_duplicate_email_409(self, client):
        assert register(client).status_code == 201
        res = register(client, name="Someone Else")
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"]

    def test_register_duplicate_case_insensitive_409(self, client):
        assert register(client).status_code == 201
        res = register(client, email="hamza@example.com")
        assert res.status_code == 409

    def test_register_short_password_422(self, client):
        res = register(client, password="short")
        assert res.status_code == 422

    def test_register_invalid_email_422(self, client):
        res = register(client, email="not-an-email")
        assert res.status_code == 422

    @pytest.mark.parametrize("missing", ["name", "email", "password"])
    def test_register_missing_field_422(self, client, missing):
        body = {k: v for k, v in REGISTER_BODY.items() if k != missing}
        res = client.post("/auth/register", json=body)
        assert res.status_code == 422


class TestSecurityUnit:
    def test_hash_verify_roundtrip(self):
        hashed = hash_password("s3cretpass")
        assert verify_password("s3cretpass", hashed) is True
        assert verify_password("wrongpass", hashed) is False

    def test_hashes_are_salted(self):
        assert hash_password("s3cretpass") != hash_password("s3cretpass")

    def test_stored_hash_is_not_plaintext(self):
        hashed = hash_password("s3cretpass")
        assert "s3cretpass" not in hashed

    def test_token_roundtrip(self):
        token = create_access_token("665f0abc1234")
        assert decode_token(token) == "665f0abc1234"

    def test_tampered_token_rejected(self):
        token = create_access_token("665f0abc1234")
        assert decode_token(token + "x") is None

    def test_expired_token_rejected(self):
        now = datetime.now(timezone.utc) - timedelta(days=8)
        payload = {"sub": "abc123", "iat": now, "exp": now + timedelta(days=7)}
        expired = pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
        assert decode_token(expired) is None


class TestLoginContract:
    def test_login_success(self, client):
        register(client)
        res = client.post(
            "/auth/login",
            json={"email": "hamza@example.com", "password": "s3cretpass"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "hamza@example.com"
        assert data["name"] == REGISTER_BODY["name"]
        assert "password_hash" not in data
        cookie = res.headers.get("set-cookie", "")
        assert "cai_token=" in cookie
        assert "httponly" in cookie.lower()

    def test_login_wrong_password_generic_401(self, client):
        register(client)
        res = client.post(
            "/auth/login",
            json={"email": "hamza@example.com", "password": "wrongpass1"},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Invalid email or password."}

    def test_login_unknown_email_identical_error(self, client):
        register(client)
        res = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "whatever123"},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Invalid email or password."}

    def test_me_returns_current_user(self, client):
        register(client)
        res = client.get("/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "hamza@example.com"
        assert "password_hash" not in data

    def test_me_without_session_401(self, client):
        res = client.get("/auth/me")
        assert res.status_code == 401

    def test_logout_clears_cookie_and_session(self, client):
        register(client)
        assert client.get("/auth/me").status_code == 200
        res = client.post("/auth/logout")
        assert res.status_code == 204
        cookie = res.headers.get("set-cookie", "")
        assert "Max-Age=0" in cookie or "max-age=0" in cookie
        assert client.get("/auth/me").status_code == 401

class TestIsolation:
    @pytest.fixture(autouse=True)
    def _mock_ai(self, monkeypatch):
        async def fake_analyze(content, message_id=None, user_id=None, thread_id=None):
            return {
                "priority": "normal",
                "confidence": 0.9,
                "explanation": "stubbed",
                "summary": "stubbed summary",
                "recommended_action": "",
                "recommended_actions": [],
                "tasks_extracted": [],
                "deadlines": [],
                "provider": "stub",
                "analyzed_at": datetime.now(timezone.utc),
                "status": "completed",
            }

        monkeypatch.setattr("services.webhook_ingest.process_message", fake_analyze)

    def _register(self, client, email):
        res = client.post(
            "/auth/register",
            json={"name": "Iso User", "email": email, "password": "s3cretpass"},
        )
        assert res.status_code == 201
        return res.json()["id"], res.cookies.get("cai_token")

    @staticmethod
    def _switch_session(client, token):
        client.cookies.clear()
        if token:
            client.cookies.set("cai_token", token)

    @staticmethod
    def _message_body(content):
        return {"sender": "Test Contact", "content": content, "source": "whatsapp"}

    def test_messages_isolated_between_users(self, client, sync_db):
        uid_a, token_a = self._register(client, "iso-a@example.com")
        res_a = client.post("/messages", json=self._message_body("A secret note"))
        assert res_a.status_code == 201
        msg_a_id = res_a.json()["id"]

        _, token_b = self._register(client, "iso-b@example.com")
        assert token_b != token_a
        assert client.post("/messages", json=self._message_body("B own note")).status_code == 201

        listing = client.get("/messages")
        assert listing.status_code == 200
        assert all(
            m["id"] != msg_a_id for m in listing.json()["messages"]
        )

        assert client.get(f"/messages/{msg_a_id}").status_code == 404
        assert client.put(f"/messages/{msg_a_id}", json={"status": "read"}).status_code == 404
        assert client.delete(f"/messages/{msg_a_id}").status_code == 404

        doc = sync_db.messages.find_one({"_id": ObjectId(msg_a_id)})
        assert doc is not None
        assert doc["content"] == "A secret note"
        assert doc["status"] == "unread"
        assert doc["user_id"] == uid_a

        self._switch_session(client, token_a)
        assert client.get(f"/messages/{msg_a_id}").status_code == 200

    def test_tasks_isolated_between_users(self, client, sync_db):
        uid_a, token_a = self._register(client, "iso-ta@example.com")
        now = datetime.now(timezone.utc)
        task_id = sync_db.tasks.insert_one(
            {
                "user_id": uid_a,
                "title": "A private task",
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
        ).inserted_id

        self._register(client, "iso-tb@example.com")

        listing = client.get("/tasks")
        assert listing.status_code == 200
        assert all(t["id"] != str(task_id) for t in listing.json())

        status_res = client.put(
            f"/tasks/{task_id}/status", json={"status": "completed"}
        )
        assert status_res.status_code == 404
        assert client.delete(f"/tasks/{task_id}").status_code == 404
        assert sync_db.tasks.find_one({"_id": task_id})["status"] == "pending"

        self._switch_session(client, token_a)
        assert any(t["id"] == str(task_id) for t in client.get("/tasks").json())

    def test_data_routes_require_session(self, client):
        self._switch_session(client, None)

        assert client.get("/messages").status_code == 401
        assert client.post("/messages", json=self._message_body("x")).status_code == 401
        assert client.get("/tasks").status_code == 401
        oid = "507f1f77bcf86cd799439011"
        assert (
            client.put(f"/tasks/{oid}/status", json={"status": "completed"}).status_code
== 401
        )
        assert client.delete(f"/tasks/{oid}").status_code == 401
        assert (
            client.post(
                "/webhooks/whatsapp", json={"sender": "s", "message": "m"}
            ).status_code
            == 403
        )

class TestProtectedSurface:
    def test_anonymous_message_detail_401(self, client):
        res = client.get("/messages/507f1f77bcf86cd799439011")
        assert res.status_code == 401

    def test_health_remains_public(self, client):
        res = client.get("/health")
        assert res.status_code == 200

    def test_logout_ends_session_in_browser(self, client):
        client.post(
            "/auth/register",
            json={"name": "Surf User", "email": "surf@example.com", "password": "s3cretpass"},
        )
        assert client.get("/auth/me").status_code == 200

        res = client.post("/auth/logout")
        assert res.status_code == 204

        client.cookies.clear()
        assert client.get("/auth/me").status_code == 401


class TestAuthCoverage:
    PUBLIC_ROUTES = {
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("POST", "/auth/logout"),
        ("GET", "/auth/google/callback"),
        ("GET", "/health"),
        ("GET", "/webhooks/whatsapp"),
        ("POST", "/webhooks/whatsapp"),
    }
    API_PREFIXES = ("/auth", "/messages", "/tasks", "/webhooks", "/health")

    def test_all_api_routes_require_session_except_allowlist(self):
        from fastapi.routing import APIRoute

        from dependencies import get_current_user
        from main import app

        def uses_current_user(route):
            stack = [route.dependant]
            while stack:
                dep = stack.pop()
                if dep.call is get_current_user:
                    return True
                stack.extend(dep.dependencies)
            return False

        checked = []
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue
            if not route.path.startswith(self.API_PREFIXES):
                continue
            for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
                if (method, route.path) in self.PUBLIC_ROUTES:
                    continue
                assert uses_current_user(route), (
                    f"{method} {route.path} lacks session requirement"
                )
                checked.append((method, route.path))

        assert len(checked) >= 10, f"audit covered only {len(checked)} routes"
