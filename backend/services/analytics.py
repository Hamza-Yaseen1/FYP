"""Read-only analytics aggregations (Day 28).

Every pipeline starts with a ``user_id`` ``$match`` — the session-scoped
owner is always the FIRST filter, and no cross-user aggregation is ever
performed (constitution Day 28 hard rules).

Response is computed on demand per request from live data; nothing is stored
or cached beyond request lifetime.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from database import messages_collection, tasks_collection

logger = logging.getLogger(__name__)

VALID_PERIODS = ("day", "week", "month")
PERIOD_DAYS = {"day": 1, "week": 7, "month": 30}

PRIORITY_BUCKETS = ("urgent", "important", "normal", "low", "pending")


def _period_range(period: str) -> tuple[datetime, datetime]:
    """Resolve a period string to an inclusive UTC ``[from, to]`` window."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=PERIOD_DAYS[period])
    return start, now


async def build_analytics_response(user_id: str, period: str) -> dict:
    """Assemble the full analytics snapshot for one user and period.

    The five aggregations are independent user-scoped reads, so they run
    concurrently (asyncio.gather) instead of serially waiting on the same
    MongoDB connection.
    """
    from_dt, to_dt = _period_range(period)
    total, by_priority, by_source, tasks, trends = await asyncio.gather(
        _message_total(user_id, from_dt, to_dt),
        _message_priority_buckets(user_id, from_dt, to_dt),
        _message_source_counts(user_id, from_dt, to_dt),
        _tasks_summary(user_id, from_dt, to_dt),
        _message_trends(user_id, from_dt, to_dt, period),
    )
    return {
        "period": period,
        "from": from_dt,
        "to": to_dt,
        "total": total,
        "by_priority": by_priority,
        "by_source": by_source,
        "tasks": tasks,
        "trends": trends,
    }


def _base_match(user_id: str, from_dt: datetime, to_dt: datetime) -> dict:
    """Owner-first match shared by every pipeline (Day 28 isolation rule)."""
    return {"user_id": user_id, "received_at": {"$gte": from_dt, "$lte": to_dt}}


async def _message_total(
    user_id: str, from_dt: datetime, to_dt: datetime
) -> int:
    pipeline = [
        {"$match": _base_match(user_id, from_dt, to_dt)},
        {"$count": "total"},
    ]
    docs = await messages_collection.aggregate(pipeline).to_list(length=1)
    return docs[0]["total"] if docs else 0


async def _message_priority_buckets(
    user_id: str, from_dt: datetime, to_dt: datetime
) -> dict[str, int]:
    pipeline = [
        {"$match": _base_match(user_id, from_dt, to_dt)},
        {"$group": {"_id": "$ai_analysis.priority", "count": {"$sum": 1}}},
    ]
    docs = await messages_collection.aggregate(pipeline).to_list(length=100)
    buckets = dict.fromkeys(PRIORITY_BUCKETS, 0)
    for doc in docs:
        key = doc["_id"]
        bucket = key if key in ("urgent", "important", "normal", "low") else "pending"
        buckets[bucket] += doc["count"]
    return buckets


async def _message_source_counts(
    user_id: str, from_dt: datetime, to_dt: datetime
) -> dict[str, int]:
    pipeline = [
        {"$match": _base_match(user_id, from_dt, to_dt)},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    docs = await messages_collection.aggregate(pipeline).to_list(length=100)
    return {doc["_id"]: doc["count"] for doc in docs if doc["_id"]}


async def _tasks_summary(
    user_id: str, from_dt: datetime, to_dt: datetime
) -> dict[str, int]:
    """Count extracted vs completed tasks in the period.

    A task is scoped to the period via its parent message's ``received_at``
    (resolved from ``source_message_id``, always stayed within the same
    user's documents). If the parent message is missing, the task falls back
    to its own ``created_at``.

    Previously all tasks for a user were loaded into Python and filtered.
    Now the Mongo query pre-filters to the period window via ``created_at``
    (a safe upper/lower bound on any task that could count), and only the
    lightweight fields needed for in-Python scoping are transferred.
    """
    task_docs = await tasks_collection.find(
        {"user_id": user_id, "created_at": {"$gte": from_dt, "$lte": to_dt}},
        {"_id": 0, "source_message_id": 1, "created_at": 1, "status": 1, "user_id": 1},
    ).to_list(length=10_000)
    if not task_docs:
        return {"total": 0, "completed": 0}

    message_ids = [
        ObjectId(t["source_message_id"])
        for t in task_docs
        if t.get("source_message_id") and ObjectId.is_valid(t["source_message_id"])
    ]
    received_by_id: dict[str, datetime] = {}
    if message_ids:
        cursor = messages_collection.find(
            {"_id": {"$in": message_ids}, "user_id": user_id}
        )
        parent_docs = await cursor.to_list(length=len(message_ids))
        received_by_id = {
            str(doc["_id"]): doc.get("received_at") for doc in parent_docs
        }

    total = 0
    completed = 0
    for task in task_docs:
        reference = received_by_id.get(str(task.get("source_message_id")))
        if reference is None:
            reference = task.get("created_at")
        if reference is not None and from_dt <= reference <= to_dt:
            total += 1
            if task.get("status") == "completed":
                completed += 1
    return {"total": total, "completed": completed}


async def _message_trends(
    user_id: str, from_dt: datetime, to_dt: datetime, period: str
) -> list[dict]:
    """Time-bucket message counts, zero-filled across the full window.

    Hourly buckets for ``day``; daily (UTC) buckets for ``week``/``month``.
    Bucket boundaries are floored so no message at either edge of the window
    is dropped; gaps between buckets are filled with zero counts in Python.
    """
    if period == "day":
        bucket = {
            "$dateToString": {
                "format": "%Y-%m-%dT%H:00:00Z",
                "date": "$received_at",
                "timezone": "UTC",
            }
        }
    else:
        bucket = {
            "$dateToString": {
                "format": "%Y-%m-%d",
                "date": "$received_at",
                "timezone": "UTC",
            }
        }
    pipeline = [
        {"$match": _base_match(user_id, from_dt, to_dt)},
        {"$group": {"_id": bucket, "count": {"$sum": 1}}},
    ]
    docs = await messages_collection.aggregate(pipeline).to_list(length=10_000)
    counts = {doc["_id"]: doc["count"] for doc in docs if doc["_id"]}
    return _zero_filled_trends(counts, from_dt, to_dt, period)


def _zero_filled_trends(
    counts: dict[str, int], from_dt: datetime, to_dt: datetime, period: str
) -> list[dict]:
    trends: list[dict] = []
    if period == "day":
        start = from_dt.replace(minute=0, second=0, microsecond=0)
        end = to_dt.replace(minute=0, second=0, microsecond=0)
        while start <= end:
            key = f"{start:%Y-%m-%dT%H:00:00Z}"
            trends.append({"date": key, "count": counts.get(key, 0)})
            start += timedelta(hours=1)
    else:
        start = from_dt.date()
        end = to_dt.date()
        while start <= end:
            key = start.isoformat()
            trends.append({"date": key, "count": counts.get(key, 0)})
            start += timedelta(days=1)
    return trends