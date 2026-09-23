"""
Tests for Gmail email ingest (User Story 2 — Receive New Emails).

Written FIRST (TDD). Must FAIL before corresponding implementation tasks
T019-T024 are complete (T019-T021 already implemented in services/gmail.py;
T022-T024 remain).

Tests cover:
- T017: Unit tests for normalize_email (MIME parsing)
- T018: Integration test for poller → ingest → dedup
"""
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from unittest.mock import patch, AsyncMock, MagicMock

import asyncio
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

import pytest


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

USER_ID = "507f1f77bcf86cd799439011"


def _make_raw_message(
    message_id: str = "msg-abc-123",
    sender: str = "Teacher <teacher@example.com>",
    subject: str = "Homework Due Friday",
    body_text: str = "Please submit your report by Friday.",
    body_html: str = "<p>Please submit your report by Friday.</p>",
    multipart: bool = True,
) -> dict:
    """Build a fake Gmail API message dict with format=raw."""
    if multipart:
        msg = MIMEText(body_text, "plain")
        html_part = MIMEText(body_html, "html")
        from email.mime.multipart import MIMEMultipart
        outer = MIMEMultipart("alternative")
        outer["From"] = sender
        outer["Subject"] = subject
        outer.attach(msg)
        outer.attach(html_part)
    else:
        msg = MIMEText(body_text, "plain")
        msg["From"] = sender
        msg["Subject"] = subject
        outer = msg

    raw_bytes = outer.as_bytes()
    encoded_raw = urlsafe_b64encode(raw_bytes).decode("ascii")

    return {
        "id": message_id,
        "raw": encoded_raw,
        "snippet": body_text[:40],
    }


def _make_html_only_message(
    message_id: str = "msg-html-1",
    sender: str = "Alerts <alerts@example.com>",
    subject: str = "HTML Only",
    body_html: str = "<html><body><h1>Hello</h1><p>World</p></body></html>",
) -> dict:
    from email.mime.multipart import MIMEMultipart
    outer = MIMEMultipart("alternative")
    outer["From"] = sender
    outer["Subject"] = subject
    outer.attach(MIMEText(body_html, "html"))
    raw_bytes = outer.as_bytes()
    encoded_raw = urlsafe_b64encode(raw_bytes).decode("ascii")
    return {
        "id": message_id,
        "raw": encoded_raw,
    }


def _make_empty_body_message(
    message_id: str = "msg-empty-1",
    sender: str = "NoBody <nobody@example.com>",
    subject: str = "Empty",
) -> dict:
    """Message with no body payload (raw is empty string)."""
    return {
        "id": message_id,
        "payload": {
            "raw": "",
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
            ],
        },
    }


