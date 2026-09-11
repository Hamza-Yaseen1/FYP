"""Deterministic message-thread linking (Day 25).

``resolve_and_stamp`` implements the ONLY rule that groups messages: same
``user_id``, same ``source``, same normalized sender, arriving within
``LINK_WINDOW_MINUTES`` of the thread's latest message. It is pure
determinism + one indexed read — no AI grouping, no vector store, no memory
framework (spec FR-015 / SC-008).
"""

import logging
import os
import re
from datetime import datetime, timedelta

from database import messages_collection

logger = logging.getLogger(__name__)

LINK_WINDOW_MINUTES = int(os.getenv("LINK_WINDOW_MINUTES", "60"))


def normalize_sender(sender: str) -> str:
    """Canonical sender form used by the link rule.

    Same granularity as the inbox sender filter: case- and
    whitespace-insensitive. Never approximates names.
    """
    return str(sender).strip().lower()


def _sender_filter(normalized: str) -> dict:
    """Match stored (as-authored) sender values against the normalized form.

    Message documents keep the sender string exactly as delivered, so the
    link query compares case-insensitively but still exactly — a pure
    function of the rule's inputs, never a fuzzy match.
    """
    return {"$regex": f"^{re.escape(normalized)}$", "$options": "i"}


async def resolve_and_stamp(
    user_id: str,
    source: str,
    sender: str,
    received_at: datetime,
) -> tuple[str | None, str | None]:
    """Resolve the thread identity for one incoming message at ingest time.

    Returns ``(thread_id, conversation_id)``:
    - ``(None, None)`` when no in-window message from the same
      user/source/sender exists — the message stands alone.
    - a thread's ids when the latest in-window message already carries a
      ``threadId`` (inherited).
    - otherwise the candidate becomes the **anchor**: ``threadId`` is born as
      ``str(candidate._id)``, the anchor is stamped with it, and the pair is
      returned.

    Every query is ``user_id``-scoped and only ``state: "active"`` messages
    are link candidates. The anchor stamp uses a guarded update against
    ``{"_id", "user_id"}`` so a concurrent/duplicate delivery cannot
    double-stamp or touch another user's document.
    """
    window_start = received_at - timedelta(minutes=LINK_WINDOW_MINUTES)
    candidate = await messages_collection.find_one(
        {
            "user_id": user_id,
            "source": source,
            "sender": _sender_filter(normalize_sender(sender)),
            "state": "active",
            "received_at": {"$gte": window_start},
        },
        sort=[("received_at", -1)],
    )
    if candidate is None:
        return None, None

    inherited = candidate.get("threadId")
    if inherited:
        thread_id = str(inherited)
        return thread_id, thread_id

    thread_id = str(candidate["_id"])
    await messages_collection.find_one_and_update(
        {"_id": candidate["_id"], "user_id": user_id},
        {"$set": {"threadId": thread_id, "conversationId": thread_id}},
        return_document=True,
    )
    logger.info(
        "Anchor stamped: thread=%s (sender=%s source=%s)",
        thread_id,
        sender,
        source,
    )
    return thread_id, thread_id