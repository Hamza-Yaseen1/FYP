"""
Tests for Gmail connection lifecycle (User Story 3 — Disconnect / Revoke / Error).

Written FIRST (TDD). Must FAIL before T027-T028 implementation.

Covers:
- T025: Contract test — DELETE /connections/{id} triggers revoke + DB delete
- T026: Error state — set_connection_error flips status to 'error'
"""
import asyncio
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from bson import ObjectId

from models.connection import ConnectionStatus, Provider


# ──────────────────────────────────────────────────────────────
# T025: Contract test — DELETE revokes then deletes
# ──────────────────────────────────────────────────────────────


class TestDeleteRevoke:
    """DELETE /connections/{id} for a Gmail connection calls revoke
    before deleting the DB row."""

    def test_delete_gmail_connection_calls_revoke(self, client, sync_db):
        """Deleting a Gmail connection calls revoke_google_access with
        the encrypted refresh_token before removing the row."""
        from services.connection import ConnectionService
        from utils.encryption import encrypt

        # Register + login
        client.post("/auth/register", json={"name": "Revoke Tester", "email": "revoke@test.com", "password": "password123"})
        client.post("/auth/login", json={"email": "revoke@test.com", "password": "password123"})

        # Insert a Gmail connection directly
        user = sync_db.users.find_one({"email": "revoke@test.com"})
        uid = str(user["_id"])
        conn_id = ObjectId()
        encrypted_refresh = encrypt("real-refresh-token-123")
        sync_db.connections.insert_one({
            "_id": conn_id,
            "user_id": uid,
            "provider": "gmail",
            "status": "connected",
            "access_token": encrypt("access-abc"),
            "refresh_token": encrypted_refresh,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

        with patch("services.gmail.revoke_google_access", new_callable=AsyncMock) as mock_revoke:
            mock_revoke.return_value = True
            resp = client.delete(f"/connections/{conn_id}")
            assert resp.status_code == 204
            mock_revoke.assert_called_once_with(encrypted_refresh)

        # Row deleted
        assert sync_db.connections.find_one({"_id": conn_id}) is None

    def test_delete_gmail_connection_still_deletes_when_revoke_fails(self, client, sync_db):
        """Even if Google revoke fails, the DB row is still removed."""
        from services.connection import ConnectionService
        from utils.encryption import encrypt

        client.post("/auth/register", json={"name": "Revoke Tester 2", "email": "revoke2@test.com", "password": "password123"})
        client.post("/auth/login", json={"email": "revoke2@test.com", "password": "password123"})

        user = sync_db.users.find_one({"email": "revoke2@test.com"})
        uid = str(user["_id"])
        conn_id = ObjectId()
        encrypted_refresh = encrypt("token-for-revoke-fail")
        sync_db.connections.insert_one({
            "_id": conn_id,
            "user_id": uid,
            "provider": "gmail",
            "status": "connected",
            "access_token": encrypt("access-xyz"),
            "refresh_token": encrypted_refresh,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

        with patch("services.gmail.revoke_google_access", new_callable=AsyncMock) as mock_revoke:
            mock_revoke.return_value = False
            resp = client.delete(f"/connections/{conn_id}")
            assert resp.status_code == 204
            mock_revoke.assert_called_once_with(encrypted_refresh)

        # Still deleted
        assert sync_db.connections.find_one({"_id": conn_id}) is None

    def test_delete_non_gmail_connection_no_revoke(self, client, sync_db):
        """Deleting a non-Gmail connection skips the revoke call entirely."""
        from services.connection import ConnectionService
        from utils.encryption import encrypt

        client.post("/auth/register", json={"name": "WA Delete", "email": "wadelete@test.com", "password": "password123"})
        client.post("/auth/login", json={"email": "wadelete@test.com", "password": "password123"})

        user = sync_db.users.find_one({"email": "wadelete@test.com"})
        uid = str(user["_id"])
        conn_id = ObjectId()
        sync_db.connections.insert_one({
            "_id": conn_id,
            "user_id": uid,
            "provider": "whatsapp",
            "status": "connected",
            "access_token": encrypt("mock_at"),
            "refresh_token": encrypt("mock_rt"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

        with patch("services.gmail.revoke_google_access", new_callable=AsyncMock) as mock_revoke:
            resp = client.delete(f"/connections/{conn_id}")
            assert resp.status_code == 204
            mock_revoke.assert_not_called()

    def test_delete_other_users_connection_returns_404(self, client, sync_db):
        """SC-005: User B cannot delete User A's connection (user-scoped 404)."""
        from utils.encryption import encrypt

        # User A owns the connection
        client.post("/auth/register", json={"name": "Owner A", "email": "ownera@test.com", "password": "password123"})
        client.post("/auth/login", json={"email": "ownera@test.com", "password": "password123"})
        owner = sync_db.users.find_one({"email": "ownera@test.com"})
        owner_uid = str(owner["_id"])
        conn_id = ObjectId()
        sync_db.connections.insert_one({
            "_id": conn_id,
            "user_id": owner_uid,
            "provider": "gmail",
            "status": "connected",
            "access_token": encrypt("at-a"),
            "refresh_token": encrypt("rt-a"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

        # User B tries to delete A's connection
        client.post("/auth/register", json={"name": "Trespasser B", "email": "trespb@test.com", "password": "password123"})
        client.post("/auth/login", json={"email": "trespb@test.com", "password": "password123"})

        with patch("services.gmail.revoke_google_access", new_callable=AsyncMock) as mock_revoke:
            resp = client.delete(f"/connections/{conn_id}")
            assert resp.status_code == 404
            mock_revoke.assert_not_called()

        # Row still exists — owned by A
        doc = sync_db.connections.find_one({"_id": conn_id})
        assert doc is not None
        assert doc["user_id"] == owner_uid


# ──────────────────────────────────────────────────────────────
# T026: Error state — flip connection to 'error'
# ──────────────────────────────────────────────────────────────


class TestConnectionError:
    """Verify the error-state helper flips a connection properly."""

    def test_set_connection_error_flips_status(self, monkeypatch):
        """set_connection_error changes status to 'error' via update_one."""
        from services.connection import ConnectionService
        from test_threads import _FakeMessages

        _id = ObjectId()
        uid = "507f1f77bcf86cd799439011"
        conn = {
            "_id": _id,
            "user_id": uid,
            "provider": "gmail",
            "status": "connected",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        fake_coll = _FakeMessages([conn])

        class _FakeDb:
            def __getitem__(self, name):
                return fake_coll

        svc = ConnectionService(_FakeDb())

        result = asyncio.run(svc.set_connection_error(str(_id), uid))
        assert result is True
        assert conn["status"] == ConnectionStatus.ERROR.value

    def test_poller_sets_error_on_token_failure(self, monkeypatch):
        """When _ensure_access_token returns None, the poller marks error."""
        import services.gmail as gmail_mod

        conn_id = ObjectId()
        uid = "507f1f77bcf86cd799439011"
        conn_doc = {
            "_id": conn_id,
            "user_id": uid,
            "provider": "gmail",
            "status": "connected",
        }

        set_error_calls = []

        class _StubSvc:
            async def set_connection_error(self, cid, user):
                set_error_calls.append((cid, user))
                return True

        monkeypatch.setattr(gmail_mod, "ConnectionService", lambda db: _StubSvc())
        monkeypatch.setattr(gmail_mod, "_ensure_access_token", _async_none)

        asyncio.run(gmail_mod._poll_one_connection(conn_doc, str(conn_id), uid))

        assert len(set_error_calls) == 1
        assert set_error_calls[0][0] == str(conn_id)
        assert set_error_calls[0][1] == uid


async def _async_none(*args, **kwargs):
    return None