def _make_attachment_only_message(
    message_id: str = "msg-attach-1",
    sender: str = "Sender <s@example.com>",
    subject: str = "File attached",
    body_text: str = "See attached.",
) -> dict:
    """Multipart with text/plain + an attachment part."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    outer = MIMEMultipart()
    outer["From"] = sender
    outer["Subject"] = subject
    outer.attach(MIMEText(body_text, "plain"))
    # Fake attachment
    from email.mime.base import MIMEBase
    att = MIMEBase("application", "pdf")
    att.set_payload(b"%PDF-1.4 fake")
    att.add_header("Content-Disposition", "attachment", filename="report.pdf")
    outer.attach(att)

    raw_bytes = outer.as_bytes()
    encoded_raw = urlsafe_b64encode(raw_bytes).decode("ascii")
    return {
        "id": message_id,
        "raw": encoded_raw,
    }


# ──────────────────────────────────────────────────────────────
# T017: Unit tests — normalize_email
# ──────────────────────────────────────────────────────────────


class TestNormalizeEmail:
    """Verify MIME → canonical format conversion."""

    def test_plain_text_body(self):
        from services.gmail import normalize_email

        raw = _make_raw_message(
            body_text="Hello world",
            body_html="<p>Hello world</p>",
            multipart=True,
        )
        result = normalize_email(raw)
        assert result is not None
        assert result["content"] == "Hello world"
        assert result["sender"] == "Teacher <teacher@example.com>"
        assert result["subject"] == "Homework Due Friday"
        assert result["external_message_id"] == "msg-abc-123"

    def test_html_fallback_when_no_plain(self):
        from services.gmail import normalize_email

        raw = _make_html_only_message(body_html="<h1>Hello</h1><p>World</p>")
        result = normalize_email(raw)
        assert result is not None
        # HTML should be stripped to visible text
        assert "Hello" in result["content"]
        assert "World" in result["content"]
        assert "<h1>" not in result["content"]

    def test_empty_body_returns_empty_string(self):
        from services.gmail import normalize_email

        raw = _make_empty_body_message()
        result = normalize_email(raw)
        assert result is not None
        assert result["content"] == ""

    def test_sender_display_name_preserved(self):
        from services.gmail import normalize_email

        raw = _make_raw_message(sender="Dr. Smith <smith@uni.edu>")
        result = normalize_email(raw)
        assert result["sender"] == "Dr. Smith <smith@uni.edu>"

    def test_bare_address_sender(self):
        from services.gmail import normalize_email

        raw = _make_raw_message(sender="alert@example.com")
        result = normalize_email(raw)
        assert result["sender"] == "alert@example.com"

    def test_attachment_parts_ignored(self):
        from services.gmail import normalize_email

        raw = _make_attachment_only_message(body_text="See attached.")
        result = normalize_email(raw)
        assert result is not None
        assert result["content"] == "See attached."

    def test_subject_optional(self):
        from services.gmail import normalize_email

        raw = _make_empty_body_message(subject="")
        result = normalize_email(raw)
        assert result is not None
        assert result["subject"] == ""

    def test_missing_message_id_returns_none(self):
        from services.gmail import normalize_email

        assert normalize_email({"payload": {"raw": ""}}) is None
        assert normalize_email({"raw": "abc"}) is None

    def test_legacy_payload_raw_still_supported(self):
        """Some proxies/tests still return raw MIME under payload.raw."""
        from services.gmail import normalize_email

        raw = _make_raw_message(message_id="legacy-1", body_text="Legacy body")
        legacy = {"id": raw["id"], "payload": {"raw": raw["raw"]}}
        result = normalize_email(legacy)
        assert result is not None
        assert result["content"] == "Legacy body"

    def test_returns_all_canonical_fields(self):
        from services.gmail import normalize_email

        raw = _make_raw_message()
        result = normalize_email(raw)
        assert result is not None
        for key in ("sender", "content", "subject", "external_message_id"):
            assert key in result

    def test_top_level_raw_is_real_gmail_shape(self):
        """The Gmail API (format=raw) puts the base64 MIME in the TOP-LEVEL
        ``raw`` field — this is the regression that caused empty bodies."""
        from services.gmail import normalize_email

        raw = _make_raw_message(
            message_id="real-shape-1",
            sender="Boss <boss@corp.com>",
            subject="Quarterly numbers",
            body_text="Please send the final numbers tomorrow.",
        )
        assert "payload" not in raw and "raw" in raw
        result = normalize_email(raw)
        assert result is not None
        assert result["content"] == "Please send the final numbers tomorrow."
        assert result["sender"] == "Boss <boss@corp.com>"
        assert result["subject"] == "Quarterly numbers"


# ──────────────────────────────────────────────────────────────
# T018: Integration test — poller → ingest → dedup
# ──────────────────────────────────────────────────────────────


class _FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _FakeMessages:
    """In-memory stand-in for the motor messages collection used by
    webhook_ingest.ingest_message: insert_one + find_one, with a simulated
    unique-index duplicate raise so the dedup path is exercised."""

    def __init__(self, docs=None):
        self.docs = list(docs or [])
        self.next_id = ObjectId()

    def _insert(self, doc):
        existing = [d for d in self.docs if d.get("external_message_id") == doc.get("external_message_id") and doc.get("external_message_id")]
        if existing:
            raise DuplicateKeyError("dup", 11000)
        self.docs.append(doc)
        return doc["_id"]

    async def insert_one(self, doc):
        _id = self._insert(doc)
        return _FakeInsertResult(_id)

    async def find_one(self, flt):
        for d in self.docs:
            if all(d.get(k) == v for k, v in flt.items()):
                return d
        return None

    async def update_one(self, flt, update):
        return None


class TestPollerIngest:
    """Verify the poller path produces stored messages with AI analysis."""

    def _patch_env(self, monkeypatch):
        """Monkeypatch collection + AI/thread services so no real motor/LLM."""
        from services import webhook_ingest

        fake = _FakeMessages()
        monkeypatch.setattr(webhook_ingest, "messages_collection", fake)

        async def _noop_process(*args, **kwargs):
            return {"priority": "normal", "provider": "test"}

        async def _noop_resolve(*args, **kwargs):
            return None, None

        monkeypatch.setattr(webhook_ingest, "process_message", _noop_process)
        monkeypatch.setattr(webhook_ingest, "resolve_and_stamp", _noop_resolve)
        return fake

    def test_normalize_then_ingest_produces_message(self):
        """End-to-end: raw Gmail msg → normalize → fields present."""
        from services.gmail import normalize_email

        raw = _make_raw_message(
            message_id="poll-1",
            sender="Boss <boss@company.com>",
            subject="Q3 Report",
            body_text="Please review the Q3 numbers.",
        )
        norm = normalize_email(raw)
        assert norm is not None
        assert norm["external_message_id"] == "poll-1"
        assert norm["sender"] == "Boss <boss@company.com>"
        assert norm["subject"] == "Q3 Report"
        assert "Q3" in norm["content"]

    def test_duplicate_external_message_id_ignored(self, monkeypatch):
        """ingest_message returns existing id on duplicate (dedup works)."""
        from services.webhook_ingest import ingest_message

        fake = self._patch_env(monkeypatch)
        uid = USER_ID
        eid = "dup-test-001"

        msg_id_1 = asyncio.run(
            ingest_message(
                user_id=uid, source="gmail", sender="dup@test.com",
                content="First", external_message_id=eid, subject="Dup",
            )
        )
        assert msg_id_1 is not None

        # Simulate unique index: force duplicate insertion to raise
        from pymongo.errors import DuplicateKeyError
        fake._insert = lambda doc: (_ for _ in ()).throw(
            DuplicateKeyError("dup", 11000)
        )

        msg_id_2 = asyncio.run(
            ingest_message(
                user_id=uid, source="gmail", sender="dup@test.com",
                content="Second", external_message_id=eid, subject="Dup",
            )
        )
        assert msg_id_2 == msg_id_1  # same id, no duplicate

    def test_subject_stored_when_provided(self, monkeypatch):
        """Subject is stored on the message doc when passed to ingest_message."""
        from services.webhook_ingest import ingest_message

        fake = self._patch_env(monkeypatch)
        uid = USER_ID
        asyncio.run(
            ingest_message(
                user_id=uid, source="gmail", sender="sub@test.com",
                content="Body", subject="Important Subject",
            )
        )
        doc = fake.docs[0]
        assert doc.get("subject") == "Important Subject"
        assert doc["source"] == "gmail"

    def test_subject_absent_when_not_provided(self, monkeypatch):
        """Subject key is absent on messages without it (backward compat)."""
        from services.webhook_ingest import ingest_message

        fake = self._patch_env(monkeypatch)
        uid = USER_ID
        asyncio.run(
            ingest_message(
                user_id=uid, source="whatsapp", sender="wa@test.com",
                content="Body",
            )
        )
        doc = fake.docs[0]
        assert "subject" not in doc


# ──────────────────────────────────────────────────────────────
# Fetch-coverage: pagination + full first scan + found/saved stats
# ──────────────────────────────────────────────────────────────


class _FakeGmailMessages:
    """Messages store with count_documents for poller fetch-coverage tests."""

    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def _matches(self, doc, flt):
        for k, v in flt.items():
            if isinstance(v, dict) and "$in" in v:
                if doc.get(k) not in v["$in"]:
                    return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    async def insert_one(self, doc):
        # Mirror the real unique {user_id, external_message_id} index so the
        # duplicate path (return existing id) is exercised like production.
        existing = [
            d for d in self.docs
            if d.get("user_id") == doc.get("user_id")
            and doc.get("external_message_id")
            and d.get("external_message_id") == doc.get("external_message_id")
        ]
        if existing:
            raise DuplicateKeyError("dup", 11000)
        self.docs.append(doc)
        return _FakeInsertResult(doc["_id"])

    async def find_one(self, flt):
        for d in self.docs:
            if self._matches(d, flt):
                return d
        return None

    async def update_one(self, flt, update):
        return None

    async def count_documents(self, flt):
        return sum(1 for d in self.docs if self._matches(d, flt))


class _FakeGmailConnections:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, flt):
        for d in self.docs:
            if all(d.get(k) == v for k, v in flt.items()):
                return d
        return None

    async def update_one(self, flt, update):
        for d in self.docs:
            if all(d.get(k) == v for k, v in flt.items()):
                for k, v in update.get("$set", {}).items():
                    d[k] = v
        return None


class _FakeGmailDb:
    def __init__(self, messages, connections):
        self._messages = messages
        self._connections = connections

    def __getitem__(self, name):
        if name == "messages":
            return self._messages
        if name == "connections":
            return self._connections
        raise KeyError(name)


class TestPollerFetchCoverage:
    """Verify the poller pulls ALL inbox emails — pagination, no narrow
    ``after:`` filter on the first scan, and found-vs-saved accounting."""

    USER_ID = "507f1f77bcf86cd799439011"

    def _build_conn(self):
        conn = {
            "_id": ObjectId(),
            "user_id": self.USER_ID,
            "provider": "gmail",
            "status": "connected",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        return conn

    def _patch_poll_deps(self, monkeypatch, message_ids=None, conn=None, seed_ids=None):
        """Fake out google + motor so the poller runs under asyncio.run."""
        import services.gmail as gmail_mod
        import services.webhook_ingest as webhook_ingest_mod

        captured = {}

        async def _token(*a, **k):
            return "fresh-token"

        async def _list(access_token, after_epoch=None, **k):
            captured["after_epoch"] = after_epoch
            return list(message_ids or [])

        async def _raw(token, mid):
            return {"id": mid, "payload": {"raw": ""}}

        def _norm(raw):
            return {
                "sender": "testsender@example.com",
                "content": f"body {raw['id']}",
                "subject": f"subj {raw['id']}",
                "external_message_id": raw["id"],
            }

        async def _noop_process(*a, **k):
            return {"priority": "normal", "provider": "test"}

        async def _noop_resolve(*a, **k):
            return None, None

        messages = _FakeGmailMessages()
        for sid in seed_ids or []:
            messages.docs.append({
                "_id": ObjectId(),
                "user_id": self.USER_ID,
                "source": "gmail",
                "external_message_id": sid,
                "status": "unread",
            })
        connections = _FakeGmailConnections([conn] if conn else [])

        monkeypatch.setattr(gmail_mod, "db", _FakeGmailDb(messages, connections))
        monkeypatch.setattr(gmail_mod, "_ensure_access_token", _token)
        monkeypatch.setattr(gmail_mod, "list_new_message_ids", _list)
        monkeypatch.setattr(gmail_mod, "get_message_raw", _raw)
        monkeypatch.setattr(gmail_mod, "normalize_email", _norm)
        monkeypatch.setattr(webhook_ingest_mod, "messages_collection", messages)
        monkeypatch.setattr(webhook_ingest_mod, "process_message", _noop_process)
        monkeypatch.setattr(webhook_ingest_mod, "resolve_and_stamp", _noop_resolve)
        return captured, messages

    def test_first_poll_is_full_inbox_scan_and_saves_all(self, monkeypatch):
        """No `after:` filter on first poll → older test emails are eligible."""
        from services.gmail import _poll_one_connection

        conn = self._build_conn()
        captured, messages = self._patch_poll_deps(
            monkeypatch, message_ids=["m1", "m2"], conn=conn
        )

        summary = asyncio.run(
            _poll_one_connection(conn, str(conn["_id"]), self.USER_ID)
        )

        assert captured["after_epoch"] is None
        assert summary == {
            "found": 2,
            "fetched": 2,
            "saved": 2,
            "duplicates": 0,
            "failed": 0,
        }
        assert len(messages.docs) == 2
        assert {d["external_message_id"] for d in messages.docs} == {"m1", "m2"}
        # Watermark advanced so the next poll is a cheap incremental scan.
        assert "last_fetched_at" in conn

    def test_poll_counts_and_skips_existing_duplicates(self, monkeypatch):
        """Already-stored emails are counted as duplicates, not double-saved."""
        from services.gmail import _poll_one_connection

        conn = self._build_conn()
        _, messages = self._patch_poll_deps(
            monkeypatch, message_ids=["m1", "m2"], conn=conn, seed_ids=["m1"]
        )

        summary = asyncio.run(
            _poll_one_connection(conn, str(conn["_id"]), self.USER_ID)
        )

        assert summary["found"] == 2
        assert summary["duplicates"] == 1
        assert summary["saved"] == 1
        assert summary["failed"] == 0
        assert len(messages.docs) == 2  # m1 + newly saved m2

    def test_incremental_poll_uses_after_watermark(self, monkeypatch):
        """Later polls narrow with `after:<epoch>` — no full re-scan."""
        from services.gmail import _poll_one_connection

        conn = self._build_conn()
        conn["last_fetched_at"] = datetime(2024, 1, 1, tzinfo=timezone.utc)
        captured, _ = self._patch_poll_deps(
            monkeypatch, message_ids=["m1"], conn=conn
        )

        asyncio.run(_poll_one_connection(conn, str(conn["_id"]), self.USER_ID))

        assert captured["after_epoch"] == int(
            datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
        )

    def test_list_message_ids_paginates_until_exhausted(self, monkeypatch):
        """nextPageToken is followed so a poll never truncates at one page."""
        import json

        import services.gmail as gmail_mod

        pages = [
            {"messages": [{"id": "p1a"}, {"id": "p1b"}], "nextPageToken": "tok2"},
            {"messages": [{"id": "p2a"}], "nextPageToken": "tok3"},
            {"messages": [{"id": "p3a"}], "nextPageToken": None},
        ]
        calls = []

        class _Resp:
            def __init__(self, status_code, body):
                self.status_code = status_code
                self.text = json.dumps(body)
                self._body = body

            def json(self):
                return self._body

        class _FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def get(self, url, headers=None, params=None):
                calls.append(params)
                return _Resp(200, pages[len(calls) - 1])

        monkeypatch.setattr(gmail_mod.httpx, "AsyncClient", lambda: _FakeClient())

        ids = asyncio.run(
            gmail_mod.list_new_message_ids(
                "tk", after_epoch=1234567890, max_results=100, max_pages=10
            )
        )

        assert ids == ["p1a", "p1b", "p2a", "p3a"]
        assert len(calls) == 3
        assert calls[0]["q"] == "in:inbox after:1234567890"
        assert "pageToken" not in calls[0]
        assert calls[1]["pageToken"] == "tok2"
        assert calls[2]["pageToken"] == "tok3"

    def test_list_message_ids_full_scan_omits_after_filter(self, monkeypatch):
        """Full-scan query is just `in:inbox` — older emails are included."""
        import json

        import services.gmail as gmail_mod

        calls = []

        class _Resp:
            def __init__(self, body):
                self.status_code = 200
                self.text = "ok"
                self._body = body

            def json(self):
                return self._body

        class _FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def get(self, url, headers=None, params=None):
                calls.append(params)
                return _Resp({"messages": [{"id": "z1"}]})

        monkeypatch.setattr(gmail_mod.httpx, "AsyncClient", lambda: _FakeClient())

        asyncio.run(gmail_mod.list_new_message_ids("tk", after_epoch=None))

        assert calls[0]["q"] == "in:inbox"
        assert "after" not in calls[0]["q"]


class TestManualRefreshEndpoint:
    """POST /connections/gmail/refresh — forces a full scan on demand."""

    def _register(self, client, email="refresh@test.com"):
        res = client.post(
            "/auth/register",
            json={"name": "Refresh Tester", "email": email, "password": "password123"},
        )
        assert res.status_code == 201
        return res.json()["id"]

    def test_no_connected_gmail_returns_404(self, client):
        self._register(client)
        resp = client.post("/connections/gmail/refresh")
        assert resp.status_code == 404

    def test_refresh_runs_full_poll_and_reports_stats(self, client, sync_db, monkeypatch):
        user_id = self._register(client)
        conn_id = ObjectId()
        sync_db.connections.insert_one({
            "_id": conn_id,
            "user_id": user_id,
            "provider": "gmail",
            "status": "connected",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

        called = {}

        async def fake_poll(conn_doc, conn_id_, user_id_, force_full_scan=False):
            called["force_full_scan"] = force_full_scan
            return {"found": 3, "fetched": 3, "saved": 3, "duplicates": 0, "failed": 0}

        monkeypatch.setattr("routes.gmail._poll_one_connection", fake_poll)

        resp = client.post("/connections/gmail/refresh")
        assert resp.status_code == 200
        assert called["force_full_scan"] is True
        body = resp.json()
        assert body["connection_id"] == str(conn_id)
        assert body["found"] == 3
        assert body["saved"] == 3
        assert body["duplicates"] == 0

    def test_refresh_requires_auth(self, client):
        resp = client.post("/connections/gmail/refresh")
        assert resp.status_code == 401
