"""Link-rule tests (Day 25 US1 - tasks T007 + T008).

T007 unit cases: anchor minting, chain A->B->C, window boundary, normalize.
T008 labeled 30-pair set feeding SC-002 (false-link <= 5%) and SC-003
(recall >= 80%); both rates are computed and printed.

The deterministic link rule (same user + source + normalized sender + window)
is exercised against an in-memory fake collection - never motor under
asyncio.run (see test_orchestrator.py for the same convention).
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from services.threads import normalize_sender, resolve_and_stamp

T0 = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)


def _doc(**overrides):
    doc = {
        "_id": ObjectId(),
        "user_id": "u1",
        "source": "whatsapp",
        "sender": "Ali",
        "content": "test",
        "state": "active",
        "received_at": T0,
    }
    doc.update(overrides)
    return doc


def _set_path(doc, path, value):
    parts = path.split(".")
    node = doc
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def _push_path(doc, path, value):
    parts = path.split(".")
    node = doc
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node.setdefault(parts[-1], []).append(value)


class _FakeMessages:
    """In-memory stand-in for the motor messages collection, implementing the
    filters/sorts the Day 25 code uses: find_one, find_one_and_update, and
    find -> sort -> limit -> to_list."""

    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def _matches(self, doc, flt):
        for key, cond in flt.items():
            value = doc.get(key)
            if isinstance(cond, dict):
                if "$regex" in cond:
                    options = cond.get("$options", "")
                    flags = re.IGNORECASE if "i" in options else 0
                    if not re.match(cond["$regex"], str(value or ""), flags):
                        return False
                if "$gte" in cond and (value is None or not value >= cond["$gte"]):
                    return False
                if "$ne" in cond and value == cond["$ne"]:
                    return False
            elif value != cond:
                return False
        return True

    async def find_one(self, flt, sort=None):
        matched = [d for d in self.docs if self._matches(d, flt)]
        if sort:
            key, direction = sort[0]
            matched.sort(key=lambda d: d.get(key), reverse=(direction == -1))
        return matched[0] if matched else None

    async def find_one_and_update(self, flt, update, return_document=False):
        doc = await self.find_one(flt)
        if doc is None:
            return None
        for key, val in update.get("$set", {}).items():
            _set_path(doc, key, val)
        for key, val in update.get("$push", {}).items():
            _push_path(doc, key, val)
        return doc

    async def update_one(self, flt, update):
        doc = await self.find_one(flt)
        if doc is None:
            return _FakeUpdateResult(0)
        for key, val in update.get("$set", {}).items():
            _set_path(doc, key, val)
        for key, val in update.get("$push", {}).items():
            _push_path(doc, key, val)
        return _FakeUpdateResult(1)

    def find(self, flt):
        return _FakeCursor([d for d in self.docs if self._matches(d, flt)])


class _FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, spec):
        key, direction = spec[0]
        self._docs.sort(key=lambda d: d.get(key), reverse=(direction == -1))
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length):
        return self._docs[:length]


def _resolve(monkeypatch, docs, user_id, source, sender, at):
    fake = _FakeMessages(docs)
    monkeypatch.setattr("services.threads.messages_collection", fake)
    result = asyncio.run(resolve_and_stamp(user_id, source, sender, at))
    return result, fake


def test_normalize_sender_strips_and_lowercases():
    assert normalize_sender("  Ali  ") == "ali"
    assert normalize_sender("SARA") == "sara"
    assert normalize_sender("  Layla  ") == "layla"


def test_first_message_stands_alone(monkeypatch):
    (tid, cid), _ = _resolve(monkeypatch, [], "u1", "whatsapp", "Ali", T0)
    assert tid is None
    assert cid is None


def test_no_in_window_candidate_standalone(monkeypatch):
    anchor = _doc(received_at=T0 - timedelta(minutes=90))
    (tid, cid), _ = _resolve(monkeypatch, [anchor], "u1", "whatsapp", "Ali", T0)
    assert tid is None
    assert cid is None


def test_in_window_pair_mints_anchor_thread(monkeypatch):
    anchor = _doc(sender="Ali", received_at=T0)
    (tid, cid), fake = _resolve(
        monkeypatch, [anchor], "u1", "whatsapp", "Ali", T0 + timedelta(minutes=10)
    )
    assert tid == str(anchor["_id"])
    assert cid == str(anchor["_id"])
    assert fake.docs[0]["threadId"] == str(anchor["_id"])
    assert fake.docs[0]["conversationId"] == str(anchor["_id"])


def test_anchor_thread_inherited_by_third_message(monkeypatch):
    anchor = _doc(sender="Ali", received_at=T0)
    (tid, _), fake = _resolve(
        monkeypatch, [anchor], "u1", "whatsapp", "Ali", T0 + timedelta(minutes=10)
    )
    second = _doc(
        sender="Ali",
        received_at=T0 + timedelta(minutes=10),
        threadId=tid,
        conversationId=tid,
    )
    fake.docs.append(second)

    (tid_c, cid_c), _ = _resolve(
        monkeypatch,
        fake.docs,
        "u1",
        "whatsapp",
        "Ali",
        T0 + timedelta(minutes=45),
    )
    assert tid_c == str(anchor["_id"])
    assert cid_c == str(anchor["_id"])


def test_window_boundary_links_at_59_59_not_at_60_01(monkeypatch):
    anchor = _doc(sender="Ali", received_at=T0)
    (tid, _), _ = _resolve(
        monkeypatch,
        [anchor],
        "u1",
        "whatsapp",
        "Ali",
        T0 + timedelta(minutes=59, seconds=59),
    )
    assert tid is not None

    (tid_out, _), _ = _resolve(
        monkeypatch,
        [_doc(sender="Ali", received_at=T0)],
        "u1",
        "whatsapp",
        "Ali",
        T0 + timedelta(minutes=60, seconds=1),
    )
    assert tid_out is None


def test_different_sender_never_links(monkeypatch):
    anchor = _doc(sender="Ali", received_at=T0)
    (tid, cid), _ = _resolve(
        monkeypatch, [anchor], "u1", "whatsapp", "Sara", T0 + timedelta(minutes=5)
    )
    assert tid is None
    assert cid is None


def test_different_source_never_links(monkeypatch):
    anchor = _doc(sender="Ali", source="whatsapp", received_at=T0)
    (tid, cid), _ = _resolve(
        monkeypatch, [anchor], "u1", "gmail", "Ali", T0 + timedelta(minutes=5)
    )
    assert tid is None
    assert cid is None


# ── T008: labeled 30-pair quality bar (SC-002/SC-003) ──────────────────

LINKED_SENDERS = [
    "Ali", "Sara", "Ahmed", "Layla", "Omar", "Nadia", "Yusuf", "Huda",
    "Zaid", "Mariam", "Karim", "Samira", "Tariq", "Lina", "Hassan", "Noor",
    "Farah", "Rami", "Dina", "Ibrahim", "Amal", "Khaled", "Rasha", "Mazen",
]
SOURCES = ["whatsapp", "gmail", "simulate", "web"]


class _Pair:
    def __init__(self, anchor_sender, source, t0, follow_sender, follow_source, t1, expected):
        self.anchor_sender = anchor_sender
        self.source = source
        self.t0 = t0
        self.follow_sender = follow_sender
        self.follow_source = follow_source
        self.t1 = t1
        self.expected = expected


def _build_labeled_pairs():
    pairs = []
    for i, name in enumerate(LINKED_SENDERS):
        source = SOURCES[i % len(SOURCES)]
        t0 = T0 + timedelta(minutes=i)
        follow_sender = name.lower() if i % 3 == 0 else name
        t1 = t0 + timedelta(minutes=(1 + (i * 7) % 55))
        pairs.append(_Pair(name, source, t0, follow_sender, source, t1, True))

    negative = [
        _Pair("Ali", "whatsapp", T0, "Sara", "whatsapp", T0 + timedelta(minutes=5), False),
        _Pair("Omar", "whatsapp", T0, "Omar", "gmail", T0 + timedelta(minutes=5), False),
        _Pair("Layla", "whatsapp", T0, "Layla", "whatsapp", T0 + timedelta(minutes=61), False),
        _Pair("Rami", "simulate", T0, "Rami", "simulate", T0 + timedelta(minutes=120), False),
        _Pair("Huda", "web", T0, "Nadia", "gmail", T0 + timedelta(minutes=8), False),
        _Pair("Mariam", "whatsapp", T0, "Mariam", "whatsapp", T0 + timedelta(minutes=60, seconds=1), False),
    ]
    return pairs + negative


LABELED_PAIRS = _build_labeled_pairs()


def test_labeled_30_pairs(monkeypatch):
    assert len(LABELED_PAIRS) == 30
    expected_true = [p for p in LABELED_PAIRS if p.expected]
    correct = 0
    false_links = 0

    for p in LABELED_PAIRS:
        anchor = _doc(sender=p.anchor_sender, source=p.source, received_at=p.t0)
        (tid, _), _ = _resolve(
            monkeypatch, [anchor], "u1", p.follow_source, p.follow_sender, p.t1
        )
        if p.expected:
            if tid == str(anchor["_id"]):
                correct += 1
        elif tid is not None:
            false_links += 1

    total_linked = correct + false_links
    recall = correct / len(expected_true)
    false_rate = false_links / total_linked if total_linked else 0.0
    print(
        f"labeled-30-pairs: recall={recall:.2%} "
        f"false_link_rate={false_rate:.2%} (correct={correct}, "
        f"false_links={false_links}, expected_true={len(expected_true)})"
    )
    assert false_links <= 1
    assert false_rate <= 0.05
    assert recall >= 0.80


def test_media_only_message_still_gets_identity(monkeypatch):
    anchor = _doc(sender="Ali", received_at=T0, content="")
    (tid, _), _ = _resolve(
        monkeypatch, [anchor], "u1", "whatsapp", "Ali", T0 + timedelta(minutes=3)
    )
    assert tid == str(anchor["_id"])


def test_latest_consecutive_arrival_wins_over_older_unanchored(monkeypatch):
    """EC-13: the latest in-window arrival decides linkage — an older,
    unanchored candidate is never re-selected as the fresh-anchor target, so
    a parallel strand cannot hijack an established thread."""
    older = _doc(sender="Ali", received_at=T0)
    latest = _doc(
        sender="Ali",
        threadId=str(older["_id"]),
        conversationId=str(older["_id"]),
        received_at=T0 + timedelta(minutes=20),
    )
    (tid, cid), _ = _resolve(
        monkeypatch,
        [older, latest],
        "u1",
        "whatsapp",
        "Ali",
        T0 + timedelta(minutes=30),
    )
    assert tid == str(older["_id"])
    assert cid == str(older["_id"])


# ── T027: US5 two-user isolation ───────────────────────────────────────────


def test_two_users_same_sender_source_each_get_own_thread(monkeypatch):
    """SC-007: user A and user B messaging Ali on the same channel in-window
    each get their own thread; neither thread contains the other's messages."""
    anchor_a = _doc(user_id="u1", sender="Ali", received_at=T0)
    anchor_b = _doc(user_id="u2", sender="Ali", received_at=T0)

    (tid_a, cid_a), fake = _resolve(
        monkeypatch, [anchor_a, anchor_b], "u1", "whatsapp", "Ali", T0 + timedelta(minutes=10)
    )
    (tid_b, cid_b), _ = _resolve(
        monkeypatch, fake.docs, "u2", "whatsapp", "Ali", T0 + timedelta(minutes=10)
    )

    assert tid_a == str(anchor_a["_id"])
    assert cid_a == str(anchor_a["_id"])
    assert tid_b == str(anchor_b["_id"])
    assert cid_b == str(anchor_b["_id"])
    assert tid_a != tid_b

    a_thread = [d for d in fake.docs if d.get("threadId") == tid_a]
    b_thread = [d for d in fake.docs if d.get("threadId") == tid_b]
    assert all(d["user_id"] == "u1" for d in a_thread)
    assert all(d["user_id"] == "u2" for d in b_thread)