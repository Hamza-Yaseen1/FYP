import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import BackgroundTasks
from pymongo.errors import DuplicateKeyError

from database import messages_collection
from services.ai import analyze_message

logger = logging.getLogger(__name__)


async def _analyze_and_store(content: str, message_id: str, user_id: str) -> None:
    """Run the AI pipeline for an ingested message and persist its result.

    Runs as a background task after the webhook acknowledgement so delivery
    stays fast, mirroring how POST /messages persists ``ai_analysis``.
    ``analyze_message`` never raises (it degrades to fallback values), but we
    guard persistence independently so a DB hiccup cannot crash the task.
    """
    try:
        analysis = await analyze_message(
            content, message_id=message_id, user_id=user_id
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
) -> str:
    """Normalize, persist, and analyze one inbound message.

    All ingestion paths (real WhatsApp webhook, simulate endpoint) funnel
    through here so the AI pipeline, storage, and Dashboard never read
    provider-specific payloads.

    Returns the stored message id. On a duplicate delivery (same
    ``external_message_id``) the existing id is returned and the AI pipeline
    is NOT re-run.
    """
    now = datetime.now(timezone.utc)
    doc = {
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
    if external_message_id:
        doc["external_message_id"] = external_message_id

    try:
        result = await messages_collection.insert_one(doc)
        message_id = str(result.inserted_id)
    except DuplicateKeyError:
        existing = await messages_collection.find_one(
            {"external_message_id": external_message_id}
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
            _analyze_and_store, content, message_id, user_id
        )

    return message_id