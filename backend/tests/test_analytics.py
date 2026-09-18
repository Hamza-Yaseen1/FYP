"""Analytics service tests (Day 28).

T009: aggregation counts (total / by_priority / by_source) are computed from
live, user-scoped data. Uses an in-memory fake collection that supports the
exact pipeline stages the analytics service emits ($match, $count, $group) —
never motor under asyncio.run (see test_threads.py / test_orchestrator.py for
the same convention).
"""

import asyncio
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from services.analytics import build_analytics_response
import services.analytics as analytics_module

NOW = datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc)


def _doc(**overrides):
    doc = {
        "_id": ObjectId(),
        "user_id": "u1",
        "source": "whatsapp",
        "sender": "Ali",
        "content": "test",
        "state": "active",
        "received_at": NOW,
    }
    doc.update(overrides)
    return doc


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    async def to_list(self, length):
        return self._docs[:length]


class _FakeAnalyticsMessages:
    """In-memory (messages|tasks) stand-in implementing just the pipeline
    stages analytics uses: $match, $count, and $group ({_id: $field, count:
    {$sum: 1}})."""

    def __init__(self, docs=None):
        self.docs = list(docs or [])

    @staticmethod
    def _dot(doc, path):
        node = doc
        for part in str(path).split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def _matches(self, doc, flt):
        for key, cond in flt.items():
            value = self._dot(doc, key)
            if isinstance(cond, dict):
                if "$gte" in cond and (value is None or not value >= cond["$gte"]):
                    return False
                if "$lte" in cond and (value is None or not value <= cond["$lte"]):
                    return False
                if "$in" in cond and value not in cond["$in"]:
                    return False
            elif value != cond:
                return False
        return True

    def find(self, flt, projection=None):
        docs = [d for d in self.docs if self._matches(d, flt)]
        if projection is not None and isinstance(projection, dict):
            # Only keep keys listed with value 1 (or just present in a set)
            include = {k for k, v in projection.items() if v == 1}
            if include:
                docs = [{k: d[k] for k in include if k in d} for d in docs]
        return _FakeCursor(docs)

    def _group_key(self, d, key_field):
        if isinstance(key_field, dict):
            dts = key_field.get("$dateToString")
            if dts:
                return self._format_date(
                    self._dot(d, (dts.get("date") or "")[1:]), dts["format"]
                )
            return str(key_field)
        if isinstance(key_field, str) and key_field.startswith("$"):
            return self._dot(d, key_field[1:])
        return key_field

    @staticmethod
    def _format_date(dt, fmt):
        if not isinstance(dt, datetime):
            return None
        return (
            fmt.replace("%Y", f"{dt:%Y}")
            .replace("%m", f"{dt:%m}")
            .replace("%d", f"{dt:%d}")
            .replace("%H", f"{dt:%H}")
            .replace("%M", f"{dt:%M}")
        )

    def aggregate(self, pipeline):
        docs = self.docs
        for stage in pipeline:
            if "$match" in stage:
                docs = [d for d in docs if self._matches(d, stage["$match"])]
            elif "$count" in stage:
                docs = [{stage["$count"]: len(docs)}]
            elif "$group" in stage:
                grouped = {}
                for d in docs:
                    key = self._group_key(d, stage["$group"]["_id"])
                    acc = grouped.setdefault(key, {})
                    for out_field, expr in stage["$group"].items():
                        if out_field == "_id":
                            continue
                        acc[out_field] = acc.get(out_field, 0) + 1
                docs = [{"_id": k, **v} for k, v in grouped.items()]
        return _FakeCursor(docs)


def _analyze(monkeypatch, docs, tasks=None, user_id="u1", period="week"):
    # Pin ``services.analytics.datetime.now`` to the fixture NOW so the
    # deterministic [from, to] windows stay correct regardless of the real
    # system clock (the seeded docs are relative to the hardcoded NOW too).
    # Tests that already froze a different instant keep their own clock.
    if analytics_module.datetime is not _FrozenDatetime:
        _freeze(monkeypatch, NOW)
    fake = _FakeAnalyticsMessages(docs)
    monkeypatch.setattr(
        "services.analytics.messages_collection", _FakeAnalyticsMessages(docs)
    )
    monkeypatch.setattr(
        "services.analytics.tasks_collection", _FakeAnalyticsMessages(tasks or [])
    )
    return asyncio.run(build_analytics_response(user_id, period))


def _task(**overrides):
    doc = {
        "_id": ObjectId(),
        "user_id": "u1",
        "description": "Do the thing",
        "status": "pending",
        "source_message_id": str(ObjectId()),
        "created_at": NOW,
    }
    doc.update(overrides)
    return doc


def test_total_counts_only_listed_messages_in_window(monkeypatch):
    days_ago = timedelta(days=1)
    docs = [
        _doc(received_at=NOW),
        _doc(received_at=NOW - timedelta(hours=2), source="gmail"),
    ]
    result = _analyze(monkeypatch, docs)
    assert result["total"] == 2


