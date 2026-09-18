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
"""

import logging

from bson import ObjectId

from database import messages_collection
from services.ai import process_message

logger = logging.getLogger(__name__)


async def retry_pending_analyses(limit: int = 50) -> int:
    """Re-run the AI pipeline for stored messages whose analysis is pending.

    Returns the number of messages retried. Never creates a document —
    the ``update_one`` targets the existing ``{_id, user_id}`` document.
    """
    cursor = messages_collection.find({"ai_analysis.status": "pending"}).limit(limit)
    pending = []
    async for doc in cursor:
        pending.append(doc)
    if not pending:
        return 0

    retried = 0
    for doc in pending:
        message_id = str(doc["_id"])
        user_id = doc.get("user_id")
        if not user_id:
            logger.warning("Pending message %s has no user_id; skipping", message_id)
            continue
        try:
            analysis = await process_message(
                doc.get("content", ""),
                message_id=message_id,
                user_id=user_id,
                thread_id=doc.get("threadId"),
            )
            await messages_collection.update_one(
                {"_id": ObjectId(message_id), "user_id": user_id},
                {"$set": {"ai_analysis": analysis}},
            )
            retried += 1
        except Exception as exc:
            logger.warning(
                "Retry failed for message %s (stays pending): %s",
                message_id,
                exc,
                exc_info=True,
            )
    return retried