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