def test_total_excludes_other_users_and_out_of_window(monkeypatch):
    too_old = NOW - timedelta(days=8)
    docs = [
        _doc(received_at=too_old),                 # outside week window
        _doc(user_id="u2"),                        # other user, in window
        _doc(received_at=too_old, user_id="u2"),   # both wrong
        _doc(),                                    # in window, u1
    ]
    result = _analyze(monkeypatch, docs)
    assert result["total"] == 1


def test_priority_buckets_map_known_and_pending(monkeypatch):
    docs = [
        _doc(ai_analysis={"priority": "urgent"}),
        _doc(ai_analysis={"priority": "important"}),
        _doc(ai_analysis={"priority": "normal"}),
        _doc(ai_analysis={"priority": "low"}),
        _doc(ai_analysis={"priority": "random_surprise"}),   # unknown -> pending
        _doc(ai_analysis={"priority": "pending"}),           # pending -> pending
        _doc(),                                              # no analysis -> pending
        _doc(user_id="u2", ai_analysis={"priority": "urgent"}),
    ]
    result = _analyze(monkeypatch, docs)
    assert result["by_priority"] == {
        "urgent": 1,
        "important": 1,
        "normal": 1,
        "low": 1,
        "pending": 3,
    }


def test_by_source_counts_per_listed_source(monkeypatch):
    docs = [
        _doc(source="whatsapp"),
        _doc(source="whatsapp"),
        _doc(source="gmail"),
        _doc(source="sms"),
        _doc(user_id="u2", source="gmail"),
    ]
    result = _analyze(monkeypatch, docs)
    assert result["by_source"] == {"whatsapp": 2, "gmail": 1, "sms": 1}


def test_period_windows_scope_counts(monkeypatch):
    docs = [
        _doc(received_at=NOW - timedelta(hours=1)),          # today
        _doc(received_at=NOW - timedelta(days=3)),           # this week
        _doc(received_at=NOW - timedelta(days=20)),          # this month
        _doc(received_at=NOW - timedelta(days=45)),          # never
    ]
    day = _analyze(monkeypatch, docs, period="day")
    assert day["total"] == 1
    week = _analyze(monkeypatch, docs, period="week")
    assert week["total"] == 2
    month = _analyze(monkeypatch, docs, period="month")
    assert month["total"] == 3


# --- T014: API-level period windows, validation, and user isolation ---


