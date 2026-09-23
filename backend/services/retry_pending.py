"""Background retry for pending AI analyses (Day 29).

AI outages degrade ``process_message`` to a stored ``ai_analysis.status ==
"pending"`` stub so delivery never blocks on the provider. Nothing re-runs
those messages, so this module adds the missing sweep: ``retry_pending_analyses``
re-enters the SAME single AI entry point (``process_message`` — never
``analyze_message``) for each pending message and updates that document
in place via ``{_id, user_id}``.

Rules (contract ``contracts/security-testing.md`` §4):

- Selector ``{"ai_analysis.status": "pending"}``; every ``update_one`` is
  user-scoped.
- Idempotent: retrying never creates a document; document count is invariant.
- Guarded: a failing retry logs and leaves the message ``pending`` — it never
  raises into the sweep loop or a request path.

Throttling: retries run sequentially with a short pause between LLM calls so a
full drain can never trip the Groq OTPM cap (the usual reason a whole batch
stays stuck in ``pending``). When several consecutive attempts still return
``pending`` (typically a rate limit or provider outage), the cycle stops early
and leaves the rest for the next cycle so quota is preserved. Results are always
reported via a summary dict; ``RETRY_SLEEP_SECONDS`` and
``RETRY_MAX_CONSECUTIVE_FAILURES`` are env-tunable.
"""

import asyncio
import logging
import os

from bson import ObjectId

from database import messages_collection
from services.ai import process_message
from services.webhook_ingest import build_analysis_text

logger = logging.getLogger(__name__)

# Sequential pacing so a burst of retries cannot burn the whole OTPM quota.
RETRY_SLEEP_SECONDS = float(os.getenv("RETRY_SLEEP_SECONDS", "0.8"))
# A run of this many consecutive unresolved attempts is treated as a rate
# limit / provider outage: stop early and let the next cycle take over.
RETRY_MAX_CONSECUTIVE_FAILURES = int(
    os.getenv("RETRY_MAX_CONSECUTIVE_FAILURES", "3")
)


async def _reanalyze_pending(
    filter_query: dict,
    limit: int | None = None,
    sleep_seconds: float = RETRY_SLEEP_SECONDS,
    max_consecutive_failures: int = RETRY_MAX_CONSECUTIVE_FAILURES,
) -> dict:
    """Re-run the AI pipeline for every document matching ``filter_query``.

    Returns a summary dict and never raises:
    {scanned, completed, failed, remaining_pending, rate_limited, limit}
    """
    flt = dict(filter_query)
    query = messages_collection.find(flt)
    if limit is not None:
        query = query.limit(limit)
    pending = []
    async for doc in query:
        pending.append(doc)

    if not pending:
        return {
            "scanned": 0,
            "completed": 0,
            "failed": 0,
            "remaining_pending": await messages_collection.count_documents(flt),
            "rate_limited": False,
            "limit": limit,
        }

    completed = 0
    failed = 0
    scanned = 0
    consecutive_failures = 0
    rate_limited = False

    for doc in pending:
        scanned += 1
        if scanned > 1:
            await asyncio.sleep(sleep_seconds)

        message_id = str(doc["_id"])
        user_id = doc.get("user_id")
        if not user_id:
            logger.warning("Pending message %s has no user_id; skipping", message_id)
            failed += 1
            continue

        try:
            analysis = await process_message(
                build_analysis_text(doc.get("content", ""), doc.get("subject")),
                message_id=message_id,
                user_id=user_id,
                thread_id=doc.get("threadId"),
            )
        except Exception as exc:
            logger.warning(
                "Retry failed for message %s (stays pending): %s",
                message_id,
                exc,
                exc_info=True,
            )
            analysis = {"status": "pending"}

        if analysis.get("status") == "completed":
            await messages_collection.update_one(
                {"_id": ObjectId(message_id), "user_id": user_id},
                {"$set": {"ai_analysis": analysis}},
            )
            completed += 1
            consecutive_failures = 0
            logger.info("Pending analysis completed for message %s", message_id)
        else:
            logger.warning(
                "Pending message %s still unresolved after retry; leaving pending",
                message_id,
            )
            failed += 1
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                rate_limited = True
                logger.warning(
                    "%d consecutive unresolved retries — pausing sweep to preserve quota",
                    consecutive_failures,
                )
                break

    remaining_pending = await messages_collection.count_documents(flt)
    return {
        "scanned": scanned,
        "completed": completed,
        "failed": failed,
        "remaining_pending": remaining_pending,
        "rate_limited": rate_limited,
        "limit": limit,
    }


async def retry_pending_analyses(limit: int = 10) -> dict:
    """Sweep every pending message (used by the lifespan background loop).

    Bounded per cycle so a full drain cannot trip the provider quota; the
    next 60s cycle continues where this one stopped.
    """
    return await _reanalyze_pending(
        {"ai_analysis.status": "pending"},
        limit=limit,
    )


async def reanalyze_user_pending(
    user_id: str,
    limit: int | None = None,
    sleep_seconds: float = RETRY_SLEEP_SECONDS,
) -> dict:
    """Bulk re-analyze all of ONE user's pending messages (POST endpoint)."""
    return await _reanalyze_pending(
        {"user_id": user_id, "ai_analysis.status": "pending"},
        limit=limit,
        sleep_seconds=sleep_seconds,
    )