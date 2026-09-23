import logging
from datetime import datetime, timezone
from typing import Optional

import asyncio

from bson import ObjectId
from fastapi import BackgroundTasks
from pymongo.errors import DuplicateKeyError

from database import messages_collection
from services.ai import process_message
from services.threads import resolve_and_stamp

logger = logging.getLogger(__name__)

# Keep references to background analyze tasks spawned outside a request
# context so the event loop does not garbage-collect them mid-flight.
_pending_tasks: set = set()


def build_analysis_text(content: str, subject: Optional[str] = None) -> str:
    """Combine an optional subject line with the body for AI analysis.

    Gmail stores ``subject`` separately from ``content``; the AI must see
    both or the model can miss urgency expressed only in the subject
    (e.g. "Action Required: Submit report by tomorrow"). WhatsApp messages
    have no subject, so the text stays byte-identical to the body.
    """
    if subject and subject.strip():
        return f"Subject: {subject.strip()}\n\n{content}"
    return content


async def _analyze_and_store(
    content: str,
    message_id: str,
    user_id: str,
    thread_id: str = None,
    subject: Optional[str] = None,
) -> None:
    """Run the AI pipeline for an ingested message and persist its result.

    Runs as a background task after the webhook acknowledgement so delivery
    stays fast, mirroring how POST /messages persists ``ai_analysis``.
    ``process_message`` never raises (it degrades to a rule-based stub or
    fallback values), but we guard persistence independently so a DB hiccup
    cannot crash the task.
    """
    try:
        analysis = await process_message(
            build_analysis_text(content, subject),
            message_id=message_id,
            user_id=user_id,
            thread_id=thread_id,
        )
    except Exception as exc:
        logger.warning("AI analyze task failed for %s: %s", message_id, exc)
        return

    try:
        await messages_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"ai_analysis": analysis}},
        )
    except Exception as exc:
        logger.warning("Failed to persist ai_analysis for %s: %s", message_id, exc)


async def ingest_message(
    user_id: str,
    source: str,
    sender: str,
    content: str,
    external_message_id: Optional[str] = None,
    message_type: str = "text",
    background_tasks: Optional[BackgroundTasks] = None,
    subject: Optional[str] = None,
) -> str:
    """Normalize, persist, and analyze one inbound message.

    All ingestion paths (real WhatsApp webhook, simulate endpoint, Gmail
    poller) funnel through here so the AI pipeline, storage, and Dashboard
    never read provider-specific payloads.

    ``subject`` is additive and Gmail-specific; it is stored only when
    provided. When ``background_tasks`` is None (i.e. the call comes from a
    background task such as the Gmail poller rather than a request handler),
    analysis is spawned with :func:`asyncio.create_task` and tracked in a
    module-level set so it is not garbage-collected.

    Returns the stored message id. On a duplicate delivery (same
    ``external_message_id``) the existing id is returned and the AI pipeline
    is NOT re-run.
    """
    now = datetime.now(timezone.utc)
    _id = ObjectId()
    thread_id, conversation_id = None, None
    try:
        thread_id, conversation_id = await resolve_and_stamp(
            user_id, source, sender, now
        )
    except Exception as exc:
        logger.warning(
            "Thread resolution failed for %s; message stored standalone: %s",
            source,
            exc,
            exc_info=True,
        )

    doc = {
        "_id": _id,
        "messageId": str(_id),
        "user_id": user_id,
        "source": source,
        "sender": sender,
        "content": content,
        "message_type": message_type,
        "status": "unread",
        "state": "active",
        "created_at": now,
        "updated_at": now,
        "received_at": now,
    }
    if thread_id:
        doc["threadId"] = thread_id
        doc["conversationId"] = conversation_id
    if external_message_id:
        doc["external_message_id"] = external_message_id
    if subject is not None:
        doc["subject"] = subject

    try:
        result = await messages_collection.insert_one(doc)
        message_id = str(result.inserted_id)
    except DuplicateKeyError:
        existing = await messages_collection.find_one(
            {"user_id": user_id, "external_message_id": external_message_id}
        )
        if existing is None:
            raise
        logger.info(
            "Duplicate delivery ignored (external_message_id=%s)",
            external_message_id,
        )
        return str(existing["_id"])

    if background_tasks is not None:
        background_tasks.add_task(
            _analyze_and_store, content, message_id, user_id, thread_id, subject
        )
    else:
        task = asyncio.create_task(
            _analyze_and_store(content, message_id, user_id, thread_id, subject)
        )
        _pending_tasks.add(task)
        task.add_done_callback(_pending_tasks.discard)

    return message_id