def _register(client, email):
    resp = client.post(
        "/auth/register",
        json={"name": "Ana", "email": email, "password": "secret123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _seed_period_messages(sync_db, user_id, offsets):
    now = datetime.now(timezone.utc)
    for i, delta_days in enumerate(offsets):
        sync_db.messages.insert_one({
            "_id": ObjectId(),
            "user_id": user_id,
            "source": "whatsapp",
            "sender": "tester",
            "content": f"period message {i}",
            "state": "active",
            "received_at": now - timedelta(days=delta_days),
        })


def test_period_windows_at_api_level(client, sync_db):
    user_id = _register(client, "period@test.dev")
    _seed_period_messages(sync_db, user_id, offsets=[0, 3, 20, 45])

    assert client.get("/analytics?period=day").json()["total"] == 1
    assert client.get("/analytics?period=week").json()["total"] == 2
    assert client.get("/analytics?period=month").json()["total"] == 3


def test_analytics_defaults_to_week(client, sync_db):
    user_id = _register(client, "default@test.dev")
    _seed_period_messages(sync_db, user_id, offsets=[0, 3, 20, 45])

    resp = client.get("/analytics")
    assert resp.status_code == 200
    assert resp.json()["period"] == "week"
    assert resp.json()["total"] == 2


def test_analytics_invalid_period_400(client):
    _register(client, "bad@test.dev")
    resp = client.get("/analytics?period=year")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid period. Must be day, week, or month."


def test_analytics_requires_auth_401(client):
    resp = client.get("/analytics")
    assert resp.status_code == 401


def test_analytics_isolates_users(client, sync_db):
    _register(client, "b@test.dev")
    user_a = _register(client, "a@test.dev")  # session now belongs to A
    _seed_period_messages(sync_db, user_a, offsets=[0, 1])

    resp = client.get("/analytics?period=week")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert sum(body["by_priority"].values()) == 2
    assert sum(body["by_source"].values()) == 2

    # A fresh user sees only their empty dataset, never user A's numbers.
    client.post("/auth/logout")
    _register(client, "c@test.dev")
    resp_b = client.get("/analytics?period=week")
    assert resp_b.status_code == 200
    assert resp_b.json()["total"] == 0


# --- T019: tasks summary (period-scoped via parent message received_at) ---


def test_tasks_total_and_completed_scoped_by_parent_message(monkeypatch):
    m_now = _doc(received_at=NOW)
    m_3d = _doc(received_at=NOW - timedelta(days=3))
    _doc(user_id="u2", received_at=NOW)  # another user's message: never ours
    tasks = [
        _task(source_message_id=str(m_now["_id"]), status="pending"),
        _task(source_message_id=str(m_3d["_id"]), status="completed"),
        _task(source_message_id=None, created_at=NOW),          # fallback: created_at
        _task(user_id="u2", source_message_id=str(m_now["_id"])),  # other user
    ]
    week = _analyze(monkeypatch, [m_now, m_3d], tasks=tasks, period="week")
    assert week["tasks"] == {"total": 3, "completed": 1}

    day = _analyze(monkeypatch, [m_now, m_3d], tasks=tasks, period="day")
    # In-day: t1 (parent NOW) + t3 (created_at NOW). t2's parent is 3 days old.
    assert day["tasks"] == {"total": 2, "completed": 0}


def test_tasks_empty_when_none_extracted(monkeypatch):
    result = _analyze(monkeypatch, [_doc(received_at=NOW)], tasks=[])
    assert result["tasks"] == {"total": 0, "completed": 0}


# --- T025: trend buckets (hourly for day, daily for week/month, zero-filled) ---


class _FrozenDatetime:
    """Stand-in for ``services.analytics.datetime`` so trend windows are
    deterministic instead of relative to the real clock."""

    frozen = NOW

    @classmethod
    def now(cls, tz=None):
        return cls.frozen


def _freeze(monkeypatch, frozen):
    _FrozenDatetime.frozen = frozen
    monkeypatch.setattr("services.analytics.datetime", _FrozenDatetime)


def test_trends_daily_buckets_zero_filled(monkeypatch):
    frozen = datetime(2026, 9, 11, 13, 45, 0, tzinfo=timezone.utc)
    _freeze(monkeypatch, frozen)
    docs = [
        _doc(received_at=datetime(2026, 9, 11, 10, 0, 0, tzinfo=timezone.utc)),
        _doc(received_at=datetime(2026, 9, 9, 8, 0, 0, tzinfo=timezone.utc)),
        _doc(received_at=datetime(2026, 9, 5, 1, 0, 0, tzinfo=timezone.utc)),
    ]
    result = _analyze(monkeypatch, docs, period="week")
    trends = result["trends"]
    assert [t["date"] for t in trends] == [
        "2026-09-04",
        "2026-09-05",
        "2026-09-06",
        "2026-09-07",
        "2026-09-08",
        "2026-09-09",
        "2026-09-10",
        "2026-09-11",
    ]
    counts = {t["date"]: t["count"] for t in trends}
    assert counts["2026-09-05"] == 1
    assert counts["2026-09-09"] == 1
    assert counts["2026-09-11"] == 1
    assert counts["2026-09-06"] == 0  # zero-filled day, never skipped


def test_trends_hourly_buckets_zero_filled_for_day(monkeypatch):
    frozen = datetime(2026, 9, 11, 13, 45, 0, tzinfo=timezone.utc)
    _freeze(monkeypatch, frozen)
    docs = [
        _doc(received_at=datetime(2026, 9, 11, 10, 15, 0, tzinfo=timezone.utc)),
        _doc(received_at=datetime(2026, 9, 10, 20, 0, 0, tzinfo=timezone.utc)),
    ]
    result = _analyze(monkeypatch, docs, period="day")
    trends = result["trends"]
    assert len(trends) == 25  # 2026-09-10T13:00Z .. 2026-09-11T13:00Z inclusive
    assert trends[0]["date"] == "2026-09-10T13:00:00Z"
    assert trends[-1]["date"] == "2026-09-11T13:00:00Z"
    counts = {t["date"]: t["count"] for t in trends}
    assert counts["2026-09-11T10:00:00Z"] == 1
    assert counts["2026-09-10T20:00:00Z"] == 1
    assert counts["2026-09-10T15:00:00Z"] == 0  # zero-filled hour


def test_trends_month_uses_daily_buckets(monkeypatch):
    frozen = datetime(2026, 9, 11, 13, 45, 0, tzinfo=timezone.utc)
    _freeze(monkeypatch, frozen)
    docs = [
        _doc(received_at=datetime(2026, 9, 11, 9, 0, 0, tzinfo=timezone.utc)),
        _doc(received_at=datetime(2026, 8, 20, 9, 0, 0, tzinfo=timezone.utc)),
    ]
    result = _analyze(monkeypatch, docs, period="month")
    trends = result["trends"]
    assert all(len(t["date"]) == 10 for t in trends)  # YYYY-MM-DD only
    counts = {t["date"]: t["count"] for t in trends}
    assert counts["2026-09-11"] == 1
    assert counts["2026-08-20"] == 1
    assert counts["2026-08-30"] == 0
    assert len(trends) >= 30